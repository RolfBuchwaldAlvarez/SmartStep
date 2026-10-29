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


class Config(unittest.TestCase):
    def test_factory_yml(self):
        self.assertEqual(CONFIG, {"implementers": ["codex", "claude"], "judges": ["claude", "hermes", "codex"],
                                  "judges_per_pr": 2, "max_rounds": 3})

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
        self.assertEqual(c.ticket_labels(False, CONFIG), {"next:implement:codex"})
        self.assertEqual(c.ticket_labels(True, CONFIG), set())

    def test_implementer_label_picks_another_implementer(self):
        self.assertEqual(c.ticket_labels(False, CONFIG, frozenset({"implementer:claude"})), {"next:implement:claude"})
        self.assertEqual(c.ticket_labels(False, CONFIG, frozenset({"implementer:owner"})), set())

    def test_unknown_or_ambiguous_implementer_falls_back_to_the_default(self):
        self.assertEqual(c.ticket_labels(False, CONFIG, frozenset({"implementer:hermes"})), {"next:implement:codex"})
        both = frozenset({"implementer:claude", "implementer:codex"})
        self.assertEqual(c.ticket_labels(False, CONFIG, both), {"next:implement:codex"})

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

    def test_checks_state(self):
        self.assertEqual(c.checks_state([]), "green")
        self.assertEqual(c.checks_state([{"status": "completed", "conclusion": "success"}]), "green")
        self.assertEqual(c.checks_state([{"status": "in_progress"}]), "pending")
        self.assertEqual(c.checks_state([{"status": "completed", "conclusion": "failure"}]), "red")


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
