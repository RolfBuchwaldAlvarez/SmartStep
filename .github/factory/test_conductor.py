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
    base = {"number": 9, "user": {"login": f"{author}-bot-rba[bot]"}, "head": {"sha": HEAD}, "draft": False,
            "created_at": OPENED, "mergeable_state": "clean", "body": "Closes #5"}
    base.update(extra)
    return base


def review(agent, state="COMMENTED", commit=HEAD, body="Round 1: findings."):
    return {"user": {"login": f"{agent}-bot-rba[bot]"}, "state": state, "commit_id": commit, "body": body}


PROOFREAD = review("codex", body="Proofread: no findings.", commit=OLD)


class Config(unittest.TestCase):
    def test_factory_yml(self):
        self.assertEqual(CONFIG, {"implementer": "codex", "judges": ["claude", "hermes"], "max_rounds": 3,
                                  "owner_paths": [".github/"]})


class Ticket(unittest.TestCase):
    def test_implement_until_a_pr_exists(self):
        self.assertEqual(c.ticket_labels(False, CONFIG), {"next:implement:codex"})
        self.assertEqual(c.ticket_labels(True, CONFIG), set())

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

    def test_drafts_and_owner_prs_get_nothing(self):
        self.assertEqual(self.labels([PROOFREAD], draft=True), set())
        self.assertEqual(c.pr_labels(dict(pr(), user={"login": "RolfBuchwaldAlvarez"}), [], "green", NOW, CONFIG), set())

    def test_checks_state(self):
        self.assertEqual(c.checks_state([]), "green")
        self.assertEqual(c.checks_state([{"status": "completed", "conclusion": "success"}]), "green")
        self.assertEqual(c.checks_state([{"status": "in_progress"}]), "pending")
        self.assertEqual(c.checks_state([{"status": "completed", "conclusion": "failure"}]), "red")


class FakeGitHub:
    def __init__(self, labels=()):
        self.calls, self.labels = [], set(labels)

    def call(self, method, path, body=None):
        self.calls.append((method, path, body))


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


if __name__ == "__main__":
    unittest.main()
