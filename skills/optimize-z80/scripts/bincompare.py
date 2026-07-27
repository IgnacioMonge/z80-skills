#!/usr/bin/env python3
"""Diff build artifacts by size and JSON numeric keys."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def flatten(prefix, value, out):
    if isinstance(value, dict):
        for k, v in value.items():
            flatten(f"{prefix}.{k}" if prefix else str(k), v, out)
    elif isinstance(value, (int, float)):
        out[prefix] = value


def read_json(path):
    try:
        data = json.loads(Path(path).read_text())
        out = {}
        flatten("", data, out)
        return out
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    args = ap.parse_args()
    a = Path(args.before)
    b = Path(args.after)
    ja = read_json(a)
    jb = read_json(b)
    if ja is not None and jb is not None:
        keys = sorted(set(ja) | set(jb))
        for k in keys:
            va, vb = ja.get(k), jb.get(k)
            if va != vb and isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                print(f"{k}: {va} -> {vb} ({vb - va:+})")
        return
    print(f"{a.name}: {a.stat().st_size}")
    print(f"{b.name}: {b.stat().st_size} ({b.stat().st_size - a.stat().st_size:+})")


if __name__ == "__main__":
    main()
