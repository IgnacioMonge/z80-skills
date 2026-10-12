"""Tests for install.py (no network, no venv)."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import install  # noqa: E402
from llm import load_env  # noqa: E402


def test_write_env_replaces_keys_and_keeps_other_lines(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# keep me\nOTHER=1\nANTHROPIC_API_KEY=old\nANTHROPIC_WORKSPACE_ID=wrkspc_old\n")
    install.write_env(env, {"ANTHROPIC_API_KEY": "new", "ANTHROPIC_WORKSPACE_ID": ""})
    assert env.read_text().splitlines() == ["# keep me", "OTHER=1", "ANTHROPIC_API_KEY=new"]
    assert load_env(env) == {"OTHER": "1", "ANTHROPIC_API_KEY": "new"}


def test_write_env_creates_file(tmp_path):
    env = tmp_path / ".env"
    install.write_env(env, {"ANTHROPIC_API_KEY": "k", "ANTHROPIC_WORKSPACE_ID": "w"})
    assert load_env(env) == {"ANTHROPIC_API_KEY": "k", "ANTHROPIC_WORKSPACE_ID": "w"}
