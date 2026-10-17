#!/usr/bin/env python3
"""Validate repository skills, or one supplied skill directory."""

# Adapted from skill-creator's quick_validate.py; owned here to survive updates.
import re
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError as error:
    if error.name != "yaml":
        raise
    raise SystemExit(
        "PyYAML is required. Install validation dependencies with: "
        "python3 -m pip install -r scripts/requirements-validation.txt"
    ) from None

MAX_SKILL_NAME_LENGTH = 64


def validate_skill(skill_path):
    """Return whether a skill passes the supported frontmatter and scaffold checks."""
    skill_path = Path(skill_path)
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False, "No YAML frontmatter found"

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    try:
        frontmatter = yaml.safe_load(match.group(1))
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as error:
        return False, f"Invalid YAML in frontmatter: {error}"

    allowed_properties = {
        "name", "description", "license", "allowed-tools", "metadata",
        "disable-model-invocation",
    }
    unexpected_keys = set(frontmatter.keys()) - allowed_properties
    if unexpected_keys:
        allowed = ", ".join(sorted(allowed_properties))
        unexpected = ", ".join(sorted(map(str, unexpected_keys)))
        return (
            False,
            f"Unexpected key(s) in SKILL.md frontmatter: {unexpected}. Allowed properties are: {allowed}",
        )

    if "disable-model-invocation" in frontmatter and not isinstance(
        frontmatter["disable-model-invocation"], bool
    ):
        return False, "disable-model-invocation must be a boolean"

    if "name" not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if "description" not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    name = frontmatter.get("name", "")
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        if not re.match(r"^[a-z0-9-]+$", name):
            return (
                False,
                f"Name '{name}' should be hyphen-case (lowercase letters, digits, and hyphens only)",
            )
        if name.startswith("-") or name.endswith("-") or "--" in name:
            return (
                False,
                f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens",
            )
        if len(name) > MAX_SKILL_NAME_LENGTH:
            return (
                False,
                f"Name is too long ({len(name)} characters). "
                f"Maximum is {MAX_SKILL_NAME_LENGTH} characters.",
            )

    description = frontmatter.get("description", "")
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if description.startswith("[TODO:"):
        return False, "Description contains an unfinished TODO placeholder"
    if description:
        if "<" in description or ">" in description:
            return False, "Description cannot contain angle brackets (< or >)"
        if len(description) > 1024:
            return (
                False,
                f"Description is too long ({len(description)} characters). Maximum is 1024 characters.",
            )

    body = content[match.end():]
    fence_marker = None
    fence_length = 0
    for line in body.splitlines():
        fence = re.match(r"^[ \t]*(?:(?:[-+*]|\d+[.)])[ \t]+)?(`{3,}|~{3,})(.*)$", line)
        if fence:
            marker = fence.group(1)
            if fence_marker is None:
                fence_marker = marker[0]
                fence_length = len(marker)
            elif (
                marker[0] == fence_marker
                and len(marker) >= fence_length
                and not fence.group(2).strip()
            ):
                fence_marker = None
                fence_length = 0
            continue

        if fence_marker is None and re.fullmatch(
            r"[ ]{0,3}\[TODO:[^\n]*\][ \t]*", line
        ):
            return False, "Skill instructions contain an unfinished TODO placeholder"

    return True, "Skill is valid!"


def main():
    if len(sys.argv) > 2:
        print("Usage: python3 scripts/validate_skills.py [skill_directory]", file=sys.stderr)
        return 1

    if len(sys.argv) == 2:
        skills = [Path(sys.argv[1])]
    else:
        skills = sorted(
            path for path in (Path(__file__).resolve().parents[1] / "skills").iterdir()
            if path.is_dir()
        )
    if not skills:
        print("No skill directories found", file=sys.stderr)
        return 1

    all_valid = True
    for skill in skills:
        try:
            valid, message = validate_skill(skill)
        except (OSError, UnicodeError) as error:
            valid, message = False, str(error)
        print(f"{skill.name}: {message}")
        all_valid = all_valid and valid
    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
