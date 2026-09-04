#!/usr/bin/env python3
"""Send files through the official BridgeZX client with target/IP safeguards."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Any, Callable, Sequence


EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_UNCERTAIN = 4
EXIT_INTERRUPTED = 130


class UsageError(ValueError):
    """The local invocation cannot safely start a transfer."""


@dataclass(frozen=True)
class BridgeZXAPI:
    default_port: int
    ready_status: Any
    load_config: Callable[[], dict[str, Any]]
    remember_ip: Callable[[str], None]
    probe: Callable[..., Any]
    send_queue: Callable[..., Any]
    build_remote_path_map: Callable[..., Any]
    progress: Callable[[str], None]
    finish_progress: Callable[[], None]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send files to ZX Spectrum through the official BridgeZX engine."
    )
    parser.add_argument("sources", nargs="+", help="Local files/directories to send")
    parser.add_argument("--client-root", help="BridgeZX repo root or client directory")
    parser.add_argument("--ip", help="Spectrum IP (default: BridgeZX last used)")
    parser.add_argument("--port", type=int, help="BridgeZX TCP port")
    parser.add_argument("--target", choices=("classic", "next"))
    parser.add_argument("--destination", metavar="REMOTE_PATH")
    parser.add_argument(
        "--ordered",
        action="store_true",
        help="Send each source as a separate operation in argument order",
    )
    parser.add_argument("--quiet", action="store_true")
    return parser


def _add_client_root(value: str) -> None:
    root = Path(value).expanduser().resolve()
    for candidate in (root, root / "client"):
        if (candidate / "bridgezx" / "__init__.py").is_file():
            sys.path.insert(0, str(candidate))
            return
    raise UsageError(
        f"BridgeZX client not found under {root}; expected bridgezx/__init__.py "
        "or client/bridgezx/__init__.py"
    )


def _load_bridgezx(client_root: str | None) -> BridgeZXAPI:
    selected_root = client_root or os.environ.get("BRIDGEZX_CLIENT_ROOT")
    if selected_root:
        _add_client_root(selected_root)
    try:
        from bridgezx import constants
        from bridgezx.config import load_config, remember_ip
        from bridgezx.transfer import (
            ProbeStatus,
            build_remote_path_map,
            default_progress_printer,
            finish_progress_line,
            probe,
            send_queue,
        )
    except ImportError as exc:
        missing = getattr(exc, "name", None)
        detail = f" (missing {missing})" if missing else ""
        raise UsageError(
            "BridgeZX Python client is unavailable, incomplete, or incompatible"
            f"{detail}; provide a current client through --client-root or "
            "BRIDGEZX_CLIENT_ROOT"
        ) from exc
    return BridgeZXAPI(
        default_port=constants.LAIN_PORT,
        ready_status=ProbeStatus.READY,
        load_config=load_config,
        remember_ip=remember_ip,
        probe=probe,
        send_queue=send_queue,
        build_remote_path_map=build_remote_path_map,
        progress=default_progress_printer,
        finish_progress=finish_progress_line,
    )


def _selected_ip(explicit: str | None, api: BridgeZXAPI) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    config = api.load_config()
    last = str(config.get("last_ip") or "").strip()
    if last:
        return last
    history = config.get("ip_history") or []
    if history:
        candidate = str(history[0]).strip()
        if candidate:
            return candidate
    raise UsageError("No BridgeZX IP given and no IP exists in BridgeZX history")


def _resolve_sources(values: Sequence[str], api: BridgeZXAPI) -> list[str]:
    sources: list[str] = []
    for value in values:
        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise UsageError(f"Source not found: {path}")
        if not (path.is_file() or path.is_dir()):
            raise UsageError(f"Source is not a file or directory: {path}")
        sources.append(str(path))

    # The BridgeZX planner owns recursive filtering, limits, naming, and
    # collision checks. Validate every source before any ordered transfer starts.
    try:
        api.build_remote_path_map(sources)
    except (OSError, ValueError) as exc:
        raise UsageError(str(exc)) from exc
    return sources


def _send_operation(
    api: BridgeZXAPI,
    ip: str,
    port: int,
    sources: Sequence[str],
    *,
    destination: str | None,
    detected_target: str,
    quiet: bool,
) -> tuple[int, str]:
    try:
        result = api.send_queue(
            ip,
            list(sources),
            port=port,
            progress=None if quiet else api.progress,
            destination=destination,
            target=detected_target,
            expected_target=detected_target,
        )
    except KeyboardInterrupt as exc:
        if not quiet:
            api.finish_progress()
        message = str(exc).strip()
        if message:
            return EXIT_INTERRUPTED, f"uncertain: {message}"
        return EXIT_INTERRUPTED, "interrupted: transfer cancelled"
    if not quiet:
        api.finish_progress()
    if result.ok:
        return 0, str(result.message)
    if result.outcome_unknown:
        return EXIT_UNCERTAIN, f"uncertain: {result.message}"
    return EXIT_ERROR, f"error: {result.message}"


def run(args: argparse.Namespace, api: BridgeZXAPI) -> int:
    try:
        ip = _selected_ip(args.ip, api)
        sources = _resolve_sources(args.sources, api)
    except KeyboardInterrupt:
        print("interrupted: transfer preparation cancelled", file=sys.stderr)
        return EXIT_INTERRUPTED
    port = args.port if args.port is not None else api.default_port

    try:
        probe_result = api.probe(ip, port=port)
    except KeyboardInterrupt:
        print("interrupted: probe cancelled", file=sys.stderr)
        return EXIT_INTERRUPTED
    if probe_result.status != api.ready_status:
        print(f"error: {probe_result.message} ({ip}:{port})", file=sys.stderr)
        return EXIT_ERROR

    detected = str(probe_result.target or "").strip()
    if detected not in {"classic", "next"}:
        print("error: BridgeZX probe did not identify Classic or Next", file=sys.stderr)
        return EXIT_ERROR
    if args.target and args.target != detected:
        print(
            f"error: requested {args.target}, but BridgeZX detected {detected} "
            f"at {ip}:{port}",
            file=sys.stderr,
        )
        return EXIT_ERROR

    api.remember_ip(ip)
    version = f" {probe_result.version}" if probe_result.version else ""
    print(f"ready: {ip}:{port} ({detected}{version})")
    print(f"destination: {args.destination or '(server directory)'}")

    operations = [[source] for source in sources] if args.ordered else [sources]
    completed = 0
    for operation in operations:
        code, message = _send_operation(
            api,
            ip,
            port,
            operation,
            destination=args.destination,
            detected_target=detected,
            quiet=args.quiet,
        )
        print(message, file=sys.stdout if code == 0 else sys.stderr)
        if code:
            if args.ordered:
                print(f"failed source: {operation[0]}", file=sys.stderr)
                print(
                    f"ordered sequence stopped after {completed} of {len(operations)} operations",
                    file=sys.stderr,
                )
            return code
        completed += 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        api = _load_bridgezx(args.client_root)
        return run(args, api)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
