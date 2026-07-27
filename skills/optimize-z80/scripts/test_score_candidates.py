import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("score_candidates.py")
spec = importlib.util.spec_from_file_location("score_candidates", MODULE)
score_candidates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score_candidates)


def candidate(**overrides):
    data = {
        "lane": "SAFE",
        "confidence": "LIKELY",
        "evidence": "map shows symbol",
        "targets": ["all"],
        "bytes": 1,
        "speed": 1,
        "ram": 1,
        "ux": 1,
        "simplicity": 1,
        "validation": 1,
        "low_risk": 1,
        "reversible": 1,
    }
    data.update(overrides)
    return data


class ScoreCandidatesTest(unittest.TestCase):
    @unittest.skipIf(score_candidates.tomllib is None, "tomllib requires Python 3.11+")
    def test_policy_file_vetoes_forbidden_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy = Path(tmp) / "z80opt.toml"
            policy.write_text(
                'target = "zx-spectrum"\n\n[forbidden]\nsmc = true\n',
                encoding="utf-8",
            )
            policy_data = score_candidates.load_policy_data(policy)
            forbidden = score_candidates.load_forbidden(policy_data, None)
            target = score_candidates.load_target(policy_data, None)
            c = candidate(tags=["smc"], targets=["zx-spectrum"])
            self.assertEqual(
                score_candidates.score(c, "balanced", forbidden, target), -999
            )
            self.assertIn("forbidden tags: smc", c["policy_veto"])

    def test_policy_file_without_tomllib_fails_loud(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy = Path(tmp) / "z80opt.toml"
            policy.write_text('target = "cpm"\n', encoding="utf-8")
            old_tomllib = score_candidates.tomllib
            score_candidates.tomllib = None
            try:
                with self.assertRaises(SystemExit):
                    score_candidates.load_policy_data(policy)
            finally:
                score_candidates.tomllib = old_tomllib

    def test_dangerous_without_known_tags_is_rejected(self):
        c = candidate(lane="DANGEROUS", tags=[])
        self.assertEqual(score_candidates.score(c, "balanced", set(), ""), -999)
        self.assertIn("DANGEROUS", c["schema_error"])

    def test_invalid_numeric_field_is_rejected(self):
        c = candidate(low_risk=True)
        self.assertEqual(score_candidates.score(c, "balanced", set(), ""), -999)
        self.assertEqual(c["schema_error"], "low_risk must be an integer")

    def test_tags_and_targets_must_be_lists(self):
        c = candidate(tags="smc")
        self.assertEqual(score_candidates.score(c, "balanced", set(), ""), -999)
        self.assertEqual(c["schema_error"], "tags must be a list")

    def test_overlay_overflow_is_rejected(self):
        c = candidate(category="overlay/banking", overlay_after=2050)
        self.assertEqual(
            score_candidates.score(c, "balanced", set(), "", {"overlay_size": 2048}),
            -999,
        )
        self.assertIn("overlay_after 2050", c["policy_veto"])

    def test_overlay_overflow_rejected_without_textual_overlay_hint(self):
        # A candidate that declares overlay_after must face the size veto even
        # when no category/zone/tag mentions "overlay" or "bank".
        c = candidate(overlay_after=2100)
        self.assertEqual(
            score_candidates.score(c, "balanced", set(), "", {"overlay_size": 2048}),
            -999,
        )
        self.assertIn("overlay_after 2100", c["policy_veto"])

    def test_overlay_candidate_without_size_evidence_is_speculative(self):
        c = candidate(category="overlay/banking", confidence="LIKELY")
        self.assertGreater(
            score_candidates.score(c, "balanced", set(), "", {"overlay_size": 2048}),
            -999,
        )
        self.assertEqual(c["confidence"], "SPECULATIVE")
        self.assertIn("missing overlay_after", c["evidence_gate"])

    def test_unknown_target_rejects_hardware_specific_and_missing_targets(self):
        hardware = candidate(targets=["zx-spectrum"])
        missing = candidate(targets=[])
        self.assertEqual(
            score_candidates.score(hardware, "balanced", set(), "unknown"), -999
        )
        self.assertIn("hardware-specific", hardware["policy_veto"])
        self.assertEqual(
            score_candidates.score(missing, "balanced", set(), "zx-spectrum"), -999
        )
        self.assertIn("missing targets", missing["policy_veto"])

    def test_proven_requires_current_structured_evidence(self):
        prose = candidate(confidence="PROVEN", evidence="trust me")
        current = candidate(
            confidence="PROVEN",
            evidence=[
                {
                    "kind": "measurement",
                    "ref": "build/run-17.json",
                    "current": True,
                }
            ],
        )
        score_candidates.score(prose, "balanced", set(), "")
        score_candidates.score(current, "balanced", set(), "")
        self.assertEqual(prose["confidence"], "LIKELY")
        self.assertIn("structured evidence", prose["evidence_gate"])
        self.assertEqual(current["confidence"], "PROVEN")


if __name__ == "__main__":
    unittest.main()
