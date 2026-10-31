#!/usr/bin/env python3
"""Factory conductor (my-ai-second-brain#173): writes the next step as labels.

Deterministic, no AI. Runs as a GitHub Actions workflow on every relevant event
and every 15 minutes. It reads the state from GitHub only (tickets, PRs, reviews
on the head, checks) and sets or removes labels so that they match:

  ticket  factory:ready, no PR yet       -> next:implement:<implementer>
          (implementer:<name> picks one of `implementers`, default the first;
          implementer:owner means the owner implements: no label)
  PR      by an agent or the owner; its judges are the first `judges_per_pr`
          of `judges` other than its author (the owner's PRs get no proofread;
          update, fix and merge are his, the conductor only asks the judges)
          conflicts with its base        -> next:update:<author>
          no proofread yet (first hour)  -> next:proofread:<author>
          a judge's approval missing     -> next:judge:<judge>
          all judges reviewed the head,
          not all approve or CI red      -> next:fix:<author> (plus the open judges)
          all approve, CI green          -> next:merge:<author>
          a judge at the round limit     -> needs:owner (one comment)
  ticket  closed as completed with
          factory:ready and a merged PR  -> step:acceptance, until the owner sets accepted
  other   open issue, a PR by someone else,
          or a PR for a ticket without
          factory:ready                  -> none of the conductor's labels

Complexity routing (routing.py, olympus-agents docs/complexity-routing.md):
a ticket needs points:<n> (else needs:points; 13 or more: needs:split); the
implement and fix labels come with level:<n> for the run's model and effort;
judge labels on a risky diff come with risk:high; evidence that a round was too
weak raises an escalation floor (state comment on the PR); points or a floor
of 13 or more stop an agent's PR with needs:split, unless needs:owner stands.

The agents' pollers act on the next:* labels addressed to them and decide the
details (rounds, re-checks, one run at a time). Re-running changes nothing.
Uses only the workflow's own token: labels and comments, nothing else.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import routing  # noqa: E402

API = "https://api.github.com"
OWNER_LOGIN = "RolfBuchwaldAlvarez"
AGENT_LOGINS = {"claude-bot-rba[bot]": "claude", "codex-bot-rba[bot]": "codex", "hermes-bot-rba[bot]": "hermes"}
DECIDING = ("APPROVED", "CHANGES_REQUESTED", "DISMISSED")
PROOFREAD = re.compile(r"^[\s*_#>]*Proofread:")
CLOSES = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", re.IGNORECASE)
PROOFREAD_WAIT = 3600
MANAGED = ("next:", "needs:owner", "needs:points", "needs:split", "step:acceptance", "level:", "risk:")
LABEL_COLORS = {"next:": "1d76db", "needs:": "d93f0b", "step:acceptance": "0e8a16", "level:": "c5def5",
                "risk:": "fbca04"}
NEEDS_COMMENTS = {
    "needs:owner": "a judge reached the round limit without approving. The agents pause until you decide.",
    "needs:points": "this ticket has no valid `points:<n>` label (1, 2, 3, 5, 8, 13 or 21). "
                    "Nothing is implemented until it has one.",
    "needs:split": "this is estimated or escalated at 13 points or more: too uncertain for one PR. "
                   "Please split it into tickets of at most 8 points. The agents pause here.",
}


# ----------------------------------------------------------------- config

def load_config(path: Path) -> dict:
    """The small `key: value` file .github/factory.yml (lists comma-separated)."""
    config = {"implementers": ["codex"], "judges": ["claude", "hermes"], "judges_per_pr": 2, "max_rounds": 3,
              "required_checks": []}
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if key in ("judges", "implementers", "implementer", "required_checks"):     # `implementer` is the former single key
            config["implementers" if key == "implementer" else key] = [v.strip() for v in value.split(",") if v.strip()]
        elif key in ("max_rounds", "judges_per_pr"):
            config[key] = int(value)
    return config


# -------------------------------------------------------------- decisions

def agent_of(login: str) -> str | None:
    return AGENT_LOGINS.get((login or "").lower())


def author_of(login: str) -> str | None:
    """The agent's name, "owner" for the owner, None for anyone else."""
    return "owner" if (login or "").lower() == OWNER_LOGIN.lower() else agent_of(login)


def implementer_for(labels: set[str], config: dict) -> str:
    """The ticket's implementer: an `implementer:<name>` label naming one of `implementers` or the owner,
    otherwise the first of `implementers`."""
    allowed = set(config["implementers"]) | {"owner"}
    chosen = sorted(l.split(":", 1)[1] for l in labels if l.startswith("implementer:") and l.split(":", 1)[1] in allowed)
    return chosen[0] if len(chosen) == 1 else config["implementers"][0]


def judges_for(author: str, config: dict) -> list[str]:
    """Nobody judges their own PR; the first `judges_per_pr` of the others do."""
    return [j for j in config["judges"] if j != author][:config["judges_per_pr"]]


def is_real(review: dict) -> bool:
    """Thread replies show up as empty COMMENTED reviews; they are not judgements."""
    return review.get("state") != "COMMENTED" or bool((review.get("body") or "").strip())


def linked_ticket(pr: dict) -> int | None:
    match = CLOSES.search(pr.get("body") or "")
    return int(match.group(1)) if match else None


OWN_CHECK = "conduct"                                      # the conductor's own job: never CI


def checks_state(check_runs: list[dict], required: list[str] = ()) -> str:
    """green, red or pending for the head's check runs, ignoring the conductor's own job.

    With `required` names, only the latest run of each counts, and a missing one is pending,
    so a PR whose CI did not run never looks green. Without, every other run counts
    (no checks: green)."""
    runs = [c for c in check_runs if c.get("name") != OWN_CHECK]
    if required:
        latest = {}
        for run in runs:
            if run.get("name") in required:
                # Check-run ids grow with creation; a queued run has no start time yet (Codex, #4).
                if run.get("name") not in latest or run.get("id", 0) > latest[run["name"]].get("id", 0):
                    latest[run["name"]] = run
        if len(latest) < len(set(required)):
            return "pending"
        runs = list(latest.values())
    if any(c.get("status") != "completed" for c in runs):
        return "pending"
    if any(c.get("conclusion") not in ("success", "neutral", "skipped") for c in runs):
        return "red"
    return "green"


def ticket_labels(has_pr: bool, config: dict, labels: frozenset = frozenset()) -> set[str]:
    implementer = implementer_for(set(labels), config)
    if has_pr or implementer == "owner":
        return set()
    points = routing.points_of(labels)
    if points is None:
        return {"needs:points"}
    if points >= routing.SPLIT_AT:
        return {"needs:split"}
    return {f"next:implement:{implementer}", f"level:{points}"}


def routed(labels: set[str], points: int | None, floor: int, severity: str, risk: str) -> set[str]:
    """Add complexity routing to a PR's labels from pr_labels. Pure."""
    labels = set(labels)
    if "needs:owner" in labels:                            # the pipeline's stop comes first
        return labels
    if points is not None and (points >= routing.SPLIT_AT or floor >= routing.SPLIT_AT):
        return {"needs:split"}
    if points is not None and any(l.startswith("next:fix:") for l in labels):
        labels.add(f"level:{routing.fix_level(points, severity, floor)}")
    if risk == "high" and any(l.startswith("next:judge:") for l in labels):
        labels.add("risk:high")
    return labels


def pr_labels(pr: dict, reviews: list[dict], checks: str, now: float, config: dict) -> set[str]:
    """The labels a factory PR should carry right now. Pure."""
    author = author_of(pr["user"]["login"])
    if author is None or pr.get("draft"):
        return set()
    by_owner = author == "owner"
    head = pr["head"]["sha"]
    reviews = [r for r in reviews if is_real(r)]
    if pr.get("mergeable_state") == "dirty" and not by_owner:
        return {f"next:update:{author}"}
    proofread = any(agent_of(r["user"]["login"]) == author and PROOFREAD.match(r.get("body") or "") for r in reviews)
    opened = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    if not by_owner and not proofread and now - opened <= PROOFREAD_WAIT:
        return {f"next:proofread:{author}"}
    judges = judges_for(author, config)
    open_judges, present = [], []
    for judge in judges:
        theirs = [r for r in reviews if agent_of(r["user"]["login"]) == judge]
        deciding = [r for r in theirs if r.get("state") in DECIDING]
        reviewed = [r.get("commit_id") for r in theirs]
        approved_head = bool(deciding) and deciding[-1]["state"] == "APPROVED" and deciding[-1].get("commit_id") == head
        approved_last = bool(deciding) and bool(reviewed) and deciding[-1]["state"] == "APPROVED" \
            and deciding[-1].get("commit_id") == reviewed[-1]
        if len(theirs) >= config["max_rounds"] and not approved_last:
            return {"needs:owner"}
        if any(r.get("commit_id") == head for r in theirs):
            present.append(judge)
        if not approved_head:
            open_judges.append(judge)
    labels = {f"next:judge:{j}" for j in open_judges}
    if by_owner:                                           # fixing and merging are his
        return labels
    if not open_judges:
        if checks == "green":
            return {f"next:merge:{author}"}
        if checks == "red":
            return {f"next:fix:{author}"}
        return set()                                       # checks still running
    if len(present) == len(judges):                        # a fix round waits for both judgements
        labels.add(f"next:fix:{author}")
    return labels


def acceptance_labels(labels: set[str]) -> set[str]:
    return set() if "accepted" in labels else {"step:acceptance"}


# ----------------------------------------------------------------- GitHub

class GitHub:
    def __init__(self, repo: str, token: str):
        self.repo, self.token = repo, token

    def call(self, method: str, path: str, body=None):
        req = urllib.request.Request(f"{API}/repos/{self.repo}{path}", method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": f"Bearer {self.token}",
                                              "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
        return json.loads(raw) if raw else None

    def all(self, path: str) -> list:
        items, page = [], 1
        while True:
            sep = "&" if "?" in path else "?"
            batch = self.call("GET", f"{path}{sep}per_page=100&page={page}")
            if isinstance(batch, dict):
                batch = batch.get("check_runs", [])
            items += batch
            if len(batch) < 100:
                return items
            page += 1


def sync_labels(gh, number: int, current: set[str], desired: set[str], known: set[str]) -> None:
    """Make the conductor's labels on an issue or PR match `desired`; leave all others alone."""
    for name in sorted(desired - current):
        if name not in known:
            color = next(c for p, c in LABEL_COLORS.items() if name.startswith(p))
            try:
                gh.call("POST", "/labels", {"name": name, "color": color})
            except urllib.error.HTTPError as exc:
                if exc.code != 422:                        # 422: it exists already
                    raise
            known.add(name)
        gh.call("POST", f"/issues/{number}/labels", {"labels": [name]})
        if name in NEEDS_COMMENTS:
            gh.call("POST", f"/issues/{number}/comments",
                    {"body": f"@{OWNER_LOGIN} the factory needs you here: {NEEDS_COMMENTS[name]}"})
        print(f"conductor: #{number} + {name}")
    for name in sorted(current - desired):
        if name.startswith(MANAGED):
            gh.call("DELETE", f"/issues/{number}/labels/{urllib.request.quote(name, safe='')}")
            print(f"conductor: #{number} - {name}")


def route_pr(gh, pr: dict, reviews: list[dict], checks: str, current: set[str], desired: set[str],
             points: int | None, config: dict) -> set[str]:
    """Complexity routing for one PR: findings' severity, risk, escalation floor (state comment)."""
    number, head = pr["number"], pr["head"]["sha"]
    author = author_of(pr["user"]["login"])
    if author == "owner":
        points = None                                      # his PRs: no levels, no split, no state comment
    real = [r for r in reviews if is_real(r)]
    by_judge = {j: [r for r in real if agent_of(r["user"]["login"]) == j] for j in judges_for(author, config)}
    floor, severity = 0, "major"
    if points is not None:
        comment_id, before = routing.read_state(gh.all(f"/issues/{number}/comments"))
        state = routing.advance(before, points, head, False)
        signal = routing.signal_at(head, checks, by_judge, "complexity:underestimated" in current,
                                   head in state["levels"])
        state = routing.advance(state, points, head, signal)
        floor = state["floor"]
        open_reviews = [r for rs in by_judge.values() for r in rs[-1:]
                        if r.get("commit_id") == head and r.get("state") != "APPROVED"]
        findings = []
        for r in open_reviews:
            comments = [c.get("body") for c in gh.all(f"/pulls/{number}/reviews/{r['id']}/comments")]
            findings += routing.review_findings(r.get("body"), comments)
        severity = routing.severity_of(findings)
        labels = routed(desired, points, floor, severity, "normal")
        fix = next((l for l in labels if l.startswith("level:")), None)
        state["next_level"] = int(fix.split(":", 1)[1]) if fix else None   # no fix due: no head to expect
        if state != before or comment_id is None:
            body = routing.render_state(state)
            if comment_id is None:
                gh.call("POST", f"/issues/{number}/comments", {"body": body})
            else:
                gh.call("PATCH", f"/issues/comments/{comment_id}", {"body": body})
    risk = "normal"
    if any(l.startswith("next:judge:") for l in desired):
        risk = routing.risk_of(f["filename"] for f in gh.all(f"/pulls/{number}/files"))
    return routed(desired, points, floor, severity, risk)


def reconcile(gh, config: dict, now: float) -> None:
    known = {l["name"] for l in gh.all("/labels")}
    prs = gh.all("/pulls?state=open")
    by_ticket = {}
    for pr in prs:
        ticket = linked_ticket(pr)
        if ticket is not None and author_of(pr["user"]["login"]):
            by_ticket.setdefault(ticket, pr)
    handled = set()
    for issue in gh.all("/issues?state=open&labels=factory:ready"):
        if issue.get("pull_request"):
            continue
        current = {l["name"] for l in issue["labels"]}
        desired = ticket_labels(issue["number"] in by_ticket, config, frozenset(current))
        sync_labels(gh, issue["number"], current, desired, known)
        handled.add(issue["number"])
    ready = [i for i in gh.all("/issues?state=all&labels=factory:ready") if not i.get("pull_request")]
    tickets = {i["number"] for i in ready}
    ticket_points = {i["number"]: routing.points_of({l["name"] for l in i["labels"]}) for i in ready}
    for pr in prs:                                         # every PR by an agent or the owner ...
        if author_of(pr["user"]["login"]) is None:
            continue
        ticket = linked_ticket(pr)
        if ticket is not None and ticket not in tickets:
            continue                                       # ... except for a ticket the owner took out of the factory
        full = gh.call("GET", f"/pulls/{pr['number']}")
        reviews = gh.all(f"/pulls/{pr['number']}/reviews")
        checks = checks_state(gh.all(f"/commits/{pr['head']['sha']}/check-runs"), config["required_checks"])
        current = {l["name"] for l in pr["labels"]}
        desired = pr_labels(full, reviews, checks, now, config)
        if not full.get("draft"):                          # also with nothing due, to record a fix round's head
            desired = route_pr(gh, full, reviews, checks, current, desired, ticket_points.get(ticket), config)
        sync_labels(gh, pr["number"], current, desired, known)
        handled.add(pr["number"])
    for item in gh.all("/issues?state=open"):            # no longer a factory item: clear our labels
        current = {l["name"] for l in item["labels"]}
        if item["number"] not in handled and any(name.startswith(MANAGED) for name in current):
            sync_labels(gh, item["number"], current, set(), known)
    closed = [i for i in gh.all("/issues?state=closed&labels=factory:ready") if not i.get("pull_request")]
    merged = {linked_ticket(p) for p in gh.all("/pulls?state=closed") if p.get("merged_at")} if closed else set()
    for issue in closed:
        current = {l["name"] for l in issue["labels"]}
        delivered = issue.get("state_reason") == "completed" and issue["number"] in merged
        sync_labels(gh, issue["number"], current, acceptance_labels(current) if delivered else set(), known)


def main() -> int:
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        print("conductor: GITHUB_REPOSITORY and GITHUB_TOKEN are required", file=sys.stderr)
        return 2
    config = load_config(Path(__file__).resolve().parent.parent / "factory.yml")
    reconcile(GitHub(repo, token), config, time.time())
    return 0


if __name__ == "__main__":
    sys.exit(main())
