"""Tests for conductor.py. Run: python3 -m unittest discover -s .github/factory"""

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("conductor", HERE / "conductor.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

HEAD, OLD = "h" * 40, "o" * 40
OPENED = "2027-01-15T08:00:00Z"
NOW = 1_800_000_000.0 + 7200                  # two hours after OPENED
CONFIG = c.load_config(HERE.parent / "factory.yml")


def pr(author="codex", **extra):
    login = "RolfBuchwaldAlvarez" if author == "owner" else f"{author}-bot-rba[bot]"
    base = {"number": 9, "user": {"login": login}, "head": {"sha": HEAD}, "draft": False,
            "created_at": OPENED, "mergeable_state": "clean", "body": "Closes #5"}
    base.update(extra)
    return base


def review(agent, state="COMMENTED", commit=HEAD, body="Round 1: findings."):
    return {"user": {"login": f"{agent}-bot-rba[bot]"}, "state": state, "commit_id": commit, "body": body}


PROOFREAD = review("codex", body="Proofread: no findings.", commit=OLD)
P3 = frozenset({"points:3"})


class Config(unittest.TestCase):
    def test_factory_yml(self):
        self.assertEqual(CONFIG, {"implementers": ["codex", "claude"], "judges": ["claude", "hermes", "codex"],
                                  "judges_per_pr": 2, "max_rounds": 3, "required_checks": ["android-ci"]})

    def test_former_single_implementer_key(self):
        path = HERE / "_legacy.yml"
        try:
            path.write_text("implementer: codex\njudges: claude, hermes\n")
            self.assertEqual(c.load_config(path)["implementers"], ["codex"])
        finally:
            path.unlink()


class Judges(unittest.TestCase):
    def test_nobody_judges_their_own_pr_and_there_are_always_two(self):
        self.assertEqual(c.judges_for("codex", CONFIG), ["claude", "hermes"])
        self.assertEqual(c.judges_for("claude", CONFIG), ["hermes", "codex"])
        self.assertEqual(c.judges_for("owner", CONFIG), ["claude", "hermes"])
        self.assertEqual(c.judges_for("hermes", CONFIG), ["claude", "codex"])


class Ticket(unittest.TestCase):
    def test_implement_until_a_pr_exists(self):
        self.assertEqual(c.ticket_labels(False, CONFIG, P3), {"next:implement:codex", "level:3"})
        self.assertEqual(c.ticket_labels(True, CONFIG, P3), set())

    def test_implementer_label_picks_another_implementer(self):
        self.assertEqual(c.ticket_labels(False, CONFIG, P3 | {"implementer:claude"}),
                         {"next:implement:claude", "level:3"})
        self.assertEqual(c.ticket_labels(False, CONFIG, P3 | {"implementer:owner"}), set())

    def test_unknown_or_ambiguous_implementer_falls_back_to_the_default(self):
        self.assertEqual(c.ticket_labels(False, CONFIG, P3 | {"implementer:hermes"}),
                         {"next:implement:codex", "level:3"})
        both = P3 | {"implementer:claude", "implementer:codex"}
        self.assertEqual(c.ticket_labels(False, CONFIG, both), {"next:implement:codex", "level:3"})

    def test_points_decide_whether_and_at_which_level(self):
        self.assertEqual(c.ticket_labels(False, CONFIG), {"needs:points"})
        self.assertEqual(c.ticket_labels(False, CONFIG, frozenset({"points:4"})), {"needs:points"})   # not Fibonacci
        self.assertEqual(c.ticket_labels(False, CONFIG, frozenset({"points:8"})), {"next:implement:codex", "level:8"})
        self.assertEqual(c.ticket_labels(False, CONFIG, frozenset({"points:13"})), {"next:split:codex", "level:13"})
        self.assertEqual(c.ticket_labels(False, CONFIG, frozenset({"points:21", "implementer:claude"})),
                         {"next:split:claude", "level:21"})
        self.assertEqual(c.ticket_labels(False, CONFIG, frozenset({"points:21", "split:done"})), set())
        self.assertEqual(c.ticket_labels(False, CONFIG, frozenset({"points:13", "implementer:owner"})), set())
        self.assertEqual(c.ticket_labels(False, CONFIG, frozenset({"points:3", "points:5"})), {"needs:points"})


class Routed(unittest.TestCase):
    def test_fix_level_follows_severity_and_floor(self):
        fix = {"next:fix:codex", "next:judge:hermes"}
        self.assertIn("level:2", c.routed(fix, 8, 0, "minor", "normal"))
        self.assertIn("level:5", c.routed(fix, 8, 0, "major", "normal"))
        self.assertIn("level:8", c.routed(fix, 8, 0, "critical", "normal"))
        self.assertIn("level:8", c.routed(fix, 8, 8, "minor", "normal"))           # the floor wins
        self.assertEqual(c.routed(fix, 8, 13, "minor", "normal"), {"needs:split"})

    def test_a_ticket_of_13_points_stops_its_open_pr_too(self):
        self.assertEqual(c.routed({"next:fix:codex", "next:judge:hermes"}, 13, 0, "major", "normal"), {"needs:split"})
        self.assertEqual(c.routed(set(), 13, 0, "major", "normal"), {"needs:split"})

    def test_needs_owner_stays_ahead_of_the_split(self):
        self.assertEqual(c.routed({"needs:owner"}, 8, 13, "major", "normal"), {"needs:owner"})
        self.assertEqual(c.routed({"needs:owner"}, 13, 0, "major", "normal"), {"needs:owner"})

    def test_risk_only_with_judges_and_no_level_without_points(self):
        self.assertEqual(c.routed({"next:judge:claude"}, None, 0, "major", "high"), {"next:judge:claude", "risk:high"})
        self.assertEqual(c.routed({"next:merge:codex"}, 5, 0, "major", "high"), {"next:merge:codex"})
        self.assertEqual(c.routed({"next:fix:codex"}, None, 0, "critical", "normal"), {"next:fix:codex"})

    def test_linked_ticket(self):
        self.assertEqual(c.linked_ticket({"body": "Closes #5\n\nMore."}), 5)
        self.assertEqual(c.linked_ticket({"body": "fixes #12"}), 12)
        self.assertIsNone(c.linked_ticket({"body": "Relates to #5"}))
        self.assertIsNone(c.linked_ticket({"body": None}))

    def test_acceptance_until_accepted(self):
        self.assertEqual(c.acceptance_labels({"factory:ready"}), {"step:acceptance"})
        self.assertEqual(c.acceptance_labels({"factory:ready", "accepted"}), set())


class PullRequest(unittest.TestCase):
    def labels(self, reviews, checks="green", **extra):
        return c.pr_labels(pr(**extra), reviews, checks, NOW, CONFIG)

    def test_proofread_first(self):
        self.assertEqual(c.pr_labels(pr(), [], "green", 1_800_000_000.0 + 60, CONFIG), {"next:proofread:codex"})

    def test_judges_after_proofread_or_an_hour(self):
        self.assertEqual(self.labels([PROOFREAD]), {"next:judge:claude", "next:judge:hermes"})
        self.assertEqual(self.labels([]), {"next:judge:claude", "next:judge:hermes"})

    def test_one_judgement_missing(self):
        self.assertEqual(self.labels([PROOFREAD, review("claude", "APPROVED")]), {"next:judge:hermes"})

    def test_fix_when_both_judged_and_not_both_approve(self):
        got = self.labels([PROOFREAD, review("claude", "APPROVED"), review("hermes")])
        self.assertEqual(got, {"next:fix:codex", "next:judge:hermes"})

    def test_merge_when_both_approve_and_ci_green(self):
        reviews = [PROOFREAD, review("claude", "APPROVED"), review("hermes", "APPROVED")]
        self.assertEqual(self.labels(reviews), {"next:merge:codex"})
        self.assertEqual(self.labels(reviews, checks="pending"), set())
        self.assertEqual(self.labels(reviews, checks="red"), {"next:fix:codex"})

    def test_red_ci_waits_for_both_judgements_before_a_fix(self):
        self.assertEqual(self.labels([PROOFREAD], checks="red"), {"next:judge:claude", "next:judge:hermes"})
        self.assertEqual(self.labels([PROOFREAD, review("claude", "APPROVED")], checks="red"), {"next:judge:hermes"})

    def test_a_comment_keeps_an_approval_and_a_stale_approval_does_not_count(self):
        keep = [PROOFREAD, review("claude", "APPROVED"), review("hermes", "APPROVED"), review("hermes", body="note")]
        self.assertEqual(self.labels(keep), {"next:merge:codex"})
        stale = [PROOFREAD, review("claude", "APPROVED", commit=OLD), review("hermes", "APPROVED")]
        self.assertEqual(self.labels(stale), {"next:judge:claude"})

    def test_thread_replies_are_no_judgements(self):
        self.assertEqual(self.labels([PROOFREAD, review("claude", body="")]), {"next:judge:claude", "next:judge:hermes"})

    def test_round_limit_needs_the_owner(self):
        rounds = [review("hermes", commit=x) for x in ("a" * 40, "b" * 40, HEAD)]
        self.assertEqual(self.labels([PROOFREAD, review("claude", "APPROVED")] + rounds), {"needs:owner"})

    def test_conflict_update_first(self):
        self.assertEqual(self.labels([PROOFREAD], mergeable_state="dirty"), {"next:update:codex"})

    def test_drafts_and_strangers_get_nothing(self):
        self.assertEqual(self.labels([PROOFREAD], draft=True), set())
        self.assertEqual(c.pr_labels(dict(pr(), user={"login": "someone"}), [], "green", NOW, CONFIG), set())

    def test_claude_as_implementer_is_judged_by_hermes_and_codex(self):
        proofread = review("claude", body="Proofread: no findings.", commit=OLD)
        self.assertEqual(self.labels([proofread], author="claude"), {"next:judge:hermes", "next:judge:codex"})
        approved = [proofread, review("hermes", "APPROVED"), review("codex", "APPROVED")]
        self.assertEqual(self.labels(approved, author="claude"), {"next:merge:claude"})

    def test_owner_prs_get_judges_only(self):
        early = c.pr_labels(pr(author="owner"), [], "green", 1_800_000_000.0 + 60, CONFIG)
        self.assertEqual(early, {"next:judge:claude", "next:judge:hermes"})        # no proofread
        self.assertEqual(self.labels([], author="owner", mergeable_state="dirty"),
                         {"next:judge:claude", "next:judge:hermes"})                # he updates himself
        judged = [review("claude", "APPROVED"), review("hermes")]
        self.assertEqual(self.labels(judged, author="owner"), {"next:judge:hermes"})  # he fixes himself
        approved = [review("claude", "APPROVED"), review("hermes", "APPROVED")]
        self.assertEqual(self.labels(approved, author="owner"), set())             # he merges himself

    def test_the_conductors_own_job_is_no_ci(self):
        green = {"name": "build", "status": "completed", "conclusion": "success"}
        for own in ({"status": "in_progress"}, {"status": "completed", "conclusion": "failure"},
                    {"status": "completed", "conclusion": "cancelled"}):
            self.assertEqual(c.checks_state([green, dict(own, name="conduct")]), "green")

    def test_required_checks(self):
        ok = {"id": 101, "name": "android-ci", "status": "completed", "conclusion": "success",
              "started_at": "2027-01-15T09:00:00Z"}
        old_red = dict(ok, id=100, conclusion="failure", started_at="2027-01-15T08:00:00Z")
        other_red = {"name": "factory-tests", "status": "completed", "conclusion": "failure"}
        self.assertEqual(c.checks_state([], ["android-ci"]), "pending")              # CI did not run: never green
        self.assertEqual(c.checks_state([old_red, ok], ["android-ci"]), "green")     # the latest run counts
        self.assertEqual(c.checks_state([ok, other_red], ["android-ci"]), "green")   # only the required ones
        self.assertEqual(c.checks_state([old_red], ["android-ci"]), "red")
        queued = {"id": 102, "name": "android-ci", "status": "queued", "started_at": None}
        for runs in ([ok, queued], [queued, ok]):                                  # a newer run not started yet
            self.assertEqual(c.checks_state(runs, ["android-ci"]), "pending")

    def test_checks_state(self):
        self.assertEqual(c.checks_state([]), "green")
        self.assertEqual(c.checks_state([{"status": "completed", "conclusion": "success"}]), "green")
        self.assertEqual(c.checks_state([{"status": "in_progress"}]), "pending")
        self.assertEqual(c.checks_state([{"status": "completed", "conclusion": "failure"}]), "red")


def state_comment(state=None, body=None):
    return {"id": 4, "user": {"login": "github-actions[bot]"}, "body": body or c.routing.render_state(state)}


def stored(bodies):
    return c.routing.read_state([state_comment(body=b) for b in bodies])[1]


class FakeGitHub:
    def __init__(self, labels=(), lists=None, prs=None):
        self.calls, self.labels = [], set(labels)
        self.lists, self.prs = lists or {}, prs or {}

    def call(self, method, path, body=None):
        if method == "GET":
            return self.prs[int(path.rsplit("/", 1)[1])]
        self.calls.append((method, path, body))

    def all(self, path):
        return self.lists.get(path, [])


def item(number, *labels, **extra):
    return dict({"number": number, "labels": [{"name": n} for n in labels]}, **extra)


def lists(open_ready=(), open_all=(), closed_ready=(), open_prs=(), closed_prs=()):
    return {"/issues?state=open&labels=factory:ready": list(open_ready), "/issues?state=open": list(open_all),
            "/issues?state=all&labels=factory:ready": list(open_ready) + list(closed_ready),
            "/issues?state=closed&labels=factory:ready": list(closed_ready),
            "/pulls?state=open": list(open_prs), "/pulls?state=closed": list(closed_prs)}


class Sync(unittest.TestCase):
    def test_adds_missing_removes_stale_keeps_others(self):
        gh = FakeGitHub()
        c.sync_labels(gh, 9, {"next:judge:claude", "factory:ready", "bug"}, {"next:judge:hermes"}, {"next:judge:hermes"})
        self.assertIn(("POST", "/issues/9/labels", {"labels": ["next:judge:hermes"]}), gh.calls)
        self.assertIn(("DELETE", "/issues/9/labels/next%3Ajudge%3Aclaude", None), gh.calls)
        self.assertFalse(any("factory" in p or "bug" in p for m, p, _ in gh.calls if m == "DELETE"))

    def test_nothing_to_do_changes_nothing(self):
        gh = FakeGitHub()
        c.sync_labels(gh, 9, {"next:merge:codex"}, {"next:merge:codex"}, {"next:merge:codex"})
        self.assertEqual(gh.calls, [])

    def test_needs_owner_comments_once_when_added(self):
        gh = FakeGitHub()
        c.sync_labels(gh, 9, set(), {"needs:owner"}, {"needs:owner"})
        self.assertEqual([p for m, p, _ in gh.calls if p.endswith("/comments")], ["/issues/9/comments"])
        gh2 = FakeGitHub()
        c.sync_labels(gh2, 9, {"needs:owner"}, {"needs:owner"}, {"needs:owner"})
        self.assertEqual(gh2.calls, [])

    def test_unknown_labels_are_created_first(self):
        gh = FakeGitHub()
        c.sync_labels(gh, 9, set(), {"next:fix:codex"}, set())
        self.assertEqual(gh.calls[0], ("POST", "/labels", {"name": "next:fix:codex", "color": "1d76db"}))


class Reconcile(unittest.TestCase):
    def run_conductor(self, **kw):
        gh = FakeGitHub(lists=lists(**kw), prs={p["number"]: p for p in kw.get("open_prs", ())})
        c.reconcile(gh, CONFIG, NOW)
        return gh.calls

    def test_withdrawn_readiness_clears_task_labels(self):
        ticket = item(5, "next:implement:codex", "bug")
        fix = item(9, "next:fix:codex", "bug", pull_request={})
        calls = self.run_conductor(open_all=[ticket, fix], open_prs=[pr(labels=[{"name": "next:fix:codex"}])])
        self.assertEqual(sorted(p for m, p, _ in calls if m == "DELETE"),
                         ["/issues/5/labels/next%3Aimplement%3Acodex", "/issues/9/labels/next%3Afix%3Acodex"])
        self.assertEqual([p for m, p, _ in calls if m != "DELETE"], [])

    def test_fix_round_level_from_findings_and_state_comment(self):
        ticket = item(5, "factory:ready", "points:8")
        judged = [dict(PROOFREAD, id=1), dict(review("claude", "APPROVED"), id=2), dict(review("hermes"), id=3)]
        open_pr = pr(labels=[])
        gh = FakeGitHub(lists=dict(lists(open_ready=[ticket], open_prs=[open_pr]), **{
            "/pulls/9/reviews": judged,
            "/pulls/9/reviews/3/comments": [{"body": "[critical] the step count is lost on rotation"}]}),
            prs={9: open_pr})
        c.reconcile(gh, CONFIG, NOW)
        added = sorted(b["labels"][0] for m, p, b in gh.calls if p == "/issues/9/labels")
        self.assertEqual(added, ["level:8", "next:fix:codex", "next:judge:hermes"])
        state = [b["body"] for m, p, b in gh.calls if m == "POST" and p == "/issues/9/comments"]
        self.assertTrue(state and state[0].startswith("<!-- factory-state "))

    def test_the_head_a_fix_round_produced_is_written_even_without_a_new_fix_label(self):
        before = {"floor": 0, "head": OLD, "levels": {}, "next_level": 5, "signaled": []}
        gh = FakeGitHub(lists={"/issues/9/comments": [state_comment(before)]})
        c.route_pr(gh, pr(), [], "pending", set(), {"next:judge:claude", "next:judge:hermes"}, 8, CONFIG)
        written = [b["body"] for m, p, b in gh.calls if (m, p) == ("PATCH", "/issues/comments/4")]
        self.assertEqual(stored(written)["levels"], {HEAD: 5})
        again = FakeGitHub(lists={"/issues/9/comments": [state_comment(body=written[0])]})
        c.route_pr(again, pr(), [], "pending", set(), {"next:judge:claude", "next:judge:hermes"}, 8, CONFIG)
        self.assertEqual([m for m, p, _ in again.calls if p.startswith("/issues/comments")], [])

    def test_the_fix_head_is_recorded_when_nothing_is_due(self):
        # Both judges approve the fix's head while CI runs: no label, but the state must learn the head.
        ticket = item(5, "factory:ready", "points:8")
        judged = [dict(PROOFREAD, id=1), dict(review("claude", "APPROVED"), id=2), dict(review("hermes", "APPROVED"), id=3)]
        open_pr = pr(labels=[])
        before = {"floor": 0, "head": OLD, "levels": {}, "next_level": 5, "signaled": []}
        gh = FakeGitHub(lists=dict(lists(open_ready=[ticket], open_prs=[open_pr]), **{
            "/pulls/9/reviews": judged, "/issues/9/comments": [state_comment(before)],
            f"/commits/{HEAD}/check-runs": [{"name": "build", "status": "in_progress"}]}), prs={9: open_pr})
        c.reconcile(gh, CONFIG, NOW)
        self.assertFalse([p for m, p, _ in gh.calls if p == "/issues/9/labels"])
        written = [b["body"] for m, p, b in gh.calls if (m, p) == ("PATCH", "/issues/comments/4")]
        self.assertEqual((stored(written)["levels"], stored(written)["next_level"]), ({HEAD: 5}, None))

    def test_a_canceled_fix_expects_no_head(self):
        # The fix is stopped by needs:owner; a later owner push must not count as that fix round.
        before = {"floor": 0, "head": HEAD, "levels": {}, "next_level": 5, "signaled": []}
        gh = FakeGitHub(lists={"/issues/9/comments": [state_comment(before)]})
        self.assertEqual(c.route_pr(gh, pr(), [], "green", set(), {"needs:owner"}, 8, CONFIG), {"needs:owner"})
        written = [b["body"] for m, p, b in gh.calls if (m, p) == ("PATCH", "/issues/comments/4")]
        self.assertIsNone(stored(written)["next_level"])
        update = FakeGitHub(lists={"/issues/9/comments": [state_comment(body=written[0])]})
        c.route_pr(update, pr(head={"sha": OLD}), [], "red", set(), {"needs:owner"}, 8, CONFIG)
        after = stored([b["body"] for m, p, b in update.calls if m == "PATCH"])
        self.assertEqual((after["levels"], after["floor"]), ({}, 0))

    def test_a_pr_without_a_ticket_is_judged_too(self):
        calls = self.run_conductor(open_prs=[pr(author="owner", body="Moves the workflows.", labels=[])])
        added = sorted(b["labels"][0] for m, p, b in calls if p == "/issues/9/labels")
        self.assertEqual(added, ["next:judge:claude", "next:judge:hermes"])

    def test_nothing_managed_makes_no_calls(self):
        self.assertEqual(self.run_conductor(open_all=[item(5, "bug")]), [])

    def test_acceptance_needs_a_merged_pr(self):
        closed = item(5, "factory:ready", state_reason="completed")
        self.assertEqual(self.run_conductor(closed_ready=[closed]), [])
        unmerged = pr(merged_at=None)
        self.assertEqual(self.run_conductor(closed_ready=[closed], closed_prs=[unmerged]), [])
        merged = pr(merged_at="2027-01-16T08:00:00Z")
        calls = self.run_conductor(closed_ready=[closed], closed_prs=[merged])
        self.assertIn(("POST", "/issues/5/labels", {"labels": ["step:acceptance"]}), calls)

    def test_acceptance_is_removed_without_a_merged_pr(self):
        calls = self.run_conductor(closed_ready=[item(5, "factory:ready", "step:acceptance", state_reason="completed")])
        self.assertEqual(calls, [("DELETE", "/issues/5/labels/step%3Aacceptance", None)])


if __name__ == "__main__":
    unittest.main()
