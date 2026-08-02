#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest


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
            "plugins": [{"name": "other", "source": {"path": "./other"}}],
        }
        data = INSTALLER.marketplace_data(original, "./src/z80-skills")
        self.assertEqual(
            [item["name"] for item in data["plugins"]], ["other", "z80-skills"]
        )
        self.assertEqual(data["plugins"][1]["source"]["path"], "./src/z80-skills")


if __name__ == "__main__":
    unittest.main()
