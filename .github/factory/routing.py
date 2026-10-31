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
STATE_WRITER = "github-actions[bot]"                       # the conductor's workflow token
SEVERITIES = ("minor", "major", "critical")
# Explicit tags first; Codex's P0-P3 as a fallback (P0 critical, P1-P2 major, P3 minor).
TAG = re.compile(r"\[(critical|major|minor|blocking|non-blocking|p[0-3])\]", re.IGNORECASE)
TAG_SEVERITY = {"critical": "critical", "p0": "critical", "major": "major", "blocking": "major", "p1": "major",
                "p2": "major", "minor": "minor", "non-blocking": "minor", "p3": "minor"}
RISKY = re.compile(r"(\.gradle(\.kts)?$|gradle\.properties$|(^|/)gradle/|libs\.versions\.toml$|AndroidManifest\.xml$|"
                   r"(^|/)schemas/|migration|\.sql$|(^|/)\.github/|security|crypto|auth(?!or(?!i[sz])))", re.IGNORECASE)
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


def severity_of(findings) -> str:
    """The highest severity of the open findings, one text per finding; an untagged finding counts as major."""
    found = []
    for text in findings:
        tags = [TAG_SEVERITY[m.lower()] for m in TAG.findall(text or "")]
        found.append(max(tags, key=SEVERITIES.index) if tags else "major")
    return max(found, key=SEVERITIES.index) if found else "major"


def review_findings(body: str, comments) -> list[str]:
    """A review's findings: its inline comments, plus its body if the body is tagged or stands alone.
    An untagged body next to inline comments is the review's summary, not a finding."""
    comments = [c or "" for c in comments]
    return comments + [body or ""] if not comments or TAG.search(body or "") else comments


def fix_level(points: int, severity: str, floor: int = 0) -> int:
    """Level of a fix round: by the open findings' severity, never below the escalation floor."""
    base = {"minor": MIN_LEVEL, "major": step_below(points), "critical": points}[severity]
    return max(base, floor, MIN_LEVEL)


def risk_of(filenames) -> str:
    files = list(filenames)
    return "high" if len(files) > RISKY_FILE_COUNT or any(RISKY.search(f) for f in files) else "normal"


# ------------------------------------------------------------ state comment

def valid_state(state) -> bool:
    """The shape render_state writes: anything else is ignored, never used or overwritten."""
    def level(v):
        return isinstance(v, int) and not isinstance(v, bool)
    return (isinstance(state, dict) and set(state) == {"floor", "head", "levels", "next_level", "signaled"}
            and level(state["floor"]) and (state["head"] is None or isinstance(state["head"], str))
            and isinstance(state["levels"], dict)
            and all(isinstance(k, str) and level(v) for k, v in state["levels"].items())
            and (state["next_level"] is None or level(state["next_level"]))
            and isinstance(state["signaled"], list) and all(isinstance(h, str) for h in state["signaled"]))


def read_state(comments) -> tuple[int | None, dict]:
    """(comment id, state) of the conductor's state comment on a PR, or (None, empty state).
    Only a comment by the conductor's own identity with a valid state counts; anyone can comment."""
    for comment in comments:
        body = comment.get("body") or ""
        if (comment.get("user") or {}).get("login") != STATE_WRITER or not body.startswith(STATE_MARK):
            continue
        try:
            state = json.loads(body[len(STATE_MARK):body.index(" -->")])
        except ValueError:
            continue
        if valid_state(state) and "id" in comment:
            return comment["id"], state
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


# ------------------------------------------------------------ planning poker

ESTIMATE = re.compile(r"^[\s*_#>]*Estimate:[\s*_]*(\d+)", re.IGNORECASE)


def estimate_of(body: str) -> int | None:
    """The points of an `Estimate: <n> – reasoning` comment, if n is a Fibonacci value."""
    match = ESTIMATE.match(body or "")
    return int(match.group(1)) if match and int(match.group(1)) in FIB else None


def poker(estimates: dict) -> tuple[str, int | None]:
    """Planning poker over the estimators' points: ("agree", the higher value) when they are at most one
    Fibonacci step apart, ("differ", None) otherwise, ("open", None) while one is missing."""
    if not estimates or any(v is None for v in estimates.values()):
        return "open", None
    steps = [FIB.index(v) for v in estimates.values()]
    if max(steps) - min(steps) > 1:
        return "differ", None
    return "agree", max(estimates.values())
