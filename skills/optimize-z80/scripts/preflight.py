#!/usr/bin/env python3
"""Read-only preflight for Z80/Spectrum optimization analysis."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 fallback for simple policy files.
    tomllib = None

SOURCE_EXTS = {".c", ".h", ".asm", ".s", ".inc", ".py", ".cfg", ".ld", ".lst", ".lis"}
ARTIFACT_GLOBS = {
    "maps": ["*.map"],
    "symbols": ["*.sym", "*.noi", "*.sld"],
    "listings": ["*.lst", "*.lis"],
    "generated_asm": ["*.asm", "*.opt"],
    "size_reports": ["size_report*.json", "*size*.json"],
    "overlay_sizes": ["overlay_sizes*.json"],
    "logs": ["*.log"],
    "taps": ["*.tap", "*.TAP"],
    "snapshots": ["*.sna", "*.z80", "*.szx"],
    "binaries": ["*.bin", "*.ovl", "*.OVL", "*.dat", "*.DAT"],
    "sdcc_dumps": ["*.adb", "*.adb.json", "*.dump", "*.ic", "*.graph"],
}
CORE_IGNORE_DIRS = {".git", ".hg", ".svn", "__pycache__", "node_modules"}
SOURCE_IGNORE_DIRS = CORE_IGNORE_DIRS | {
    "build",
    "release",
    "dist",
    ".mex",
}
ARTIFACT_IGNORE_DIRS = CORE_IGNORE_DIRS | {".mex"}


def ignored(p: Path, root: Path, ignore_dirs=SOURCE_IGNORE_DIRS) -> bool:
    # Match ignore_dirs only against path components inside root, so a repo that
    # happens to live under a dir named build/dist/... is still scanned.
    try:
        parts = p.relative_to(root).parts
    except ValueError:
        parts = p.parts
    return any(part in ignore_dirs for part in parts)


def run(cmd, cwd, timeout=5):
    try:
        p = subprocess.run(
            cmd, cwd=str(cwd), text=True, capture_output=True, timeout=timeout
        )
        return {
            "ok": p.returncode == 0,
            "code": p.returncode,
            "out": p.stdout.strip(),
            "err": p.stderr.strip(),
            "cmd": cmd,
        }
    except Exception as e:
        return {"ok": False, "code": None, "out": "", "err": str(e), "cmd": cmd}


def rel(p: Path, root: Path) -> str:
    try:
        return p.relative_to(root).as_posix()
    except Exception:
        return str(p)


def visible_files(root: Path, ignore_dirs=SOURCE_IGNORE_DIRS):
    for p in root.rglob("*"):
        if ignored(p, root, ignore_dirs) or not p.is_file():
            continue
        yield p


def find_artifacts(root: Path):
    out = {}
    for key, globs in ARTIFACT_GLOBS.items():
        hits = []
        for g in globs:
            hits.extend(root.rglob(g))
        out[key] = sorted(
            {rel(p, root) for p in hits if not ignored(p, root, ARTIFACT_IGNORE_DIRS)}
        )[:120]
    return out


def detect_sources(root: Path):
    exts = {".c": 0, ".h": 0, ".asm": 0, ".s": 0, ".inc": 0, ".py": 0}
    newest = None
    for p in visible_files(root):
        e = p.suffix.lower()
        if e in exts:
            exts[e] += 1
        if e in SOURCE_EXTS:
            m = p.stat().st_mtime
            if newest is None or m > newest[1]:
                newest = (p, m)
    return exts, newest


def freshness(root: Path, artifacts, newest_source):
    if newest_source is None:
        return {
            "status": "unknown",
            "method": "mtime_heuristic",
            "reason": "no source files detected",
        }
    candidates = []
    for key in ("maps", "size_reports", "overlay_sizes", "taps", "binaries"):
        for r in artifacts.get(key, []):
            p = root / r
            if p.exists():
                candidates.append((key, p, p.stat().st_mtime))
    if not candidates:
        return {
            "status": "missing",
            "method": "mtime_heuristic",
            "reason": "no build artifacts detected",
            "newest_source": rel(newest_source[0], root),
        }
    newest_art = max(candidates, key=lambda x: x[2])
    stale = newest_source[1] > newest_art[2]
    return {
        "status": "mtime_stale" if stale else "mtime_fresh_or_unknown",
        "method": "mtime_heuristic",
        "newest_source": rel(newest_source[0], root),
        "newest_artifact": rel(newest_art[1], root),
        "message": "MTIME BASELINE STALE, rebuild required for proven deltas"
        if stale
        else "mtime heuristic only; rebuild current worktree for PROVEN deltas",
    }


def load_policy(root: Path):
    for name in (".z80opt.toml", "z80opt.toml"):
        path = root / name
        if not path.is_file():
            continue
        try:
            if tomllib:
                return {
                    "status": "declared",
                    "path": rel(path, root),
                    "data": tomllib.loads(path.read_text(encoding="utf-8")),
                }
            return {
                "status": "declared_unparsed",
                "path": rel(path, root),
                "data": {},
                "warning": "tomllib unavailable",
            }
        except Exception as e:
            return {
                "status": "invalid",
                "path": rel(path, root),
                "data": {},
                "error": str(e),
            }
    return {"status": "inferred", "path": None, "data": {}}


def content_hints(root: Path):
    hints = set()
    hardware = set()
    abi = set()
    toolchain = set()
    scan_exts = {".asm", ".s", ".inc", ".c", ".h", ".cfg", ".ld", ".lst", ".lis"}
    for p in visible_files(root):
        if p.suffix.lower() not in scan_exts:
            continue
        try:
            t = p.read_text(errors="ignore").lower()[:200000]
        except Exception:
            continue
        if any(x in t for x in ("out (0xfe", "out(0xfe", "out (254", "out(254", "+zx", "spectrum", "esxdos", "divmmc")):
            hints.add("zx-spectrum")
        if any(x in t for x in ("out (0xfe", "out(0xfe", "out (254", "out(254")):
            hints.add("graphics-render")
            hardware.add("border-or-beeper")
        if "im 2" in t or " im2" in t:
            hints.add("interrupts")
            hardware.add("im2")
        if "#pragma output" in t or "z88dk" in t or "+zx" in t:
            hints.add("c-heavy")
            toolchain.add("z88dk")
        if any(x in t for x in ("__z88dk_fastcall", "__smallc", "__z88dk_callee", "__sdcccall", "__naked")):
            abi.add("custom-abi")
        if "__z88dk_fastcall" in t:
            abi.add("fastcall")
        if "__z88dk_callee" in t:
            abi.add("callee")
        if "__sdcccall" in t:
            abi.add("sdcccall")
        if "__naked" in t:
            abi.add("naked")
        if any(x in t for x in ("sdcc", "zsdcc", "--dump-i-code", "--dump-graphs", "--peep-file")):
            toolchain.add("sdcc")
        if any(x in t for x in ("sjasmplus", "device zxspectrum", "sldopt")):
            toolchain.add("sjasmplus")
        if "pasmo" in t:
            toolchain.add("pasmo")
        if any(x in t for x in ("0xfffd", "$fffd", "65533", "0xbffd", "$bffd", "49149", "ay-3-8912", "psg")):
            hardware.add("ay")
        if any(x in t for x in ("in a,(0xfe", "in a,($fe", "in a,(254", "keyboard")):
            hardware.add("keyboard")
        if any(x in t for x in ("in a,(0xff", "in a,($ff", "floating bus")):
            hardware.add("floating-bus")
        if any(x in t for x in ("org 0x8000", "org $8000", "org 32768")):
            hints.add("asm-heavy")
        if any(x in t for x in ("cpm", "bdos", "bios", "0x0005", "$0005")):
            hints.add("cpm")
        if "msx" in t or "vdp" in t:
            hints.add("msx")
        if "amstrad" in t or "cpc" in t:
            hints.add("cpc")
        if any(x in t for x in ("+2a", "plus3", "+3")):
            hardware.add("128k-family")
        if "rc2014" in t:
            hints.add("rc2014")
    return hints, hardware, abi, toolchain

def detect_target(root: Path, artifacts, hints, policy):
    declared = str(policy.get("data", {}).get("target", "") or "").strip()
    if declared and declared != "unknown":
        return {"target": declared, "source": "policy"}
    names = "\n".join(rel(p, root).lower() for p in visible_files(root))
    if "zx-spectrum" in hints or "spectrum" in names or artifacts.get("taps"):
        return {"target": "zx-spectrum", "source": "hints"}
    for target in ("msx", "cpc", "cpm", "rc2014", "next"):
        if target in hints or target in names:
            return {"target": target, "source": "hints"}
    return {
        "target": declared or "unknown",
        "source": "policy" if declared else "inferred",
    }


def policy_rejects(policy):
    forbidden = (
        policy.get("data", {}).get("forbidden", {})
        if isinstance(policy.get("data"), dict)
        else {}
    )
    return sorted(k for k, v in forbidden.items() if v is True)


def detect_build_hints(root: Path, policy):
    data = policy.get("data", {}) if isinstance(policy.get("data"), dict) else {}
    build = data.get("build", {}) if isinstance(data.get("build", {}), dict) else {}
    files = []
    for name in ("Makefile", "makefile", "GNUmakefile", "build.ps1", "build.bat"):
        path = root / name
        if path.is_file():
            files.append(name)
    tools = {}
    for name in ("make", "zcc", "z80asm", "sdcc", "sjasmplus", "pasmo", "appmake", "z88dk-z80nm", "z88dk-dis", "z88dk-ticks", "fuse"):
        tools[name] = bool(shutil.which(name))
    return {
        "policy_command": str(build.get("command", "") or ""),
        "files": files,
        "tools": tools,
        "note": "hints only; preflight does not run builds",
    }

def detect_profile(root: Path, artifacts, sources, hints):
    names = "\n".join(rel(p, root).lower() for p in visible_files(root))
    profile = list(hints)
    if "spectrum" in names or "zx" in names or artifacts.get("taps"):
        profile.append("zx-spectrum")
    if sources.get(".c", 0) and (sources.get(".asm", 0) or sources.get(".s", 0)):
        profile.append("mixed-c-asm")
    elif sources.get(".c", 0):
        profile.append("c-heavy")
    elif sources.get(".asm", 0) or sources.get(".s", 0):
        profile.append("asm-heavy")
    if "overlay" in names or artifacts.get("overlay_sizes"):
        profile.append("overlays-banking")
    if any(k in names for k in ("uart", "mqtt", "serial", "wifi", "esp")):
        profile.append("transport-io")
    if any(k in names for k in ("screen", "sprite", "render", "display", "bitmap")):
        profile.append("graphics-render")
    return sorted(set(profile)) or ["unknown"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    git_branch = run(["git", "branch", "--show-current"], root)
    git_status = run(["git", "status", "--short", "--branch"], root)
    artifacts = find_artifacts(root)
    sources, newest_source = detect_sources(root)
    policy = load_policy(root)
    hints, hardware_hints, abi_hints, toolchain_hints = content_hints(root)
    target = detect_target(root, artifacts, hints, policy)
    profiles = detect_profile(root, artifacts, sources, hints)
    forced_profile = str(policy.get("data", {}).get("profile", "") or "").strip()
    if forced_profile and forced_profile != "auto":
        profiles = sorted(set(profiles + [forced_profile]))
    data = {
        "root": str(root),
        "branch": git_branch.get("out", "") if git_branch["ok"] else None,
        "git_status_ok": git_status["ok"],
        "git_status": git_status.get("out", ""),
        "git_error": git_status.get("err", "") if not git_status["ok"] else "",
        "policy": policy,
        "target": target,
        "policy_rejects": policy_rejects(policy),
        "sources": sources,
        "artifacts": artifacts,
        "freshness": freshness(root, artifacts, newest_source),
        "build_hints": detect_build_hints(root, policy),
        "profile_hints": profiles,
        "content_hints": sorted(hints),
        "hardware_hints": sorted(hardware_hints),
        "abi_hints": sorted(abi_hints),
        "toolchain_hints": sorted(toolchain_hints),
        "guardrails": ["do not assume Spectrum hardware"]
        if target["target"] in {"unknown", "pure-z80"}
        else [],
        "process_traps": []
        if git_status["ok"]
        else [
            {
                "command": git_status["cmd"],
                "failure": git_status["err"],
                "workaround": "use narrower git commands or absolute git path",
            }
        ],
    }
    if args.json:
        print(json.dumps(data, indent=2))
        return
    print(f"root: {data['root']}")
    print(f"branch: {data['branch']}")
    print(
        f"policy: {data['policy']['status']} target={data['target']['target']} source={data['target']['source']}"
    )
    if data["policy_rejects"]:
        print("policy rejects: " + ", ".join(data["policy_rejects"]))
    if data["guardrails"]:
        print("guardrails: " + ", ".join(data["guardrails"]))
    print("profiles: " + ", ".join(data["profile_hints"]))
    print(
        "freshness: "
        + data["freshness"]["status"]
        + " - "
        + data["freshness"].get("message", data["freshness"].get("reason", ""))
    )
    build = data["build_hints"]
    if build["policy_command"]:
        print("build command: " + build["policy_command"])
    if build["files"]:
        print("build files: " + ", ".join(build["files"]))
    available_tools = [k for k, v in build["tools"].items() if v]
    if available_tools:
        print("build tools on PATH: " + ", ".join(available_tools))
    print("sources: " + ", ".join(f"{k}={v}" for k, v in data["sources"].items() if v))
    for key, vals in data["artifacts"].items():
        if vals:
            print(f"{key}: {len(vals)}")
            for v in vals[:8]:
                print(f"  - {v}")
    if data["process_traps"]:
        print("process traps:")
        for t in data["process_traps"]:
            print(f"  - {t['failure']}")


if __name__ == "__main__":
    main()
