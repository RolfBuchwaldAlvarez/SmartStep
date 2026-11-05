"""Metrics use distinct review/check evidence and explicit duration semantics."""

import unittest
import factory_metrics as m
import routing


class Metrics(unittest.TestCase):
    def snapshot(self):
        return {"pr": {"number": 9, "state": "closed", "created_at": "2026-11-01T00:00:00Z",
                       "closed_at": "2026-11-01T01:00:00Z"}, "state": {"levels": {"head": 5}},
                "reviews": [{"id": 1, "state": "COMMENTED", "body": "Review summary"},
                            {"id": 2, "state": "APPROVED", "body": "Looks good"}],
                "inline": {1: ["[critical] data loss", "[minor] wording"]},
                "checks": [{"id": 10, "name": "android-ci", "conclusion": "failure"},
                           {"id": 10, "name": "android-ci", "conclusion": "failure"},
                           {"id": 11, "name": "conduct", "conclusion": "failure"}]}

    def summary(self, snapshots):
        return m.summarize(5, 3, snapshots, routing.severity_of, routing.review_findings)

    def test_counts_distinct_evidence_and_summary_is_not_an_extra_finding(self):
        result = self.summary([self.snapshot()])
        self.assertEqual(result["findings"], {"critical": 1, "major": 0, "minor": 1})
        self.assertEqual((result["review_rounds"], result["ci_failures"]), (2, 1))
        self.assertEqual((result["points"], result["levels_recorded"], result["duration_seconds"]), (3, [5], 3600))
        self.assertEqual(result, self.summary([self.snapshot()]))

    def test_open_duration_is_unknown_and_closed_duration_freezes(self):
        snap = self.snapshot()
        snap["pr"].update(state="open", closed_at=None)
        self.assertIsNone(self.summary([snap])["duration_seconds"])
        self.assertEqual(self.summary([self.snapshot()])["duration_seconds"], 3600)

    def test_all_attempts_contribute_and_unknown_dates_are_not_zero(self):
        second = self.snapshot()
        second["pr"].update(number=10, closed_at="2026-11-01T01:30:00Z")
        second["reviews"] = []
        second["checks"] = []
        result = self.summary([self.snapshot(), second])
        self.assertEqual((result["pull_requests"], result["duration_seconds"]), ([9, 10], 5400))
        second["pr"]["created_at"] = None
        self.assertIsNone(self.summary([second])["duration_seconds"])
        self.assertIsNone(self.summary([])["duration_seconds"])

    def test_standalone_untagged_finding_is_major_and_approvals_are_not_findings(self):
        snap = self.snapshot()
        snap["inline"] = {}
        result = self.summary([snap])
        self.assertEqual(result["findings"], {"critical": 0, "major": 1, "minor": 0})


class Integration(unittest.TestCase):
    def test_closed_pr_snapshot_is_written_once_and_ignores_untrusted_comments(self):
        import json
        import test_conductor as t
        closed = t.pr(labels=[], state="closed", closed_at="2027-01-15T09:00:00Z", merged_at=None)
        ticket = t.item(5, "factory:ready", "points:3", state_reason="not_planned")
        data = dict(t.lists(closed_ready=[ticket], closed_prs=[closed]), **{
            "/pulls?state=all": [closed],
            "/pulls/9/reviews": [dict(t.review("hermes"), id=2), dict(t.PROOFREAD, id=1)],
            "/pulls/9/reviews/2/comments": [{"body": "[minor] wording"}],
            "/issues/9/comments": [{"id": 55, "user": {"login": "someone"}, "body": m.MARK + '{} -->'}]})
        gh = t.FakeGitHub(lists=data)
        t.c.reconcile(gh, t.CONFIG, t.NOW)
        bodies = [b["body"] for method, path, b in gh.calls if path == "/issues/9/comments"]
        self.assertEqual(len(bodies), 1)
        body = bodies[0]
        payload = json.loads(body[len(m.MARK):body.index(" -->")])
        self.assertEqual(payload["review_rounds"], 1)  # author's proofread is not an outside round
        self.assertEqual(payload["findings"]["minor"], 1)
        self.assertEqual(payload["duration_seconds"], 3600)
        data["/issues/9/comments"].append({"id": 56, "user": {"login": "github-actions[bot]"}, "body": body})
        again = t.FakeGitHub(lists=data)
        t.c.reconcile(again, t.CONFIG, t.NOW + 100)
        self.assertEqual(again.calls, [])

    def test_failed_evidence_read_publishes_no_partial_metrics(self):
        import test_conductor as t
        class MissingChecks(t.FakeGitHub):
            def all(self, path):
                if '/check-runs' in path:
                    raise RuntimeError('checks unavailable')
                return super().all(path)
        ticket = t.item(5, 'factory:ready', 'points:3')
        gh = MissingChecks(lists={'/pulls?state=all': [t.pr()]})
        with self.assertRaisesRegex(RuntimeError, 'checks unavailable'):
            t.c.sync_ticket_metrics(gh, [ticket], t.NOW, t.CONFIG)
        self.assertEqual(gh.calls, [])

    def test_implementation_authors_reviews_are_not_judge_metrics(self):
        import json
        import test_conductor as t
        ticket = t.item(5, 'factory:ready', 'points:3')
        attempts = [t.pr(), t.pr('claude', number=10)]
        gh = t.FakeGitHub(lists={'/pulls?state=all': attempts,
                                 '/pulls/9/reviews': [dict(t.review('claude'), id=1),
                                                     dict(t.review('hermes', 'APPROVED'), id=2)]})
        t.c.sync_ticket_metrics(gh, [ticket], t.NOW, t.CONFIG)
        bodies = [b['body'] for method, path, b in gh.calls]
        self.assertEqual(len(bodies), 2)
        self.assertEqual(bodies[0], bodies[1])
        result = json.loads(bodies[0][len(m.MARK):bodies[0].index(' -->')])
        self.assertEqual(result['review_rounds'], 1)
        self.assertEqual(sum(result['findings'].values()), 0)

    def test_successful_retry_does_not_hide_an_earlier_failed_run(self):
        import json
        import test_conductor as t
        class RetriedChecks(t.FakeGitHub):
            def all(self, path):
                if '/check-runs' in path:
                    success = {"id": 12, "name": "android-ci", "conclusion": "success"}
                    failed = {"id": 11, "name": "android-ci", "conclusion": "failure"}
                    return [failed, success] if 'filter=all' in path else [success]
                return super().all(path)
        gh = RetriedChecks(lists={'/pulls?state=all': [t.pr()]})
        t.c.sync_ticket_metrics(gh, [t.item(5, 'factory:ready', 'points:3')], t.NOW, t.CONFIG)
        body = gh.calls[0][2]['body']
        result = json.loads(body[len(m.MARK):body.index(' -->')])
        self.assertEqual(result['ci_failures'], 1)

class ReconcileBudget(unittest.TestCase):
    def setup_ticket(self):
        import test_conductor as t
        ticket = t.item(5, 'factory:ready', 'points:3', state='closed')
        attempt = t.pr(state='closed', closed_at='2027-01-15T09:00:00Z')
        return t, ticket, attempt

    def github(self, t, attempts):
        class Recording(t.FakeGitHub):
            def __init__(self):
                super().__init__(lists={'/pulls?state=all': attempts})
                self.reads = []
            def all(self, path):
                self.reads.append(path)
                return super().all(path)
            def call(self, method, path, body=None):
                result = super().call(method, path, body)
                if method == 'POST' and path.endswith('/comments'):
                    self.lists.setdefault(path, []).append(
                        {'id': len(self.calls), 'user': {'login': routing.STATE_WRITER}, **body})
                if method == 'PATCH' and path.startswith('/issues/comments/'):
                    for comments in self.lists.values():
                        for comment in comments:
                            if comment.get('id') == int(path.rsplit('/', 1)[1]):
                                comment.update(body)
                return result
        return Recording()

    def test_final_ticket_reads_only_checkpoint_and_inventory(self):
        t, ticket, attempt = self.setup_ticket()
        gh = self.github(t, [attempt])
        t.c.sync_ticket_metrics(gh, [ticket], t.NOW, t.CONFIG)
        gh.reads.clear()
        gh.calls.clear()
        t.c.sync_ticket_metrics(gh, [ticket], t.NOW + 100, t.CONFIG)
        self.assertEqual(gh.reads, ['/pulls?state=all', '/issues/5/comments'])
        self.assertEqual(gh.calls, [])

    def test_reopened_ticket_pr_new_attempt_points_and_config_invalidate_final(self):
        import copy
        for change in ('ticket', 'pr', 'attempt', 'points', 'config'):
            with self.subTest(change=change):
                t, ticket, attempt = self.setup_ticket()
                config = copy.deepcopy(t.CONFIG)
                gh = self.github(t, [attempt])
                t.c.sync_ticket_metrics(gh, [ticket], t.NOW, config)
                checkpoint = gh.lists['/issues/5/comments'][0]
                old_body = checkpoint['body']
                if change == 'ticket': ticket['state'] = 'open'
                if change == 'pr': attempt['state'] = 'open'
                if change == 'attempt': gh.lists['/pulls?state=all'].append(t.pr(number=10))
                if change == 'points': ticket['labels'].append({'name': 'points:5'})
                if change == 'config': config['judges_per_pr'] = 1
                gh.reads.clear()
                t.c.sync_ticket_metrics(gh, [ticket], t.NOW + 100, config)
                self.assertIn('/pulls/9/reviews', gh.reads)
                if change in ('points', 'config'):
                    fresh = self.github(t, gh.lists['/pulls?state=all'])
                    t.c.sync_ticket_metrics(fresh, [ticket], t.NOW + 100, config)
                    expected_body = fresh.lists['/issues/5/comments'][0]['body']
                    self.assertNotEqual(expected_body, old_body)
                    self.assertIn(('PATCH', f"/issues/comments/{checkpoint['id']}",
                                   {'body': expected_body}), gh.calls)
                    self.assertEqual(checkpoint['body'], expected_body)
                    gh.reads.clear()
                    gh.calls.clear()
                    t.c.sync_ticket_metrics(gh, [ticket], t.NOW + 200, config)
                    self.assertEqual(gh.reads, ['/pulls?state=all', '/issues/5/comments'])
                    self.assertEqual(gh.calls, [])

    def test_untrusted_checkpoint_cannot_skip_evidence(self):
        t, ticket, attempt = self.setup_ticket()
        gh = self.github(t, [attempt])
        t.c.sync_ticket_metrics(gh, [ticket], t.NOW, t.CONFIG)
        for comment in gh.lists.get('/issues/5/comments', []):
            comment['user']['login'] = 'someone'
        gh.reads.clear()
        t.c.sync_ticket_metrics(gh, [ticket], t.NOW, t.CONFIG)
        self.assertIn('/pulls/9/reviews', gh.reads)

    def test_pending_checks_do_not_finalize(self):
        t, ticket, attempt = self.setup_ticket()
        gh = self.github(t, [attempt])
        gh.lists['/commits/head/check-runs?filter=all'] = [{'id': 1, 'name': 'ci', 'status': 'in_progress'}]
        # Use the fixture's actual head.
        gh.lists[f"/commits/{attempt['head']['sha']}/check-runs?filter=all"] = gh.lists['/commits/head/check-runs?filter=all']
        t.c.sync_ticket_metrics(gh, [ticket], t.NOW, t.CONFIG)
        gh.reads.clear()
        t.c.sync_ticket_metrics(gh, [ticket], t.NOW, t.CONFIG)
        self.assertIn('/pulls/9/reviews', gh.reads)

    def test_open_metrics_do_not_change_as_clock_advances(self):
        t, ticket, attempt = self.setup_ticket()
        ticket['state'] = attempt['state'] = 'open'
        gh = self.github(t, [attempt])
        t.c.sync_ticket_metrics(gh, [ticket], t.NOW, t.CONFIG)
        gh.calls.clear()
        t.c.sync_ticket_metrics(gh, [ticket], t.NOW + 100, t.CONFIG)
        self.assertEqual(gh.calls, [])

    def test_partial_publication_never_records_completion(self):
        t, ticket, attempt = self.setup_ticket()
        second = dict(attempt, number=10)
        gh = self.github(t, [attempt, second])
        original = gh.call
        def fail_second(method, path, body=None):
            if path == '/issues/10/comments':
                raise RuntimeError('publication failed')
            return original(method, path, body)
        gh.call = fail_second
        with self.assertRaisesRegex(RuntimeError, 'publication failed'):
            t.c.sync_ticket_metrics(gh, [ticket], t.NOW, t.CONFIG)
        self.assertNotIn('/issues/5/comments', gh.lists)
        gh.call = original
        t.c.sync_ticket_metrics(gh, [ticket], t.NOW, t.CONFIG)
        self.assertIn('/issues/5/comments', gh.lists)
        self.assertEqual(len(gh.lists['/issues/9/comments']), 1)
        self.assertEqual(len(gh.lists['/issues/10/comments']), 1)

    def test_repository_metadata_and_comment_timestamps_do_not_invalidate(self):
        t, ticket, attempt = self.setup_ticket()
        gh = self.github(t, [attempt])
        t.c.sync_ticket_metrics(gh, [ticket], t.NOW, t.CONFIG)
        attempt['head']['repo'] = {'pushed_at': 'later'}
        attempt['updated_at'] = ticket['updated_at'] = 'later'
        gh.reads.clear()
        t.c.sync_ticket_metrics(gh, [ticket], t.NOW + 100, t.CONFIG)
        self.assertEqual(gh.reads, ['/pulls?state=all', '/issues/5/comments'])
