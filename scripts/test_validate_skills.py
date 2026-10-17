#!/usr/bin/env python3
"""Regression coverage for the repository-owned skill validator."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from validate_skills import validate_skill, yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_skills.py"
FRONTMATTER = "name: example\ndescription: Example skill\n"
SPECIALISTS = {
    "audit-z80", "debug-z80", "develop-z80", "document-z80", "optimize-z80",
    "organize-z80", "port-spectranext", "send-bridgezx", "shrink-z80",
}


class ValidateSkillsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def write_skill(self, frontmatter=FRONTMATTER, body="# Example\n", directory=None):
        directory = directory or self.directory
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "SKILL.md").write_text(
            f"---\n{frontmatter}---\n\n{body}", encoding="utf-8"
        )
        return directory

    def check(self, frontmatter=FRONTMATTER, body="# Example\n"):
        return validate_skill(self.write_skill(frontmatter, body))

    def run_cli(self, *arguments, script=VALIDATOR, env=None, isolated=False):
        return subprocess.run(
            [sys.executable, *(["-I", "-S"] if isolated else []), str(script),
             *map(str, arguments)],
            cwd=self.directory,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_invocation_field_is_optional(self):
        self.assertTrue(self.check()[0])

    def test_boolean_invocation_values_are_accepted(self):
        for value in ("true", "false"):
            with self.subTest(value=value):
                valid, message = self.check(FRONTMATTER + f"disable-model-invocation: {value}\n")
                self.assertTrue(valid, message)

    def test_non_boolean_invocation_values_are_rejected(self):
        for value in ('"true"', '"false"', "0", "1", "null", "[]", "{}"):
            with self.subTest(value=value):
                valid, message = self.check(FRONTMATTER + f"disable-model-invocation: {value}\n")
                self.assertFalse(valid)
                self.assertEqual(message, "disable-model-invocation must be a boolean")

    def test_unknown_keys_are_rejected(self):
        for extra in ("disable-model-invocations: true\n", "unknown: true\n1: value\n"):
            with self.subTest(extra=extra):
                valid, message = self.check(FRONTMATTER + extra)
                self.assertFalse(valid)
                self.assertIn("Unexpected key(s)", message)

    def test_existing_optional_fields_remain_accepted(self):
        valid, message = self.check(
            FRONTMATTER + "license: MIT\nallowed-tools: Read\nmetadata:\n  version: 1\n"
        )
        self.assertTrue(valid, message)

    def test_missing_file_and_frontmatter_are_rejected(self):
        self.assertEqual(validate_skill(self.directory), (False, "SKILL.md not found"))
        for content, expected in (
            ("# No frontmatter", "No YAML frontmatter found"),
            ("---\nname: example\n", "Invalid frontmatter format"),
        ):
            with self.subTest(content=content):
                (self.directory / "SKILL.md").write_text(content, encoding="utf-8")
                self.assertEqual(validate_skill(self.directory), (False, expected))

    def test_malformed_and_nonmapping_yaml_are_rejected(self):
        for frontmatter, expected in (
            ("name: [\n", "Invalid YAML in frontmatter"),
            ("- example\n", "Frontmatter must be a YAML dictionary"),
            ("\n", "Frontmatter must be a YAML dictionary"),
        ):
            with self.subTest(frontmatter=frontmatter):
                valid, message = self.check(frontmatter)
                self.assertFalse(valid)
                self.assertIn(expected, message)

    def test_missing_required_fields_are_rejected(self):
        for frontmatter, field in (("description: Example\n", "name"), ("name: example\n", "description")):
            with self.subTest(field=field):
                self.assertEqual(self.check(frontmatter), (False, f"Missing '{field}' in frontmatter"))

    def test_invalid_names_are_rejected(self):
        for name in ("Example", "with_underscore", "-example", "example-", "two--hyphens", "a" * 65, 3, None):
            with self.subTest(name=name):
                self.assertFalse(self.check(yaml.safe_dump({"name": name, "description": "Example"}))[0])

    def test_invalid_descriptions_are_rejected(self):
        for description in (3, None, "<example>", "a" * 1025, "[TODO: explain]"):
            with self.subTest(description=description):
                self.assertFalse(self.check(yaml.safe_dump({"name": "example", "description": description}))[0])

    def test_name_and_description_limits_and_utf8_are_accepted(self):
        valid, message = self.check(yaml.safe_dump({"name": "a" * 64, "description": "ñ" * 1024}))
        self.assertTrue(valid, message)

    def test_instruction_placeholders_outside_fences_are_rejected(self):
        for body in ("[TODO: finish]\n", "   [TODO: finish] \t\n", "```text\nexample\n```\n[TODO: finish]\n"):
            with self.subTest(body=body):
                self.assertEqual(self.check(body=body), (False, "Skill instructions contain an unfinished TODO placeholder"))

    def test_example_placeholders_in_fences_are_accepted(self):
        for body in (
            "```text\n[TODO: example]\n```\n",
            "~~~~markdown\n```\n[TODO: example]\n~~~~\n",
            "- ```text\n  [TODO: example]\n  ```\n",
            "1. ~~~text\n[TODO: example]\n~~~\n",
            "````text\n```\n[TODO: example]\n````\n",
        ):
            with self.subTest(body=body):
                valid, message = self.check(body=body)
                self.assertTrue(valid, message)

    def test_single_directory_cli_accepts_valid_and_rejects_invalid(self):
        self.write_skill()
        valid = self.run_cli(self.directory)
        self.assertEqual(valid.returncode, 0, valid.stderr + valid.stdout)
        self.write_skill(FRONTMATTER + "unknown: true\n")
        invalid = self.run_cli(self.directory)
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("Unexpected key(s)", invalid.stdout)

    def test_all_directory_cli_reports_each_skill_and_fails_if_any_invalid(self):
        script = self.directory / "scripts" / VALIDATOR.name
        script.parent.mkdir()
        shutil.copyfile(VALIDATOR, script)
        self.write_skill(directory=self.directory / "skills" / "valid")
        self.write_skill(FRONTMATTER + "unknown: true\n", directory=self.directory / "skills" / "invalid")
        result = self.run_cli(script=script)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("valid: Skill is valid!", result.stdout)
        self.assertIn("invalid: Unexpected key(s)", result.stdout)

    def test_missing_yaml_dependency_has_actionable_diagnostic(self):
        result = self.run_cli(isolated=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PyYAML is required", result.stderr)
        self.assertIn("requirements-validation.txt", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_is_independent_of_missing_replaced_or_broken_system_validator(self):
        skill = self.write_skill(FRONTMATTER + "disable-model-invocation: true\n")
        codex_home = self.directory / "codex-home"
        external = codex_home / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py"
        for state, content in (
            ("missing", None),
            ("replaced", "raise SystemExit('replacement must not run')\n"),
            ("broken", "this is invalid python !!!\n"),
        ):
            with self.subTest(state=state):
                if content is not None:
                    external.parent.mkdir(parents=True, exist_ok=True)
                    external.write_text(content, encoding="utf-8")
                result = self.run_cli(skill, env={**os.environ, "CODEX_HOME": str(codex_home)})
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_repository_skills_validate_without_changing_invocation_policy_or_inputs(self):
        skills = sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir())
        self.assertEqual({skill.name for skill in skills}, SPECIALISTS | {"route-z80", "workflow"})
        paths = [path for skill in skills for path in (skill / "SKILL.md", skill / "agents" / "openai.yaml")]
        before = {path: path.read_bytes() for path in paths}
        for skill in skills:
            with self.subTest(skill=skill.name):
                frontmatter = yaml.safe_load((skill / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
                agent = yaml.safe_load((skill / "agents" / "openai.yaml").read_text(encoding="utf-8"))
                if skill.name in SPECIALISTS:
                    self.assertIs(frontmatter["disable-model-invocation"], True)
                    self.assertIs(agent["policy"]["allow_implicit_invocation"], False)
                else:
                    self.assertNotIn("disable-model-invocation", frontmatter)
                    self.assertIs(agent["policy"]["allow_implicit_invocation"], True)
                valid, message = validate_skill(skill)
                self.assertTrue(valid, message)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 11)
        self.assertEqual(before, {path: path.read_bytes() for path in paths})


if __name__ == "__main__":
    unittest.main()
