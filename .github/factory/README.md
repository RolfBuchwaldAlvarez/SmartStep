# Factory conductor

This repository is a factory repository (`../factory.yml`, my-ai-second-brain#173): the agents' review pollers work here in label mode.

- `conductor.py` reads the state from GitHub and sets labels `next:<task>:<agent>`, `needs:owner` and `step:acceptance`; the agents act only on labels addressed to them. Its docstring lists the rules.
- `test_conductor.py`: `python3 -m unittest discover -s .github/factory`.
- The workflows in `.github/workflows/`, which only the owner can change: `factory-conductor.yml` runs the conductor on every relevant event, when a CI run finishes (`workflow_run`; `check_suite` never fires for checks created by GitHub Actions) and every 15 minutes; `factory-tests.yml` runs the conductor's tests on PRs that change the factory files; `android-ci.yml` builds the app and runs the unit tests, Android Lint and ktlint on every PR and on `main`. New drafts for the owner go into `workflows/` here.

## Who implements and who judges

Set in `../factory.yml` (owner decision 2026-10-29):

- `implementers: codex, claude` – Codex by default; a ticket label `implementer:claude` lets Claude implement it, `implementer:owner` means the owner implements it himself.
- `judges: claude, hermes, codex` with `judges_per_pr: 2` – a PR's judges are the first two distinct names from that list other than its author and everyone who authored any PR for its linked ticket (including closed or draft attempts). With no earlier implementation by another agent, the usual pairs are:

| Author | Judges |
|---|---|
| Codex | Claude, Hermes |
| Claude | Hermes, Codex |
| the owner | Claude, Hermes |

If ticket history leaves fewer than two eligible judges, the conductor sets `needs:owner` and keeps asking the eligible judges. Their findings still trigger fix rounds once every eligible judge has reviewed the head; red CI also triggers a fix after they approve. When exactly one seat is missing, an approval by the owner on the current head fills it, provided he authored no PR for the ticket. Automatic merging still requires every eligible judge and the owner to approve the head, plus green CI. An old or dismissed owner approval does not count. With no eligible judge, or when the owner implemented the ticket, the owner must decide how to complete the PR; his approval cannot fill two seats or approve his own work. The owner request comment names this eligibility shortage separately from a round-limit pause. Excluded agents' reviews do not count toward routing or escalation. Ticket history is read from all PRs before label writes; an API failure stops that cycle rather than assuming an empty history.

A PR without a ticket (for example the owner's workflow PRs, or changes to the factory itself) is judged the same way.

**CI for the merge:** `required_checks` in `../factory.yml` names the checks that count; a PR without them stays pending. The conductor's own `conduct` job never counts. It names `android-ci`, so no PR merges without a green Android build.

PRs by the owner get no proofread; updating, fixing and merging them stays with him – the conductor only asks the judges.

## Complexity routing

`routing.py`, concept in olympus-agents `docs/complexity-routing.md` (reviewed by Codex and Hermes, olympus-agents#29):

- **Planning poker** (owner decision 2026-10-31, as at his former employer): a ticket drafted without points gets the label `factory:estimate`. The conductor asks each of `estimators` (`factory.yml`: Codex and Claude) with `next:estimate:<agent>`; each reads the ticket and the code and posts one comment `Estimate: <n> – <one sentence naming the criteria>` without reading the other's. At most one Fibonacci step apart: the conductor sets `points:<higher value>` and asks the owner to approve with `factory:ready`; further apart, or fewer than two `estimators` configured: `needs:estimate`, and the owner sets the points. Only a comment that starts with `Estimate:` counts (bold is fine; a quoted `> Estimate:` or a heading is not a vote). Once the ticket has a `points:` label the poker ends; conflicting or invalid point labels get `needs:points` instead of another round. The criteria: the foundation's `work-tracking/estimation.md`.
- **Points:** every `factory:ready` ticket carries exactly one `points:<n>` label, its complexity in Fibonacci points (1, 2, 3, 5, 8, 13, 21) – how hard it is to do, not how long the ticket is. The owner approves it with the ticket. Without valid points the conductor sets `needs:points` and nothing starts. **13 or 21 points are split, not implemented:** the conductor sets `next:split:<implementer>` with `level:<points>`; the agent writes child tickets of at most 8 points each (from the foundation's template, with points and reasoning, without `factory:ready`), lists them on the ticket and labels it `split:done`; the owner approves the children with `factory:ready` and closes the parent. An agent's open PR that escalates to 13 stops with `needs:split`.
- **Levels:** the implement label comes with `level:<n>` at the higher of the ticket's points and its timeout floor; a fix label with `level:<n>` by the open findings' severity, never below the escalation floor – only `[minor]` findings (or `[non-blocking]`, `[P3]`): 2, at least one `[major]` (or `[blocking]`, `[P1]`, `[P2]`, untagged): one Fibonacci step below the ticket, at least 2, at least one `[critical]` (or `[P0]`): the ticket's points. Each inline comment is one finding; a review body counts as one too when it carries a tag or the review has no inline comments (otherwise it is the review's summary). The pollers map the level to a model and an effort (`levels` in olympus-agents' `agents.json`).
- **Model and effort per level** (owner decision 2026-10-31; `levels` in olympus-agents' `agents.json`): 1–2 → low, 3–5 → medium, 8–13 → high (Codex: GPT-6.1 Sol, Claude: Opus); 21 → Codex: GPT-6 Astra, high; Claude: Opus, extra high. 13 and 21 only ever split.
- **Escalation:** CI red again after a fix round, the same judge rejecting two rounds in a row, or `complexity:underestimated` (set by the implementer) followed by a red CI or a rejection raise a floor to one Fibonacci step above the level of the round that produced the head. Fix rounds never run below the floor; at 13 the PR stops with `needs:split`. The floor and each round's level are kept in a state comment on the PR (`<!-- factory-state … -->`), so re-running never raises it twice. Only a state comment by the conductor's own identity (`github-actions[bot]`) with a valid state counts; any other is ignored.
- **Risk:** judge labels on a diff that touches build files, the Gradle wrapper or version catalog, database schemas or migrations, the manifest, `.github/`, security code (a path containing `security`, `crypto` or `auth`, but not `author`), or more than 20 files come with `risk:high`: the judges run at high effort.
- A round-limit pause (`needs:owner` alone) comes first. An owner approval request alongside judge or fix labels keeps complexity levels, risk and escalation active; `needs:split` can stop those tasks.
- The owner's PRs get no level, no `needs:split` and no state comment: a ticket he implements himself needs no points.

### Timeout evidence

`timeout_signals: true` advertises support for the poller's version-1 timeout
bridge (`olympus-agents/docs/factory-timeouts.md`, issue olympus-agents#33).
Only exactly one `timeout_signals: true` entry enables it; missing, false,
duplicate or malformed values leave it disabled without stopping routing.
The poller posts a structured comment under its own identity before adding
`complexity:timeout:<agent>`. For tickets, the existing issue-label event wakes
this conductor; PR markers are picked up by the 15-minute scheduled reconciliation.
Every poller waits while any reporter marker remains. The conductor removes
only markers in its captured label snapshot, after routing/state writes and
obsolete task-label removal. A concurrent new reporter's marker survives that
acknowledgment; one poller/run per agent prevents same-agent overlap.

For PRs with valid factory-ticket points, current-head reports from the PR
author (proofread/fix/update) or its eligible judges (review) raise the floor
from the actual run level. Review/proofread/update records must carry null,
which uses the level that produced the head, or the higher of points and the
initial implementation floor when no fix level was recorded. Fix records must
carry a numeric run level. Before a PR exists, a ticket
implementation timeout from its assigned implementer can raise its next level;
that floor follows the same implementer's linked PR. Repeated reports at one
level cannot step the floor repeatedly; a new attempt at a higher level can.
Wrong roles, stale heads, malformed comments and the wakeup label alone do not
escalate. Points, retry budgets and review/owner prerequisites remain intact;
floor 13 stops with `needs:split`, while `needs:owner` takes precedence.

Install this receiver before opting in. Older pollers ignore the new key, and
updated pollers keep their old behavior in repositories without the opt-in.
No workflow or Android application change is part of this timeout bridge.

## Flow

1. The owner writes or approves a ticket and labels it `factory:ready` (optionally `implementer:<name>`).
2. The conductor sets `next:implement:<implementer>`; the implementer opens a PR that starts with `Closes #<ticket>`.
3. The implementer proofreads it, then the two judges judge (`next:judge:*`), the implementer fixes (`next:fix:<implementer>`) once both have judged the head (red CI too) until both approve the head and CI is green.
4. `next:merge:<implementer>`: the implementer merges (no owner approval needed, owner decision 2026-10-28; workflow files stay with the owner, because the agents' Apps may not change them).
5. The ticket closes with the merge and gets `step:acceptance`; the owner accepts by adding `accepted`. A ticket closed without a merged PR gets no `step:acceptance`.

Removing `factory:ready` from an open ticket stops the factory there: the conductor removes its labels from the ticket and its PR.

A judge at the round limit → `needs:owner` and one comment; the agents pause on that PR until the owner decides (merges, closes, or changes the PR).

## Option for later: best of two

Not built (owner decision 2026-10-29). For hard or high-risk tickets, Codex and Claude could implement the same ticket independently; CI and tests run on both PRs, the judges pick the better one, the other PR is closed, and the winner goes through the normal review. Selection instead of letting the two discuss a merged solution: a discussion between two models settles on what sounds convincing, and a merged solution is a third, untested one. It doubles the cost and the runs, and needs a judge who implemented neither – with three agents only Hermes. Also usable in the pilot as a measurement: the same ticket, two implementers, compared directly.
