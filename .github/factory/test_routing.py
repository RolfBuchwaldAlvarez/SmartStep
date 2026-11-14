"""Tests for routing.py. Run: python3 -m unittest discover -s .github/factory"""

import importlib.util
import json
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

    def test_each_untagged_finding_counts_as_major_next_to_tagged_ones(self):
        self.assertEqual(r.severity_of(["[minor] spelling", "Step count is lost on rotation"]), "major")

    def test_an_untagged_body_next_to_inline_comments_is_a_summary(self):
        self.assertEqual(r.review_findings("Round 1: two findings.", ["[minor] a", "[minor] b"]), ["[minor] a", "[minor] b"])
        self.assertEqual(r.review_findings("1. [major] x", ["[minor] a"]), ["[minor] a", "1. [major] x"])
        self.assertEqual(r.review_findings("Rotation loses the count.", []), ["Rotation loses the count."])


class Risk(unittest.TestCase):
    def test_risky_paths_and_size(self):
        self.assertEqual(r.risk_of(["app/src/main/java/a/Home.kt"]), "normal")
        for risky in ("app/build.gradle.kts", "gradle.properties", "gradle/libs.versions.toml",
                      "gradle/wrapper/gradle-wrapper.properties",
                      "app/schemas/x/1.json", "app/src/main/AndroidManifest.xml", ".github/workflows/ci.yml",
                      "app/src/main/java/a/auth/Token.kt", "app/src/main/java/a/AuthInterceptor.kt",
                      "app/src/main/java/a/AuthorizationHeader.kt", "app/src/main/java/a/SecurityConfig.kt"):
            self.assertEqual(r.risk_of([risky]), "high", risky)
        for plain in ("app/src/main/java/com/example/data/AuthorsDao.kt", "app/src/test/java/a/ui/AuthorRowTest.kt"):
            self.assertEqual(r.risk_of([plain]), "normal", plain)
        self.assertEqual(r.risk_of([f"app/src/F{i}.kt" for i in range(21)]), "high")


CONDUCTOR = {"login": "github-actions[bot]"}


class State(unittest.TestCase):
    def test_round_trip(self):
        state = {"floor": 8, "head": A, "levels": {A: 5}, "next_level": None, "signaled": [A]}
        cid, read = r.read_state([{"id": 1, "body": "other", "user": CONDUCTOR},
                                  {"id": 7, "body": r.render_state(state), "user": CONDUCTOR}])
        self.assertEqual((cid, read), (7, state))
        self.assertEqual(r.read_state([{"id": 1, "body": "hi", "user": CONDUCTOR}]), (None, {}))

    def test_only_a_valid_state_by_the_conductor_counts(self):
        state = {"floor": 0, "head": A, "levels": {}, "next_level": None, "signaled": []}
        forged = r.render_state(dict(state, floor=13))
        self.assertEqual(r.read_state([{"id": 1, "body": forged, "user": {"login": "someone"}},
                                       {"id": 2, "body": "<!-- factory-state [] -->", "user": CONDUCTOR},
                                       {"id": 3, "body": r.render_state(dict(state, floor="13")), "user": CONDUCTOR}]),
                         (None, {}))
        self.assertEqual(r.read_state([{"id": 2, "body": "<!-- factory-state [] -->", "user": CONDUCTOR},
                                       {"id": 4, "body": r.render_state(state), "user": CONDUCTOR}]), (4, state))

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


class PlanningPoker(unittest.TestCase):
    def test_ticket_findings(self):
        self.assertIsNone(r.findings_of("Estimate: 5 – three layers"))           # the part is missing
        self.assertEqual(r.findings_of("Estimate: 5 – x\n**Ticket findings:** none"), [])
        body = ("Estimate: 5 – x\nTicket findings:\n- `UNCLEAR`: 'sync' means push or pull\n"
                "2. **SCOPE_TOO_BROAD** – split the widget\n- UNCLEAR\n- MISSING_DEPENDENCY:\n- a remark")
        self.assertEqual(r.findings_of(body), [("UNCLEAR", "'sync' means push or pull"),
                                               ("SCOPE_TOO_BROAD", "split the widget")])
        # Findings without a detail do not count.
        self.assertEqual(r.findings_of("Estimate: 5 – x\nTicket findings:\n- UNCLEAR"), [])
        # A quoted part is not one's own.
        self.assertIsNone(r.findings_of("Estimate: 5 – x\n> Ticket findings: none"))

    def test_a_longer_word_is_not_a_finding_category(self):
        body = ("Estimate: 5 – x\nTicket findings:\n- UNCLEARED: the criterion is vague\n"
                "- CONTRADICTS_SPECIFICATION: quoted\n- `UNCLEAR_X`: y\n- `UNCLEAR`: 'sync' means push or pull")
        self.assertEqual(r.findings_of(body), [("UNCLEAR", "'sync' means push or pull")])

    def test_revised_comments(self):
        self.assertTrue(r.revised("Revised: 1. fixed in the body"))
        self.assertTrue(r.revised("**Revised:** all three"))
        self.assertFalse(r.revised("> Revised: quoted"))
        self.assertFalse(r.revised("I revised the ticket"))

    def test_estimate_comments(self):
        self.assertEqual(r.estimate_of("Estimate: 5 – three layers"), 5)
        self.assertEqual(r.estimate_of("**Estimate:** 8 – cross-cutting"), 8)   # bold is fine
        self.assertEqual(r.estimate_of("Estimate: 4"), None)              # not a Fibonacci value
        self.assertEqual(r.estimate_of("I estimate 5"), None)
        # Quoting or restating another estimator's vote is not a vote of one's own.
        self.assertEqual(r.estimate_of("> Estimate: 5 – quoting Claude\nI have not estimated this yet."), None)
        self.assertEqual(r.estimate_of("## Estimate: 5"), None)

    def test_poker(self):
        self.assertEqual(r.poker({"a": 3, "b": None}), ("open", None))
        self.assertEqual(r.poker({"a": 3, "b": 5}), ("agree", 5))
        self.assertEqual(r.poker({"a": 3, "b": 8}), ("differ", None))
        self.assertEqual(r.poker({"a": 13, "b": 21}), ("agree", 21))


class Signals(unittest.TestCase):
    def timeout(self, **changes):
        event = {"version": 1, "kind": "fix", "head": A, "level": 3, "run_id": "a" * 32}
        actor = changes.pop("actor", "codex-bot-rba[bot]")
        event.update(changes)
        return {"user": {"login": actor}, "body": r.TIMEOUT_MARK + json.dumps(event) + " -->\nTimed out."}

    def test_timeout_is_idempotent_and_uses_the_failed_run_level(self):
        note = self.timeout()
        self.assertEqual(r.timeout_floor([note, note], A, "codex-bot-rba[bot]"), 5)
        # Another attempt on the unchanged head at its raised level can raise again.
        self.assertEqual(r.timeout_floor([note, self.timeout(level=5)], A, "codex-bot-rba[bot]"), 8)

    def test_wrong_heads_roles_actors_and_malformed_evidence_are_ignored(self):
        for changes in ({"head": B}, {"actor": "someone"}, {"actor": "hermes-bot-rba[bot]"},
                        {"kind": "estimate"}, {"kind": "implement"}, {"run_id": "bad"},
                        {"version": True}, {"version": 2}, {"level": True}, {"level": 4},
                        {"level": [5]}, {"level": "5"}):
            with self.subTest(changes=changes):
                self.assertEqual(r.timeout_floor([self.timeout(**changes)], A, "codex-bot-rba[bot]"), 0)
        for body in (r.TIMEOUT_MARK + "not-json -->", r.TIMEOUT_MARK + "[] -->", "x" * 5000,
                     r.TIMEOUT_MARK + "[" * 1100 + " -->"):
            note = {"user": {"login": "codex-bot-rba[bot]"}, "body": body}
            self.assertEqual(r.timeout_floor([note], A, "codex-bot-rba[bot]"), 0)

    def test_reviewer_timeout_uses_producing_level_and_only_eligible_judges(self):
        note = self.timeout(kind="review", actor="hermes-bot-rba[bot]", level=None)
        self.assertEqual(r.timeout_floor([note], A, "codex-bot-rba[bot]", ["hermes-bot-rba[bot]"], 5), 8)
        self.assertEqual(r.timeout_floor([note], A, "codex-bot-rba[bot]", [], 5), 0)
        self.assertEqual(r.timeout_floor([self.timeout(kind="review", actor="hermes-bot-rba[bot]", level=3)],
                                        A, "codex-bot-rba[bot]", ["hermes-bot-rba[bot]"], 5), 0)
        for kind in ("proofread", "update"):
            self.assertEqual(r.timeout_floor([self.timeout(kind=kind, level=3)], A, "codex-bot-rba[bot]",
                                            produced_level=5), 0)
        self.assertEqual(r.timeout_floor([self.timeout(level=None)], A, "codex-bot-rba[bot]",
                                        produced_level=5), 0)

    def test_ticket_timeout_requires_assigned_implementer_and_run_level(self):
        note = self.timeout(kind="implement", head="ticket", level=8)
        self.assertEqual(r.timeout_floor([note], "ticket", "codex-bot-rba[bot]"), 13)
        self.assertEqual(r.timeout_floor([note], "ticket", "claude-bot-rba[bot]"), 0)
        self.assertEqual(r.timeout_floor([self.timeout(kind="implement", head="ticket", level=None)],
                                        "ticket", "codex-bot-rba[bot]", produced_level=8), 0)

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
