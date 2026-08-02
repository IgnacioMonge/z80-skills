#!/usr/bin/env python3
import io
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).with_name("install_personal_marketplace.py")
SPEC = importlib.util.spec_from_file_location("marketplace_installer", SCRIPT)
assert SPEC and SPEC.loader
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


class PersonalMarketplaceTest(unittest.TestCase):
    def test_source_path_follows_checkout_location(self) -> None:
        source = INSTALLER.marketplace_source_path(
            Path("/Users/example/Developer/z80-skills"), Path("/Users/example")
        )
        self.assertEqual(source, "./Developer/z80-skills")

        with self.assertRaises(ValueError):
            INSTALLER.marketplace_source_path(
                Path("/opt/z80-skills"), Path("/Users/example")
            )

    def test_update_preserves_unrelated_entries(self) -> None:
        original = {
            "name": "personal",
            "plugins": [
                {"name": "other", "source": {"path": "./other"}},
                {"name": "z80-skills", "source": {"path": "./old"}},
            ],
        }
        data = INSTALLER.marketplace_data(original, "./src/z80-skills")
        self.assertEqual(
            [item["name"] for item in data["plugins"]], ["other", "z80-skills"]
        )
        self.assertEqual(data["plugins"][1]["source"]["path"], "./src/z80-skills")

    def test_atomic_write_preserves_original_when_replace_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            marketplace = Path(tmp) / "marketplace.json"
            marketplace.write_text("original\n", encoding="utf-8")

            with mock.patch.object(
                INSTALLER.Path,
                "replace",
                side_effect=OSError("replace failed"),
            ):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    INSTALLER.write_marketplace(marketplace, {"name": "new"})

            self.assertEqual(marketplace.read_text(encoding="utf-8"), "original\n")
            self.assertFalse(list(marketplace.parent.glob(".marketplace.json.*")))

    def test_main_preserves_catalog_and_warns_for_both_skill_locations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            marketplace = home / ".agents" / "plugins" / "marketplace.json"
            marketplace.parent.mkdir(parents=True)
            marketplace.write_text(
                json.dumps(
                    {
                        "name": "personal",
                        "plugins": [
                            {"name": "other", "source": {"path": "./other"}}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            conflicts = (
                home / ".agents" / "skills" / "workflow" / "SKILL.md",
                home / ".codex" / "skills" / "workflow" / "SKILL.md",
            )
            for conflict in conflicts:
                conflict.parent.mkdir(parents=True)
                conflict.write_text("---\nname: workflow\n---\n", encoding="utf-8")

            with (
                mock.patch.object(INSTALLER.Path, "home", return_value=home),
                mock.patch.object(
                    INSTALLER,
                    "marketplace_source_path",
                    return_value="./src/z80-skills",
                ),
                mock.patch("sys.stdout", new_callable=io.StringIO) as output,
            ):
                INSTALLER.main()

            data = json.loads(marketplace.read_text(encoding="utf-8"))
            self.assertEqual(
                [item["name"] for item in data["plugins"]],
                ["other", "z80-skills"],
            )
            for conflict in conflicts:
                self.assertIn(str(conflict.parent), output.getvalue())
            self.assertFalse(list(marketplace.parent.glob(".marketplace.json.*")))


if __name__ == "__main__":
    unittest.main()
