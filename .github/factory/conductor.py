#!/usr/bin/env python3
"""Factory conductor (my-ai-second-brain#173): writes the next step as labels.

Deterministic, no AI. Runs as a GitHub Actions workflow on every relevant event
and every 15 minutes. It reads the state from GitHub only (tickets, PRs, reviews
on the head, checks) and sets or removes labels so that they match:

  ticket  factory:ready, no PR yet       -> next:implement:<implementer>
  PR      conflicts with its base        -> next:update:<author>
          no proofread yet (first hour)  -> next:proofread:<author>
          a judge's approval missing     -> next:judge:<judge>
          all judges reviewed the head,
          not all approve or CI red      -> next:fix:<author> (plus the open judges)
          all approve, CI green          -> next:merge:<author>
          a judge at the round limit     -> needs:owner (one comment)
  ticket  closed as completed with
          factory:ready and a merged PR  -> step:acceptance, until the owner sets accepted
  other   open issue or PR (e.g. the
          owner removed factory:ready)   -> none of the conductor's labels

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

API = "https://api.github.com"
OWNER_LOGIN = "RolfBuchwaldAlvarez"
AGENT_LOGINS = {"claude-bot-rba[bot]": "claude", "codex-bot-rba[bot]": "codex", "hermes-bot-rba[bot]": "hermes"}
DECIDING = ("APPROVED", "CHANGES_REQUESTED", "DISMISSED")
PROOFREAD = re.compile(r"^[\s*_#>]*Proofread:")
CLOSES = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", re.IGNORECASE)
PROOFREAD_WAIT = 3600
MANAGED = ("next:", "needs:owner", "step:acceptance")
LABEL_COLORS = {"next:": "1d76db", "needs:owner": "d93f0b", "step:acceptance": "0e8a16"}


# ----------------------------------------------------------------- config

def load_config(path: Path) -> dict:
    """The small `key: value` file .github/factory.yml (lists comma-separated)."""
    config = {"implementer": "codex", "judges": ["claude", "hermes"], "max_rounds": 3}
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if key == "judges":
            config[key] = [v.strip() for v in value.split(",") if v.strip()]
        elif key == "max_rounds":
            config[key] = int(value)
        elif key == "implementer":
            config[key] = value
    return config


# -------------------------------------------------------------- decisions

def agent_of(login: str) -> str | None:
    return AGENT_LOGINS.get((login or "").lower())


def is_real(review: dict) -> bool:
    """Thread replies show up as empty COMMENTED reviews; they are not judgements."""
    return review.get("state") != "COMMENTED" or bool((review.get("body") or "").strip())


def linked_ticket(pr: dict) -> int | None:
    match = CLOSES.search(pr.get("body") or "")
    return int(match.group(1)) if match else None


def checks_state(check_runs: list[dict]) -> str:
    """green, red or pending for the head's check runs (no checks: green)."""
    if any(c.get("status") != "completed" for c in check_runs):
        return "pending"
    if any(c.get("conclusion") not in ("success", "neutral", "skipped") for c in check_runs):
        return "red"
    return "green"


def ticket_labels(has_pr: bool, config: dict) -> set[str]:
    return set() if has_pr else {f"next:implement:{config['implementer']}"}


def pr_labels(pr: dict, reviews: list[dict], checks: str, now: float, config: dict) -> set[str]:
    """The labels a factory PR should carry right now. Pure."""
    author = agent_of(pr["user"]["login"])
    if author is None or pr.get("draft"):
        return set()
    head = pr["head"]["sha"]
    reviews = [r for r in reviews if is_real(r)]
    if pr.get("mergeable_state") == "dirty":
        return {f"next:update:{author}"}
    proofread = any(agent_of(r["user"]["login"]) == author and PROOFREAD.match(r.get("body") or "") for r in reviews)
    opened = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    if not proofread and now - opened <= PROOFREAD_WAIT:
        return {f"next:proofread:{author}"}
    judges = [j for j in config["judges"] if j != author]
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
        if name == "needs:owner":
            gh.call("POST", f"/issues/{number}/comments",
                    {"body": f"@{OWNER_LOGIN} the factory needs you here: a judge reached the round limit "
                             "without approving. The agents pause until you decide."})
        print(f"conductor: #{number} + {name}")
    for name in sorted(current - desired):
        if name.startswith(MANAGED):
            gh.call("DELETE", f"/issues/{number}/labels/{urllib.request.quote(name, safe='')}")
            print(f"conductor: #{number} - {name}")


def reconcile(gh, config: dict, now: float) -> None:
    known = {l["name"] for l in gh.all("/labels")}
    prs = gh.all("/pulls?state=open")
    by_ticket = {}
    for pr in prs:
        ticket = linked_ticket(pr)
        if ticket is not None and agent_of(pr["user"]["login"]):
            by_ticket.setdefault(ticket, pr)
    handled = set()
    for issue in gh.all("/issues?state=open&labels=factory:ready"):
        if issue.get("pull_request"):
            continue
        current = {l["name"] for l in issue["labels"]}
        sync_labels(gh, issue["number"], current, ticket_labels(issue["number"] in by_ticket, config), known)
        handled.add(issue["number"])
    tickets = {i["number"] for i in gh.all("/issues?state=all&labels=factory:ready") if not i.get("pull_request")}
    for ticket, pr in by_ticket.items():
        if ticket not in tickets:
            continue                                       # only PRs for factory tickets
        full = gh.call("GET", f"/pulls/{pr['number']}")
        reviews = gh.all(f"/pulls/{pr['number']}/reviews")
        checks = checks_state(gh.all(f"/commits/{pr['head']['sha']}/check-runs"))
        current = {l["name"] for l in pr["labels"]}
        sync_labels(gh, pr["number"], current, pr_labels(full, reviews, checks, now, config), known)
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
