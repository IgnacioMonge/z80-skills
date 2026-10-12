"""Claude API access for the shrink agent: key loading, tool calls, cost."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# USD per million tokens: (input, output, 5-minute cache write, cache read).
# Source: platform.claude.com/docs/en/about-claude/pricing, checked 2026-10-12.
# Haiku 5.5 uses its <=100k-token prompt tier. Override in the config [prices].
DEFAULT_PRICES: dict[str, tuple[float, float, float, float]] = {
    "claude-fable-5-1": (10.0, 50.0, 12.5, 0.25),
    "claude-opus-5-5": (4.0, 20.0, 5.0, 0.20),
    "claude-sonnet-5-5": (2.0, 10.0, 2.5, 0.10),
    "claude-haiku-5-5": (0.10, 0.50, 0.125, 0.01),
}


class ApiFatal(RuntimeError):
    """An API error that must stop the run (auth, credit, invalid model)."""


def load_env(env_path: Path) -> dict[str, str]:
    """Parse a dotenv-style file. The process environment is never consulted."""
    if not env_path.is_file():
        raise ApiFatal(f"API key file not found: {env_path}")
    values: dict[str, str] = {}
    for raw in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_api_key(env_path: Path) -> str:
    key = load_env(env_path).get("ANTHROPIC_API_KEY", "")
    if not key:
        raise ApiFatal(f"ANTHROPIC_API_KEY missing in {env_path}")
    return key


def usage_cost(model: str, usage: Any, prices: dict[str, tuple[float, float, float, float]]) -> float:
    if model not in prices:
        raise ApiFatal(f"no price for model {model!r}; add it under [prices] in the config")
    p_in, p_out, p_cw, p_cr = prices[model]
    get = lambda name: int(getattr(usage, name, 0) or 0)  # noqa: E731
    return (
        get("input_tokens") * p_in
        + get("output_tokens") * p_out
        + get("cache_creation_input_tokens") * p_cw
        + get("cache_read_input_tokens") * p_cr
    ) / 1_000_000


@dataclass
class ToolCall:
    data: dict
    cost: float
    assistant_content: list = field(default_factory=list)
    tool_use_id: str = ""
    history: list = field(default_factory=list)  # messages actually sent for this reply


class Claude:
    """Thin wrapper: one tool call per request, cached system prompt.

    Models with built-in thinking reject a forced tool_choice, so the tool is
    offered with tool_choice auto; a reply without the tool call gets one nudge.
    """

    def __init__(self, api_key: str, prices: dict[str, tuple[float, float, float, float]], workspace_id: str = ""):
        import anthropic  # imported lazily so dry runs and tests need no SDK

        self._anthropic = anthropic
        headers = {"anthropic-workspace-id": workspace_id} if workspace_id else None
        self.client = anthropic.Anthropic(api_key=api_key, max_retries=4, timeout=600, default_headers=headers)
        self.prices = prices
        self.spent = 0.0
        self.tokens: dict[str, dict[str, int]] = {}  # model -> usage field -> total, to reconcile with the Console

    def call(self, model: str, system: list[str], messages: list[dict], tool: dict, max_tokens: int) -> ToolCall:
        system_blocks = [{"type": "text", "text": s} for s in system]
        system_blocks[-1]["cache_control"] = {"type": "ephemeral"}
        msgs, total = list(messages), 0.0
        for attempt in range(2):
            resp = self._create(model, max_tokens, system_blocks, tool, msgs)
            cost = usage_cost(model, resp.usage, self.prices)
            self.spent += cost
            total += cost
            tally = self.tokens.setdefault(model, {})
            for f in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
                tally[f] = tally.get(f, 0) + int(getattr(resp.usage, f, 0) or 0)
            content = [b.model_dump(exclude_none=True) for b in resp.content]
            for block in resp.content:
                if getattr(block, "type", "") == "tool_use" and block.name == tool["name"]:
                    return ToolCall(dict(block.input), total, content, block.id, msgs)
            if attempt == 0:
                msgs = msgs + [
                    {"role": "assistant", "content": content or [{"type": "text", "text": "(no answer)"}]},
                    {"role": "user", "content": f"Answer only by calling the {tool['name']} tool."},
                ]
        raise RuntimeError(f"model returned no {tool['name']} call (stop_reason={resp.stop_reason})")

    def _create(self, model: str, max_tokens: int, system_blocks: list, tool: dict, messages: list[dict]):
        a = self._anthropic
        try:
            return self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_blocks,
                tools=[tool],
                tool_choice={"type": "auto"},
                messages=messages,
            )
        except (a.AuthenticationError, a.PermissionDeniedError, a.NotFoundError) as exc:
            raise ApiFatal(f"{type(exc).__name__}: {exc}") from exc
        except a.BadRequestError as exc:
            # A 400 repeats on every request (key scope, credit, model, schema): stop the run.
            msg = str(exc)
            if "workspace" in msg.lower():
                msg += (
                    "\nFix: add ANTHROPIC_WORKSPACE_ID=wrkspc_... to the .env file (Console -> Settings ->"
                    " Workspaces), or create a key inside a workspace."
                )
            raise ApiFatal(msg) from exc
