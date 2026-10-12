"""Offline tests for shrink-agent (no z88dk, no API)."""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mapfile  # noqa: E402
import shrink_agent as sa  # noqa: E402
from llm import ApiFatal, load_api_key, usage_cost  # noqa: E402

MAP = textwrap.dedent(
    """\
    _alpha                          = $6000 ; addr, local, , src_main_build_c, code_compiler, src\\a.c::alpha::0::12:40
    i_1                             = $6010 ; addr, local, , src_main_build_c, code_compiler, src\\a.c::alpha::0::12:41
    _beta                           = $6030 ; addr, local, , src_main_build_c, code_compiler, src\\b.c::beta::0::3:7
    _gamma_alias                    = $6050 ; addr, public, , x_asm, code_user, asm/x.asm:5
    _gamma                          = $6050 ; addr, public, , x_asm, code_user, asm/x.asm:6
    loop                            = $6055 ; addr, local, , x_asm, code_user, asm/x.asm:9
    _delta                          = $6060 ; addr, public, , x_asm, code_user, asm/x.asm:20
    RING                            = $0800 ; const, local, , x_asm, code_user, asm/x.asm:2
    __code_compiler_tail            = $6050 ; const, public, def, , ,
    __code_user_tail                = $6070 ; const, public, def, , ,
    __data_compiler_tail            = $7000 ; const, public, def, , ,
    """
)


def test_routines_sizes_and_locations():
    syms = mapfile.parse_map_text(MAP)
    assert mapfile.symbol_value(syms, "__data_compiler_tail") == 0x7000
    rs = {r.name: r for r in mapfile.routines(syms, ["code_compiler", "code_user"])}
    assert rs["alpha"].size == 0x30 and rs["alpha"].file == "src/a.c" and rs["alpha"].line == 40
    assert rs["beta"].size == 0x20 and rs["beta"].lang == "c"
    assert rs["_gamma_alias"].size == 0x10 and rs["_gamma_alias"].lang == "asm" and rs["_gamma_alias"].line == 5
    assert "_gamma" not in rs  # same-address alias collapses onto the earlier label
    assert rs["_delta"].size == 0x10
    assert [r.name for r in mapfile.routines(syms, ["code_compiler", "code_user"])][0] == "alpha"


def test_c_function_span_ignores_braces_in_strings_and_comments():
    src = textwrap.dedent(
        """\
        int other(void);

        /* doc */
        static int f(const char *s)
        {
            /* { */ const char *t = "}{"; // }
            if (s[0] == '{') { return 1; }
            return t[0];
        }
        int after;
        """
    ).splitlines()
    assert sa.c_function_span(src, 5) == (2, 8)


def test_asm_span_stops_before_next_routine_comments():
    src = ["; header", "_a:", "  ld a,1", "  ret", "; about b", "_b:", "  ret"]
    assert sa.asm_span(src, 2, [6]) == (0, 3)


def _cfg(tmp_path: Path, **kw) -> sa.Config:
    base = dict(name="t", root=tmp_path, editable=["src/*.c"], targets=[sa.Target("t", "", "out.map", "__data_compiler_tail", 0)])
    base.update(kw)
    return sa.Config(**base)


def test_apply_edits_rules_and_crlf(tmp_path):
    (tmp_path / "src").mkdir()
    f = tmp_path / "src" / "a.c"
    f.write_bytes(b"int a;\r\nint b;\r\nint b;\r\n")
    cfg = _cfg(tmp_path)
    assert "not editable" in sa.apply_edits(cfg, tmp_path, [{"file": "inc/x.h", "old": "a", "new": "b"}])[1]
    assert "not editable" in sa.apply_edits(cfg, tmp_path, [{"file": "src/../x.c", "old": "a", "new": "b"}])[1]
    assert "2 times" in sa.apply_edits(cfg, tmp_path, [{"file": "src/a.c", "old": "int b;", "new": "x"}])[1]
    diff, err = sa.apply_edits(cfg, tmp_path, [{"file": "src/a.c", "old": "int a;\nint b;", "new": "int a, b;"}])
    assert not err and "+int a, b;" in diff
    assert f.read_bytes() == b"int a, b;\r\nint b;\r\n"


def test_apply_edits_is_atomic(tmp_path):
    (tmp_path / "src").mkdir()
    f = tmp_path / "src" / "a.c"
    f.write_text("x\n")
    cfg = _cfg(tmp_path)
    err = sa.apply_edits(cfg, tmp_path, [{"file": "src/a.c", "old": "x", "new": "y"}, {"file": "src/a.c", "old": "zz", "new": "q"}])[1]
    assert err and f.read_text() == "x\n"


def test_usage_cost_and_unknown_model():
    usage = SimpleNamespace(input_tokens=1_000_000, output_tokens=100_000, cache_creation_input_tokens=0, cache_read_input_tokens=2_000_000)
    prices = {"m": (4.0, 20.0, 5.0, 0.2)}
    assert usage_cost("m", usage, prices) == pytest.approx(4.0 + 2.0 + 0.4)
    with pytest.raises(ApiFatal):
        usage_cost("other", usage, prices)


def test_load_api_key_reads_file_only(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-env")
    env = tmp_path / ".env"
    env.write_text('# c\nANTHROPIC_API_KEY="sk-test"\n')
    assert load_api_key(env) == "sk-test"
    with pytest.raises(ApiFatal):
        load_api_key(tmp_path / "missing.env")


# ------------------------------------------------------------- end to end

FAKE_BUILD = textwrap.dedent(
    """\
    # Fake linker: each C function's size is its body length without spaces.
    import re, sys
    from pathlib import Path
    src = Path("src/a.c").read_text()
    if "SYNTAX_ERROR" in src:
        print("error: syntax"); sys.exit(1)
    addr, lines = 0x6000, []
    for m in re.finditer(r"int (\\w+)\\(void\\)\\n\\{(.*?)\\n\\}", src, re.S):
        line = src[: m.start()].count("\\n") + 2
        lines.append(f"_{m[1]} = ${addr:04X} ; addr, local, , m, code_compiler, src\\\\a.c::{m[1]}::0::1:{line}")
        addr += len(re.sub(r"\\s", "", m[2]))
    lines.append(f"__code_compiler_tail = ${addr:04X} ; const, public, def, , ,")
    lines.append(f"__data_compiler_tail = ${addr:04X} ; const, public, def, , ,")
    Path("out.map").write_text("\\n".join(lines) + "\\n")
    """
)

FAKE_SRC = textwrap.dedent(
    """\
    int big(void)
    {
        return 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12;
    }

    int mid(void)
    {
        return 100 + 200 + 300 + 400 + 500;
    }
    """
)


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_end_to_end_with_scripted_agent(tmp_path, monkeypatch):
    proj = tmp_path / "proj"
    (proj / "src").mkdir(parents=True)
    (proj / "src" / "a.c").write_text(FAKE_SRC)
    (proj / "build.py").write_text(FAKE_BUILD)
    (proj / ".gitignore").write_text("out.map\n")
    _git(proj, "init", "-q", "-b", "main")
    _git(proj, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    _git(proj, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
    _git(proj, "config", "user.name", "t")
    _git(proj, "config", "user.email", "t@t")
    (proj / "untracked.txt").write_text("user work\n")

    cfg = tmp_path / "cfg.toml"
    cfg.write_text(
        textwrap.dedent(
            f"""\
            [project]
            name = "fake"
            root = "{proj.as_posix()}"
            editable = ["src/*.c"]
            [[targets]]
            name = "t1"
            build = "{{python}} build.py"
            map = "out.map"
            [agent]
            max_rounds = 2
            min_routine_size = 1
            knowledge = []
            """
        )
    )
    big_old = "return 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12;"
    mid_old = "return 100 + 200 + 300 + 400 + 500;"
    script = {
        "proposals": [
            # big: round 1 breaks the build, round 2 shrinks it -> accepted
            {"analysis": "x", "decision": "edit", "edits": [{"file": "src/a.c", "old": big_old, "new": "SYNTAX_ERROR"}]},
            {"analysis": "fold", "decision": "edit", "summary": "fold constant", "edits": [{"file": "src/a.c", "old": big_old, "new": "return 78;"}]},
            # mid: shrinks but reviewer says DIFFERENT, then declines
            {"analysis": "y", "decision": "edit", "edits": [{"file": "src/a.c", "old": mid_old, "new": "return 1;"}]},
            {"analysis": "no safe saving", "decision": "decline"},
        ],
        "verdicts": [
            {"analysis": "ok", "verdict": "EQUIVALENT"},
            {"analysis": "1 != 1500", "verdict": "DIFFERENT", "issues": ["returns 1 instead of 1500"]},
        ],
    }
    script_path = tmp_path / "script.json"
    script_path.write_text(json.dumps(script))
    monkeypatch.setenv("TEMP", str(tmp_path))
    runs = tmp_path / "runs"
    rc = sa.main(["--config", str(cfg), "--iterations", "5", "--mock-script", str(script_path), "--runs-dir", str(runs)])
    assert rc == 0

    branches = subprocess.run(["git", "branch", "--list", "shrink/auto-*"], cwd=proj, capture_output=True, text=True).stdout.split()
    assert len(branches) == 1
    branch = branches[0]
    log = subprocess.run(["git", "log", "--format=%s%n%b", f"main..{branch}"], cwd=proj, capture_output=True, text=True).stdout
    assert log.count("shrink(") == 1 and "shrink(big): fold constant" in log and "HW PENDING" in log
    shown = subprocess.run(["git", "show", f"{branch}:src/a.c"], cwd=proj, capture_output=True, text=True).stdout
    assert "return 78;" in shown and mid_old in shown
    # primary checkout untouched, worktree gone
    assert (proj / "src" / "a.c").read_text() == FAKE_SRC
    assert (proj / "untracked.txt").exists()
    wts = subprocess.run(["git", "worktree", "list"], cwd=proj, capture_output=True, text=True).stdout.strip().splitlines()
    assert len(wts) == 1
    compact = next(runs.glob("fake-*/shrink.log")).read_text()
    assert "ACCEPT" in compact and "DECLINE" in compact and "no candidates left" in compact


def test_dry_run_creates_no_branch(tmp_path, monkeypatch):
    proj = tmp_path / "proj"
    (proj / "src").mkdir(parents=True)
    (proj / "src" / "a.c").write_text(FAKE_SRC)
    (proj / "build.py").write_text(FAKE_BUILD)
    _git(proj, "init", "-q", "-b", "main")
    _git(proj, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    _git(proj, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
    cfg = tmp_path / "cfg.toml"
    cfg.write_text(f'[project]\nroot = "{proj.as_posix()}"\neditable = ["src/*.c"]\n[[targets]]\nname = "t"\nbuild = "{{python}} build.py"\nmap = "out.map"\n[agent]\nmin_routine_size = 1\n')
    monkeypatch.setenv("TEMP", str(tmp_path))
    assert sa.main(["--config", str(cfg), "--dry-run", "--runs-dir", str(tmp_path / "runs")]) == 0
    out = subprocess.run(["git", "branch", "--list", "shrink/*"], cwd=proj, capture_output=True, text=True).stdout
    assert out.strip() == ""


def test_fatal_api_error_stops_and_cleans_up(tmp_path, monkeypatch):
    proj = tmp_path / "proj"
    (proj / "src").mkdir(parents=True)
    (proj / "src" / "a.c").write_text(FAKE_SRC)
    (proj / "build.py").write_text(FAKE_BUILD)
    (proj / ".gitignore").write_text("out.map\n")
    _git(proj, "init", "-q", "-b", "main")
    _git(proj, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    _git(proj, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
    cfg = tmp_path / "cfg.toml"
    cfg.write_text(f'[project]\nroot = "{proj.as_posix()}"\neditable = ["src/*.c"]\n[[targets]]\nname = "t"\nbuild = "{{python}} build.py"\nmap = "out.map"\n[agent]\nmin_routine_size = 1\nknowledge = []\n')
    script = tmp_path / "s.json"
    script.write_text(json.dumps({"proposals": [{"raise_fatal": "400 key not scoped to a workspace"}]}))
    monkeypatch.setenv("TEMP", str(tmp_path))
    runs = tmp_path / "runs"
    assert sa.main(["--config", str(cfg), "--mock-script", str(script), "--runs-dir", str(runs)]) == 3
    assert subprocess.run(["git", "branch", "--list", "shrink/*"], cwd=proj, capture_output=True, text=True).stdout.strip() == ""
    assert len(subprocess.run(["git", "worktree", "list"], cwd=proj, capture_output=True, text=True).stdout.strip().splitlines()) == 1
    assert "API stopped the run" in next(runs.glob("*/shrink.log")).read_text()


class _Block(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {k: v for k, v in vars(self).items() if v is not None}


class _FakeMessages:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def create(self, **kw):
        self.calls.append(kw)
        return self.replies.pop(0)


def _reply(blocks, stop="end_turn"):
    usage = SimpleNamespace(input_tokens=1000, output_tokens=100, cache_creation_input_tokens=0, cache_read_input_tokens=0)
    return SimpleNamespace(content=blocks, usage=usage, stop_reason=stop)


def test_claude_call_uses_auto_choice_and_nudges_once():
    from llm import Claude

    tool = {"name": "submit_candidate", "input_schema": {"type": "object"}}
    fake = _FakeMessages([
        _reply([_Block(type="thinking", thinking="t", signature="s"), _Block(type="text", text="hmm")]),
        _reply([_Block(type="tool_use", name="submit_candidate", id="tu1", input={"decision": "decline"})], "tool_use"),
    ])
    c = Claude.__new__(Claude)
    c._anthropic, c.client, c.prices, c.spent = None, SimpleNamespace(messages=fake), {"m": (4.0, 20.0, 5.0, 0.2)}, 0.0
    c.tokens = {}
    call = c.call("m", ["sys"], [{"role": "user", "content": "go"}], tool, 100)
    assert call.data == {"decision": "decline"} and call.tool_use_id == "tu1"
    assert all(kw["tool_choice"] == {"type": "auto"} for kw in fake.calls)
    assert len(call.history) == 3 and call.history[1]["role"] == "assistant"
    assert call.cost == pytest.approx(2 * (1000 * 4 + 100 * 20) / 1e6) and c.spent == pytest.approx(call.cost)
    assert c.tokens["m"]["input_tokens"] == 2000 and c.tokens["m"]["output_tokens"] == 200


def test_template_config_loads():
    cfg = sa.load_config(HERE / "examples" / "template.toml")
    assert cfg.editable and [t.name for t in cfg.targets] == ["main"]


def test_path_map_points_generated_copies_at_sources(tmp_path):
    cfg = _cfg(tmp_path, path_map={"build/generated/": ""})
    r = mapfile.Routine("alpha", "_alpha", 0x6000, 16, "code_compiler", "build/generated/src/a.c", 12, "c")
    assert sa.source_path(cfg, "out.map", r).file == "src/a.c"
    assert sa.source_path(cfg, "out.map", mapfile.Routine("beta", "_beta", 0, 8, "code_user", "asm/x.asm", 1, "asm")).file == "asm/x.asm"


SDCC_MAP = textwrap.dedent(
    """\
    _foo                            = $7000 ; addr, local, , app_c, code_compiler, ../src/app.c:2130
    l_foo_00102                     = $7008 ; addr, local, , app_c, code_compiler, ../src/app.c:2140
    foo_asm_label                   = $700C ; addr, local, , app_c, code_compiler, ../src/app.c:2150
    _bar                            = $7020 ; addr, public, , app_c, code_compiler, ../src/app.c:2200
    __code_compiler_tail            = $7050 ; const, public, def, , ,
    """
)


def test_routines_sdcc_map_keeps_static_functions_and_skips_labels():
    rs = mapfile.routines(mapfile.parse_map_text(SDCC_MAP), ["code_compiler"])
    assert [(r.name, r.lang, r.size, r.file) for r in rs] == [
        ("bar", "c", 0x30, "../src/app.c"),
        ("foo", "c", 0x20, "../src/app.c"),
    ]


def test_source_path_resolves_map_relative_parent_dirs(tmp_path):
    cfg = _cfg(tmp_path, targets=[sa.Target("t", "", "build/out.map", "__data_compiler_tail", 0)])
    r = mapfile.Routine("foo", "_foo", 0, 8, "code_compiler", "../src/app.c", 1, "c")
    assert sa.source_path(cfg, "build/out.map", r).file == "src/app.c"
    escaped = mapfile.Routine("foo", "_foo", 0, 8, "code_compiler", "../../etc/x.c", 1, "c")
    assert sa.source_path(cfg, "build/out.map", escaped).file == "../../etc/x.c"


def test_definition_line_found_by_name_when_map_line_is_wrong(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.c").write_text(textwrap.dedent(
        """\
        static void about_open(void);  /* prototype */
        /* about_open( in a comment */
        static void run(void)
        {
            about_open();
        }
        static void about_open(void)
        {
            run();
        }
        """
    ))
    cfg = _cfg(tmp_path)
    r = mapfile.Routine("about_open", "_about_open", 0, 8, "code_compiler", "src/app.c", 2130, "c")
    assert sa.definition_line(cfg, tmp_path, r).line == 7
    assert "run();" in sa.excerpt(cfg, tmp_path, sa.definition_line(cfg, tmp_path, r), [])
    (src / "ovl.c").write_text("void apply(void) FASTCALL\n{\n}\n")
    (src / "gui.c").write_text("void apply(void);\n#include \"ovl.c\"\n")
    included = mapfile.Routine("apply", "_apply", 0, 8, "code_compiler", "src/gui.c", 99, "c")
    assert (sa.definition_line(cfg, tmp_path, included).file, sa.definition_line(cfg, tmp_path, included).line) == ("src/ovl.c", 1)


def test_project_python_overrides_interpreter(tmp_path):
    assert sa.python_for_shell(_cfg(tmp_path, python="/opt/py 3/bin/python")) == '"/opt/py 3/bin/python"'
    assert sa.python_for_shell(_cfg(tmp_path)).strip('"') == sys.executable.replace("\\", "/")


def test_root_defaults_to_config_directory(tmp_path):
    cfg = tmp_path / "shrink-agent.toml"
    cfg.write_text('[project]\neditable = ["src/*.c"]\n[[targets]]\nname = "t"\nbuild = "make"\nmap = "out.map"\n')
    loaded = sa.load_config(cfg)
    assert loaded.root == tmp_path.resolve() and loaded.name == tmp_path.name


def test_config_rejects_targets_without_map_or_files(tmp_path):
    cfg = tmp_path / "c.toml"
    cfg.write_text('[project]\neditable = ["src/*.c"]\n[[targets]]\nname = "t"\nbuild = "make"\n')
    with pytest.raises(SystemExit, match="exactly one of map or files"):
        sa.load_config(cfg)
    cfg.write_text('[project]\neditable = ["src/*.c"]\n[[targets]]\nname = "t"\nfiles = "*.OVL"\n')
    with pytest.raises(SystemExit, match="first target"):
        sa.load_config(cfg)


def test_files_target_measures_each_file_from_the_previous_build(tmp_path):
    wt = tmp_path / "wt"
    wt.mkdir()
    (wt / "build.py").write_text(
        "from pathlib import Path\n"
        "Path('out.map').write_text('__data_compiler_tail = $0010 ; const, public, def, , ,\\n')\n"
        "Path('A.OVL').write_bytes(b'x' * 7)\nPath('B.OVL').write_bytes(b'y' * 3)\n"
    )
    cfg = _cfg(wt, targets=[sa.Target("main", "{python} build.py", "out.map"), sa.Target("ovl", files="*.OVL")])
    res = sa.build_all(cfg, wt, tmp_path / "cache", sys.executable)
    assert {k: v.size for k, v in res.items()} == {"main": 16, "ovl/A.OVL": 7, "ovl/B.OVL": 3}
    assert sa.missing_targets(cfg, res) == []
    cfg = _cfg(wt, targets=[sa.Target("main", "{python} build.py", "out.map"), sa.Target("ovl", files="*.BIN")])
    res = sa.build_all(cfg, wt, tmp_path / "cache", sys.executable)
    assert not res["ovl"].ok and "no files match" in res["ovl"].error


def test_source_path_strips_parent_dirs_when_the_compiler_ran_elsewhere(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.c").write_text("int f(void)\n{\n}\n")
    r = mapfile.Routine("f", "_f", 0, 8, "code_compiler", "../src/a.c", 1, "c")
    assert sa.source_path(_cfg(tmp_path), "build/ovl/X/x.map", r, tmp_path).file == "src/a.c"


def test_maps_glob_adds_overlay_routines_keeping_the_largest(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.c").write_text("int foo(void)\n{\n}\nint bar(void)\n{\n}\n")
    main_map = tmp_path / "out.map"
    main_map.write_text("_foo = $6000 ; addr, public, , a_c, code_compiler, ../src/a.c:1\n"
                        "__code_compiler_tail = $6010 ; const, public, def, , ,\n")
    ovl = tmp_path / "build" / "ovl" / "X"
    ovl.mkdir(parents=True)
    (ovl / "x.map").write_text("_bar = $6800 ; addr, public, , a_c, code_compiler, ../src/a.c:4\n"
                               "_foo = $6820 ; addr, public, , a_c, code_compiler, ../src/a.c:1\n"
                               "__code_compiler_tail = $6834 ; const, public, def, , ,\n")
    cfg = _cfg(tmp_path, targets=[sa.Target("main", "x", "out.map"), sa.Target("ovl", files="build/*.OVL", maps="build/ovl/*/*.map")])
    rs = sa.primary_routines(cfg, {"main": sa.TargetResult(True, 0, map_path=main_map)}, tmp_path)
    assert [(r.name, r.size, r.file, r.line) for r in rs] == [("bar", 0x20, "src/a.c", 4), ("foo", 0x14, "src/a.c", 1)]
