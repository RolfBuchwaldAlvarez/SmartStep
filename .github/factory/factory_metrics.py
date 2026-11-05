"""Recomputed, versioned ticket evidence for Codify; never drives routing."""

from datetime import datetime, timezone

FINAL_MARK = "<!-- factory-metrics-final "
MARK = "<!-- factory-metrics "
FAILED = {"failure", "timed_out", "action_required", "startup_failure"}


def timestamp(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() if value else None


def summarize(ticket, points, snapshots, severity_of, review_findings):
    """Count distinct source records, not repeated conductor observations or head labels.

    Snapshots contain only eligible judges' real reviews; proofreads are excluded by the caller.
    Duration is PR elapsed wall time, not agent runtime or time since ticket approval.
    """
    rounds, findings, failures, levels = set(), {}, set(), set()
    starts, ends, open_prs = [], [], []
    for snapshot in snapshots:
        pr, state = snapshot["pr"], snapshot["state"]
        number = pr["number"]
        start = timestamp(pr.get("created_at"))
        end = timestamp(pr.get("closed_at"))
        if start is not None:
            starts.append(start)
        if end is not None:
            ends.append(end)
        if pr.get("state", "open") != "closed":
            open_prs.append(number)
        levels.update(state.get("levels", {}).values())
        for review in snapshot["reviews"]:
            key = (number, review["id"])
            rounds.add(key)
            if review["state"] not in ("COMMENTED", "CHANGES_REQUESTED"):
                continue
            inline = snapshot["inline"].get(review["id"], [])
            for index, text in enumerate(review_findings(review.get("body"), inline)):
                findings[(number, review["id"], index)] = severity_of([text])
        for check in snapshot["checks"]:
            if check.get("name") != "conduct" and check.get("conclusion") in FAILED:
                failures.add(check["id"])
    # Missing timestamps mean unknown duration, not a zero-length run.
    complete_dates = len(starts) == len(snapshots) and len(ends) == len(snapshots)
    duration = max(0, int(max(ends) - min(starts))) if snapshots and complete_dates and not open_prs else None
    return {"version": 1, "ticket": ticket, "points": points,
            "pull_requests": sorted(s["pr"]["number"] for s in snapshots), "open_pull_requests": sorted(open_prs),
            "levels_recorded": sorted(levels), "review_rounds": len(rounds),
            "findings": {s: sum(v == s for v in findings.values()) for s in ("minor", "major", "critical")},
            "ci_failures": len(failures), "duration_seconds": duration}
