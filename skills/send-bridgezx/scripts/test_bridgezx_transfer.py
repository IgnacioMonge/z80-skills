#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


SCRIPT = Path(__file__).with_name("bridgezx_transfer.py")
SPEC = importlib.util.spec_from_file_location("bridgezx_transfer", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class Result:
    def __init__(
        self,
        *,
        ok: bool = True,
        message: str = "sent",
        outcome_unknown: bool = False,
    ) -> None:
        self.ok = ok
        self.message = message
        self.outcome_unknown = outcome_unknown


class Probe:
    def __init__(
        self,
        status: str = "ready",
        target: str = "next",
        message: str = "Ready",
        version: str = "1.1.2",
    ) -> None:
        self.status = status
        self.target = target
        self.message = message
        self.version = version


def arguments(sources: list[str], **overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "sources": sources,
        "client_root": None,
        "ip": None,
        "port": None,
        "target": None,
        "destination": None,
        "ordered": False,
        "quiet": True,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def fake_api(**overrides: object) -> MODULE.BridgeZXAPI:
    values: dict[str, object] = {
        "default_port": 6144,
        "ready_status": "ready",
        "load_config": Mock(
            return_value={"last_ip": "192.0.2.10", "ip_history": ["192.0.2.9"]}
        ),
        "remember_ip": Mock(),
        "probe": Mock(return_value=Probe()),
        "send_queue": Mock(return_value=Result()),
        "build_remote_path_map": Mock(return_value=[]),
        "progress": Mock(),
        "finish_progress": Mock(),
    }
    values.update(overrides)
    return MODULE.BridgeZXAPI(**values)


class BridgeZXTransferTest(unittest.TestCase):
    def test_last_ip_destination_and_detected_target_reach_one_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "one.tap"
            second = Path(tmp) / "two.tap"
            first.write_bytes(b"1")
            second.write_bytes(b"2")
            api = fake_api()

            with patch("sys.stdout", new_callable=io.StringIO):
                code = MODULE.run(
                    arguments(
                        [str(first), str(second)], destination="GAMES/ARCADE"
                    ),
                    api,
                )

        self.assertEqual(code, 0)
        api.probe.assert_called_once_with("192.0.2.10", port=6144)
        api.remember_ip.assert_called_once_with("192.0.2.10")
        sent = api.send_queue.call_args
        self.assertEqual(sent.args[0], "192.0.2.10")
        self.assertEqual(sent.args[1], [str(first.resolve()), str(second.resolve())])
        self.assertEqual(sent.kwargs["destination"], "GAMES/ARCADE")
        self.assertEqual(sent.kwargs["target"], "next")
        self.assertEqual(sent.kwargs["expected_target"], "next")

    def test_explicit_ip_wins_and_ordered_sends_stop_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sources = [
                Path(tmp) / name
                for name in ("first.tap", "second.tap", "third.tap")
            ]
            for source in sources:
                source.write_bytes(b"x")
            send = Mock(
                side_effect=(
                    Result(message="first sent"),
                    Result(ok=False, message="second failed"),
                )
            )
            api = fake_api(send_queue=send)

            with (
                patch("sys.stdout", new_callable=io.StringIO),
                patch("sys.stderr", new_callable=io.StringIO) as errors,
            ):
                code = MODULE.run(
                    arguments(
                        [str(path) for path in sources],
                        ip="192.0.2.44",
                        ordered=True,
                    ),
                    api,
                )

        self.assertEqual(code, MODULE.EXIT_ERROR)
        self.assertEqual(send.call_count, 2)
        self.assertEqual(
            [entry.args[1] for entry in send.call_args_list],
            [[str(sources[0].resolve())], [str(sources[1].resolve())]],
        )
        self.assertIn("stopped after 1 of 3", errors.getvalue())

    def test_requested_target_mismatch_blocks_all_network_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "game.nex"
            source.write_bytes(b"nex")
            api = fake_api()

            with patch("sys.stderr", new_callable=io.StringIO) as errors:
                code = MODULE.run(arguments([str(source)], target="classic"), api)

        self.assertEqual(code, MODULE.EXIT_ERROR)
        api.send_queue.assert_not_called()
        api.remember_ip.assert_not_called()
        self.assertIn("requested classic", errors.getvalue())
        self.assertIn("detected next", errors.getvalue())

    def test_uncertain_result_is_not_retried(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "game.tap"
            source.write_bytes(b"tap")
            send = Mock(
                return_value=Result(
                    ok=False,
                    message="remote acknowledgement lost",
                    outcome_unknown=True,
                )
            )
            api = fake_api(send_queue=send)

            with (
                patch("sys.stdout", new_callable=io.StringIO),
                patch("sys.stderr", new_callable=io.StringIO) as errors,
            ):
                code = MODULE.run(arguments([str(source)]), api)

        self.assertEqual(code, MODULE.EXIT_UNCERTAIN)
        send.assert_called_once()
        self.assertIn("uncertain", errors.getvalue())

    def test_all_sources_are_planned_before_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "bad.tap"
            source.write_bytes(b"tap")
            events: list[str] = []
            planner = Mock(side_effect=lambda _paths: events.append("plan"))

            def probe(*_args: object, **_kwargs: object) -> Probe:
                events.append("probe")
                return Probe()

            api = fake_api(build_remote_path_map=planner, probe=Mock(side_effect=probe))

            with patch("sys.stdout", new_callable=io.StringIO):
                code = MODULE.run(arguments([str(source)]), api)

        self.assertEqual(code, 0)
        self.assertEqual(events, ["plan", "probe"])

    def test_interrupted_preparation_stops_before_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "game.tap"
            source.write_bytes(b"tap")
            api = fake_api(build_remote_path_map=Mock(side_effect=KeyboardInterrupt))

            with patch("sys.stderr", new_callable=io.StringIO) as errors:
                code = MODULE.run(arguments([str(source)]), api)

        self.assertEqual(code, MODULE.EXIT_INTERRUPTED)
        api.probe.assert_not_called()
        api.send_queue.assert_not_called()
        self.assertIn("preparation cancelled", errors.getvalue())

    def test_missing_history_is_a_usage_error(self) -> None:
        api = fake_api(load_config=Mock(return_value={}))
        with self.assertRaisesRegex(MODULE.UsageError, "no IP"):
            MODULE._selected_ip(None, api)


if __name__ == "__main__":
    unittest.main()
