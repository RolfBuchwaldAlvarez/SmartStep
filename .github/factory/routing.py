"""Complexity routing for the factory (olympus-agents docs/complexity-routing.md).

Pure functions; the conductor calls them and writes the results as labels:

  points:<n>     the ticket's estimate in Fibonacci points, set when the ticket is
                 written and approved by the owner; without it no implementation
  level:<n>      the level the next implement or fix run uses; the poller maps it
                 to a model and an effort (`levels` in olympus-agents' agents.json)
  risk:high      the judges run at high effort (risky files in the diff)
  needs:points   a factory:ready ticket without a valid points label
  needs:split    13 or more points, at the start or after escalation

The escalation floor lives in a state comment the conductor keeps on the PR, so
re-running the conductor never raises it twice for the same evidence.
"""

from __future__ import annotations

import json
import re

FIB = (1, 2, 3, 5, 8, 13, 21)
SPLIT_AT = 13
MIN_LEVEL = 2
STATE_MARK = "<!-- factory-state "
SEVERITIES = ("minor", "major", "critical")
# Explicit tags first; Codex's P0-P3 as a fallback (P0 critical, P1-P2 major, P3 minor).
TAG = re.compile(r"\[(critical|major|minor|blocking|non-blocking|p[0-3])\]", re.IGNORECASE)
TAG_SEVERITY = {"critical": "critical", "p0": "critical", "major": "major", "blocking": "major", "p1": "major",
                "p2": "major", "minor": "minor", "non-blocking": "minor", "p3": "minor"}
RISKY = re.compile(r"(\.gradle(\.kts)?$|gradle\.properties$|(^|/)gradle/|libs\.versions\.toml$|AndroidManifest\.xml$|"
                   r"(^|/)schemas/|migration|\.sql$|(^|/)\.github/|security|crypto|auth)", re.IGNORECASE)
RISKY_FILE_COUNT = 20


def points_of(labels) -> int | None:
    """The ticket's points from exactly one `points:<n>` label with a Fibonacci value, else None."""
    values = {l.split(":", 1)[1] for l in labels if l.startswith("points:")}
    if len(values) != 1:
        return None
    value = values.pop()
    return int(value) if value.isdigit() and int(value) in FIB else None


def next_step(n: int) -> int:
    """The next Fibonacci value above n (21 and beyond: 34, which still means split)."""
    return next((f for f in FIB if f > n), 34)


def step_below(n: int) -> int:
    lower = [f for f in FIB if f < n]
    return max(lower[-1] if lower else MIN_LEVEL, MIN_LEVEL)


def severity_of(texts) -> str:
    """The highest tagged severity in the open findings; untagged findings count as major."""
    found = [TAG_SEVERITY[m.lower()] for text in texts for m in TAG.findall(text or "")]
    if not found:
        return "major"
    return max(found, key=SEVERITIES.index)


def fix_level(points: int, severity: str, floor: int = 0) -> int:
    """Level of a fix round: by the open findings' severity, never below the escalation floor."""
    base = {"minor": MIN_LEVEL, "major": step_below(points), "critical": points}[severity]
    return max(base, floor, MIN_LEVEL)


def risk_of(filenames) -> str:
    files = list(filenames)
    return "high" if len(files) > RISKY_FILE_COUNT or any(RISKY.search(f) for f in files) else "normal"


# ------------------------------------------------------------ state comment

def read_state(comments) -> tuple[int | None, dict]:
    """(comment id, state) of the conductor's state comment on a PR, or (None, empty state)."""
    for comment in comments:
        body = comment.get("body") or ""
        if body.startswith(STATE_MARK):
            try:
                return comment["id"], json.loads(body[len(STATE_MARK):body.index(" -->")])
            except (ValueError, KeyError):
                return comment.get("id"), {}
    return None, {}


def render_state(state: dict) -> str:
    return (STATE_MARK + json.dumps(state, sort_keys=True, separators=(",", ":")) + " -->\n"
            "Factory state (kept by the conductor): the level each round ran at and the escalation floor.")


def advance(state: dict, points: int, head: str, signal: bool) -> dict:
    """Record which level produced `head` and raise the floor once per head on a signal. Pure."""
    state = {"levels": dict(state.get("levels", {})), "signaled": list(state.get("signaled", [])),
             "floor": state.get("floor", 0), "head": state.get("head"), "next_level": state.get("next_level")}
    if state["head"] != head:
        if state["head"] is not None and state["next_level"]:
            state["levels"][head] = state["next_level"]       # a fix round produced this head
            state["next_level"] = None                         # a later base update is no fix round
        state["head"] = head
    if signal and head not in state["signaled"]:
        produced_by = state["levels"].get(head, points)
        state["floor"] = max(state["floor"], next_step(produced_by))
        state["signaled"].append(head)
    return state


def signal_at(head: str, checks: str, reviews_by_judge: dict, underestimated: bool, fixed_head: bool) -> bool:
    """Evidence that the head's round was too weak (docs/complexity-routing.md, "Signals")."""
    rejected_on_head = False
    for reviews in reviews_by_judge.values():
        judged = [r for r in reviews if r.get("commit_id")]
        if judged and judged[-1].get("commit_id") == head and judged[-1].get("state") != "APPROVED":
            rejected_on_head = True
            earlier = [r for r in judged if r.get("commit_id") != head]
            if earlier and earlier[-1].get("state") != "APPROVED":
                return True                                    # the same judge rejects two rounds in a row
    if checks == "red" and fixed_head:
        return True                                            # CI red again after a fix round
    return underestimated and (checks == "red" or rejected_on_head)
