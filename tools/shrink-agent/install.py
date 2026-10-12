#!/usr/bin/env python3
"""Set up shrink-agent: a Python 3.11+ venv with the Claude SDK, and the API key file.

    python3 tools/shrink-agent/install.py [--python PATH]

Everything goes under ~/.z80-skills, the tool's home: venv/ holds the SDK and
.env holds the key, outside any repository. Re-running keeps what is already
there and asks only for what is missing. Runs on any Python 3.8+; the venv
itself needs a 3.11+ interpreter, found on PATH or given with --python.
"""
from __future__ import annotations

import argparse
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from llm import load_env  # noqa: E402

HOME = Path.home() / ".z80-skills"
PACKAGES = ["anthropic", "pytest"]
CANDIDATES = [[sys.executable], ["python3.13"], ["python3.12"], ["python3.11"], ["python3"], ["python"], ["py", "-3"]]
VERIFY = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import anthropic
from llm import load_api_key, load_env
env_path = Path(sys.argv[2])
ws = load_env(env_path).get("ANTHROPIC_WORKSPACE_ID", "")
client = anthropic.Anthropic(api_key=load_api_key(env_path), max_retries=1,
                             default_headers={"anthropic-workspace-id": ws} if ws else None)
print("API key OK. Models visible:", ", ".join(m.id for m in client.models.list(limit=3).data))
"""


def find_python(override: str | None) -> list[str]:
    """Return the first interpreter command that reports Python 3.11 or newer."""
    for cmd in ([[override]] if override else []) + CANDIDATES:
        exe = shutil.which(cmd[0])
        if not exe:
            continue
        probe = subprocess.run(
            [exe, *cmd[1:], "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"],
            capture_output=True, text=True,
        )
        if probe.returncode == 0 and tuple(int(n) for n in probe.stdout.split()) >= (3, 11):
            return [exe, *cmd[1:]]
    sys.exit("No Python 3.11+ found. Install one (python.org, brew, `uv python install 3.11`) or pass --python PATH.")


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_venv(home: Path, python: list[str]) -> Path:
    """Create home/venv if missing and install (or upgrade) the packages into it."""
    venv = home / "venv"
    py = venv_python(venv)
    if not py.exists():
        print(f"Creating {venv} with {python[0]}")
        subprocess.run([*python, "-m", "venv", str(venv)], check=True)
    print(f"Installing {' '.join(PACKAGES)} into {venv}")
    subprocess.run([str(py), "-m", "pip", "install", "--quiet", "--upgrade", *PACKAGES], check=True)
    return py


def write_env(path: Path, values: dict[str, str]) -> None:
    """Set keys in a dotenv file, keeping every other line. An empty value drops the key."""
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.is_file() else []
    kept = [line for line in lines if line.split("=", 1)[0].strip() not in values]
    kept += [f"{key}={value}" for key, value in values.items() if value]
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    if os.name != "nt":
        path.chmod(0o600)


def mask(secret: str) -> str:
    return f"{secret[:7]}...{secret[-4:]}" if len(secret) > 12 else "(set)"


def ask_credentials(current: dict[str, str]) -> dict[str, str]:
    key = current.get("ANTHROPIC_API_KEY", "")
    hint = f" [Enter keeps {mask(key)}]" if key else ""
    key = getpass.getpass(f"Anthropic API key (Console -> API keys){hint}: ").strip() or key
    if not key:
        sys.exit("An API key is required.")
    ws = current.get("ANTHROPIC_WORKSPACE_ID", "")
    hint = f" [Enter keeps {ws}]" if ws else " [Enter to skip]"
    ws = input(f"Workspace ID, only if the key is not scoped to one (wrkspc_...){hint}: ").strip() or ws
    return {"ANTHROPIC_API_KEY": key, "ANTHROPIC_WORKSPACE_ID": ws}


def verify(py: Path, env_path: Path) -> bool:
    """One free Models API call through the tool's own key loader; the key never hits argv."""
    result = subprocess.run([str(py), "-c", VERIFY, str(HERE), str(env_path)], capture_output=True, text=True)
    text = result.stdout.strip() or result.stderr.strip().splitlines()[-1]
    print(text)
    if result.returncode != 0 and "workspace" in text.lower():
        print("Fix: run this again and enter the workspace ID (Console -> Settings -> Workspaces).")
    return result.returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--python", help="Python 3.11+ interpreter for the venv (default: first one found on PATH)")
    args = ap.parse_args()

    python = find_python(args.python)
    HOME.mkdir(mode=0o700, exist_ok=True)
    env_path = HOME / ".env"
    write_env(env_path, ask_credentials(load_env(env_path) if env_path.is_file() else {}))
    py = ensure_venv(HOME, python)
    ok = verify(py, env_path)
    if not shutil.which("zcc"):
        print("Warning: zcc (z88dk) is not on PATH; builds will fail until it is.")
    print()
    print("Ready." if ok else "Key not verified: fix the problem above and run this again.")
    print(f"Config:  copy {HERE / 'examples' / 'template.toml'} and set project.root and targets for your project.")
    print(f"Dry run: {py} {HERE / 'shrink_agent.py'} --config <your.toml> --dry-run")
    print(f"Tests:   {py} -m pytest -q {HERE}")


if __name__ == "__main__":
    main()
