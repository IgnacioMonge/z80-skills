#!/usr/bin/env python3
"""Install this plugin into the Codex personal marketplace."""

from __future__ import annotations

import json
from pathlib import Path


PLUGIN_NAME = "z80-skills"


def marketplace_source_path(plugin_root: Path, home: Path) -> str:
    try:
        relative = plugin_root.resolve().relative_to(home.resolve())
    except ValueError as exc:
        raise ValueError("the repository must be located under the user's home") from exc
    return f"./{relative.as_posix()}"


def marketplace_data(data: dict, source_path: str) -> dict:
    data.setdefault("name", "personal")
    data.setdefault("interface", {}).setdefault("displayName", "Personal")
    plugins = data.setdefault("plugins", [])

    entry = {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": source_path,
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }

    for index, existing in enumerate(plugins):
        if existing.get("name") == PLUGIN_NAME:
            plugins[index] = entry
            break
    else:
        plugins.append(entry)
    return data


def main() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    home = Path.home()
    try:
        source_path = marketplace_source_path(plugin_root, home)
    except ValueError as exc:
        raise SystemExit(f"Cannot install {plugin_root}: {exc}") from exc

    marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
    marketplace_path.parent.mkdir(parents=True, exist_ok=True)

    if marketplace_path.exists():
        data = json.loads(marketplace_path.read_text(encoding="utf-8"))
    else:
        data = {}
    data = marketplace_data(data, source_path)

    marketplace_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {marketplace_path}")
    print(f"Source: {plugin_root}")
    legacy_workflow = home / ".codex" / "skills" / "workflow" / "SKILL.md"
    if legacy_workflow.exists():
        print(
            f"Warning: {legacy_workflow.parent} can shadow the bundled workflow; "
            "move or remove it after verifying this plugin."
        )
    print(f"Run: codex plugin add {PLUGIN_NAME}@{data['name']}")


if __name__ == "__main__":
    main()
