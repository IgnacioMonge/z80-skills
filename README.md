# Z80 Skills

Codex plugin containing two skills:

- `audit-z80`: evidence-first audit workflow for mixed Z80 ASM and C projects on ZX Spectrum.
- `shrink-z80`: binary-size optimization workflow for mixed Z80 ASM and C projects.

## Contents

```text
.codex-plugin/plugin.json
skills/audit-z80/
skills/shrink-z80/
```

Both skills include their `SKILL.md`, `agents/openai.yaml`, `references/`, and `scripts/` files.

## Local Install

From the plugin source directory:

```sh
codex plugin add z80-skills@personal
```

Then start a new Codex thread so the newly installed skills are loaded.

## Online Transfer To MacBook

Preferred route:

1. Push this directory to a private GitHub repository.
2. On the MacBook, clone the repository into `~/plugins/z80-skills`.
3. Run:

```sh
python3 scripts/install_personal_marketplace.py
codex plugin add z80-skills@personal
```

4. Start a new Codex thread.

No manual file copying between computers is needed; GitHub or another online sync target carries the plugin source.
