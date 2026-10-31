"""Tests for routing.py. Run: python3 -m unittest discover -s .github/factory"""

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("routing", HERE / "routing.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

A, B, C = "a" * 40, "b" * 40, "c" * 40


def rv(state, commit, body="Round: findings."):
    return {"state": state, "commit_id": commit, "body": body}


class Points(unittest.TestCase):
    def test_steps(self):
        self.assertEqual([r.next_step(n) for n in (1, 2, 3, 5, 8, 13, 21)], [2, 3, 5, 8, 13, 21, 34])
        self.assertEqual([r.step_below(n) for n in (2, 3, 5, 8)], [2, 2, 3, 5])     # never below level 2

    def test_fix_level_table(self):
        self.assertEqual(r.fix_level(8, "minor"), 2)
        self.assertEqual(r.fix_level(8, "major"), 5)
        self.assertEqual(r.fix_level(3, "major"), 2)
        self.assertEqual(r.fix_level(5, "critical"), 5)
        self.assertEqual(r.fix_level(8, "major", floor=13), 13)


class Severity(unittest.TestCase):
    def test_highest_tag_wins_and_untagged_counts_as_major(self):
        self.assertEqual(r.severity_of(["[minor] naming", "[Critical] data loss"]), "critical")
        self.assertEqual(r.severity_of(["[minor] a test", "[non-blocking] wording"]), "minor")
        self.assertEqual(r.severity_of(["[P3] nit"]), "minor")
        self.assertEqual(r.severity_of(["[P2] select the newest run"]), "major")
        self.assertEqual(r.severity_of(["no tag at all"]), "major")
        self.assertEqual(r.severity_of([]), "major")


class Risk(unittest.TestCase):
    def test_risky_paths_and_size(self):
        self.assertEqual(r.risk_of(["app/src/main/java/a/Home.kt"]), "normal")
        for risky in ("app/build.gradle.kts", "gradle.properties", "gradle/libs.versions.toml",
                      "gradle/wrapper/gradle-wrapper.properties",
                      "app/schemas/x/1.json", "app/src/main/AndroidManifest.xml", ".github/workflows/ci.yml",
                      "app/src/main/java/a/auth/Token.kt"):
            self.assertEqual(r.risk_of([risky]), "high", risky)
        self.assertEqual(r.risk_of([f"app/src/F{i}.kt" for i in range(21)]), "high")


class State(unittest.TestCase):
    def test_round_trip(self):
        state = {"floor": 8, "head": A, "levels": {A: 5}, "next_level": None, "signaled": [A]}
        cid, read = r.read_state([{"id": 1, "body": "other"}, {"id": 7, "body": r.render_state(state)}])
        self.assertEqual((cid, read), (7, state))
        self.assertEqual(r.read_state([{"id": 1, "body": "hi"}]), (None, {}))

    def test_floor_rises_once_per_head_from_the_level_that_produced_it(self):
        s = r.advance({}, 8, A, False)                       # the implementation, at the ticket's 8
        s["next_level"] = 5                                  # a major fix round is due
        s = r.advance(s, 8, B, True)                         # it produced B, and B shows a signal
        self.assertEqual((s["levels"][B], s["floor"]), (5, 8))
        self.assertEqual(r.advance(s, 8, B, True)["floor"], 8)   # re-running changes nothing
        s["next_level"] = 8
        s = r.advance(s, 8, C, True)
        self.assertEqual(s["floor"], 13)                     # then split

    def test_a_base_update_is_no_fix_round(self):
        s = r.advance({}, 5, A, False)
        s["next_level"] = 3
        s = r.advance(s, 5, B, False)                        # the fix round
        s = r.advance(s, 5, C, False)                        # a base update afterwards
        self.assertIn(B, s["levels"])
        self.assertNotIn(C, s["levels"])


class Signals(unittest.TestCase):
    def test_same_judge_rejects_twice(self):
        twice = {"hermes": [rv("COMMENTED", A), rv("COMMENTED", B)]}
        self.assertTrue(r.signal_at(B, "green", twice, False, True))
        once = {"hermes": [rv("APPROVED", A), rv("COMMENTED", B)]}
        self.assertFalse(r.signal_at(B, "green", once, False, True))

    def test_ci_red_again_only_after_a_fix_round(self):
        self.assertTrue(r.signal_at(B, "red", {}, False, True))
        self.assertFalse(r.signal_at(A, "red", {}, False, False))

    def test_underestimated_counts_with_the_next_failure(self):
        rejected = {"claude": [rv("COMMENTED", A)]}
        self.assertTrue(r.signal_at(A, "green", rejected, True, False))
        self.assertTrue(r.signal_at(A, "red", {}, True, False))
        self.assertFalse(r.signal_at(A, "green", {}, True, False))


if __name__ == "__main__":
    unittest.main()
