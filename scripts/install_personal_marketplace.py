#!/usr/bin/env python3
"""Install this plugin into the Codex personal marketplace."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


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


def write_marketplace(path: Path, data: dict) -> None:
    temporary_path = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            handle.write(json.dumps(data, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary_path = Path(handle.name)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


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

    write_marketplace(marketplace_path, data)
    print(f"Updated {marketplace_path}")
    print(f"Source: {plugin_root}")
    conflicting_workflows = (
        home / ".agents" / "skills" / "workflow" / "SKILL.md",
        home / ".codex" / "skills" / "workflow" / "SKILL.md",
    )
    for workflow in conflicting_workflows:
        if workflow.exists():
            print(
                f"Warning: {workflow.parent} can conflict with the bundled workflow; "
                "move or disable it after verifying this plugin."
            )
    print(f"Run: codex plugin add {PLUGIN_NAME}@{data['name']}")


if __name__ == "__main__":
    main()
