#!/usr/bin/env python3
"""Install this plugin into the Codex personal marketplace."""

from __future__ import annotations

import json
from pathlib import Path


PLUGIN_NAME = "z80-skills"


def main() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    home = Path.home()
    expected_plugin_root = home / "plugins" / PLUGIN_NAME
    if plugin_root != expected_plugin_root:
        raise SystemExit(
            f"Clone or move this repository to {expected_plugin_root} before installing. "
            f"Current path: {plugin_root}"
        )

    marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
    marketplace_path.parent.mkdir(parents=True, exist_ok=True)

    if marketplace_path.exists():
        data = json.loads(marketplace_path.read_text(encoding="utf-8"))
    else:
        data = {
            "name": "personal",
            "interface": {"displayName": "Personal"},
            "plugins": [],
        }

    data.setdefault("name", "personal")
    data.setdefault("interface", {}).setdefault("displayName", "Personal")
    plugins = data.setdefault("plugins", [])
    entry = {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": f"./plugins/{PLUGIN_NAME}",
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

    marketplace_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {marketplace_path}")
    print(f"Run: codex plugin add {PLUGIN_NAME}@{data['name']}")


if __name__ == "__main__":
    main()

