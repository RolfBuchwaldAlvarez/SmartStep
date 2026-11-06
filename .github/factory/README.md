# Factory conductor

This repository is a factory repository (`../factory.yml`, my-ai-second-brain#173): the agents' review pollers work here in label mode.

- `conductor.py` reads the state from GitHub and sets labels `next:<task>:<agent>`, `needs:owner` and `step:acceptance`; the agents act only on labels addressed to them. Its docstring lists the rules.
- `test_conductor.py`: `python3 -m unittest discover -s .github/factory`.
- The workflows in `.github/workflows/`, which only the owner can change: `factory-conductor.yml` runs the conductor on every relevant event, when a CI run finishes (`workflow_run`; `check_suite` never fires for checks created by GitHub Actions) and every 15 minutes; `factory-tests.yml` runs the conductor's tests on PRs that change the factory files; `android-ci.yml` builds the app and runs the unit tests, Android Lint and ktlint on every PR and on `main`. New drafts for the owner go into `workflows/` here.

## Who implements and who judges

Set in `../factory.yml` (owner decision 2026-10-29):

- `implementers: codex, claude` – Codex by default; a ticket label `implementer:claude` lets Claude implement it, `implementer:owner` means the owner implements it himself.
- `judges: claude, hermes, codex` with `judges_per_pr: 2` – a PR's judges are the first two of that list other than its author, so nobody judges their own PR and there are always two judges from other model families:

| Author | Judges |
|---|---|
| Codex | Claude, Hermes |
| Claude | Hermes, Codex |
| the owner | Claude, Hermes |

A PR without a ticket (for example the owner's workflow PRs, or changes to the factory itself) is judged the same way.

**CI for the merge:** `required_checks` in `../factory.yml` names the checks that count; a PR without them stays pending. The conductor's own `conduct` job never counts. It names `android-ci`, so no PR merges without a green Android build.

PRs by the owner get no proofread; updating, fixing and merging them stays with him – the conductor only asks the judges.

## Complexity routing

`routing.py`, concept in olympus-agents `docs/complexity-routing.md` (reviewed by Codex and Hermes, olympus-agents#29):

- **Planning poker** (owner decision 2026-10-31; the ticket check: owner decision 2026-11-06): a ticket drafted without points gets the label `factory:estimate`. The conductor asks the first two of `estimators` (`factory.yml`: Codex, Claude, Hermes) other than the ticket's drafter – its author – with `next:estimate:<agent>`; each reads the ticket and the code and posts one comment without reading the other's: a line `Estimate: <n> – <one sentence naming the criteria>` and a part `Ticket findings:` with `none` or one finding per line, each a category (`UNTESTABLE_CRITERION`, `SCOPE_TOO_BROAD`, `MISSING_DEPENDENCY`, `CONTRADICTS_SPEC`, `UNCLEAR`) with its detail. Only a comment with both parts is a vote, starting with `Estimate:` (bold is fine; a quoted `> Estimate:` or a heading is not); a finding without a detail does not count. **Findings from either:** no points, also when the estimates differ; `next:revise:<drafter>`. The drafter edits the ticket and answers every finding in a comment starting with `Revised:`, which starts a new round: only votes after it count, and a finding that comes back counts again. After `max_rounds` rounds with findings, or on a ticket the owner drafted: `needs:owner` (the owner sets the points, or revises and posts `Revised:` himself, which starts a new round on any ticket; findings in it come straight back to him, because the limit stays reached). **No findings:** at most one Fibonacci step apart, the conductor sets `points:<higher value>` and asks the owner to approve with `factory:ready`; further apart, or fewer than two estimators: `needs:estimate`, and the owner sets the points. Once the ticket has a `points:` label the poker ends; conflicting or invalid point labels get `needs:points` instead of another round. The criteria: the foundation's `work-tracking/estimation.md`.
- **Points:** every `factory:ready` ticket carries exactly one `points:<n>` label, its complexity in Fibonacci points (1, 2, 3, 5, 8, 13, 21) – how hard it is to do, not how long the ticket is. The owner approves it with the ticket. Without valid points the conductor sets `needs:points` and nothing starts. **13 or 21 points are split, not implemented:** the conductor sets `next:split:<implementer>` with `level:<points>`; the agent writes child tickets of at most 8 points each (from the foundation's template, with points and reasoning, without `factory:ready`), lists them on the ticket and labels it `split:done`; the owner approves the children with `factory:ready` and closes the parent. An agent's open PR that escalates to 13 stops with `needs:split`.
- **Levels:** the implement label comes with `level:<n>` at the higher of the ticket's points and its timeout floor; a fix label with `level:<n>` by the open findings' severity, never below the escalation floor – only `[minor]` findings (or `[non-blocking]`, `[P3]`): 2, at least one `[major]` (or `[blocking]`, `[P1]`, `[P2]`, untagged): one Fibonacci step below the ticket, at least 2, at least one `[critical]` (or `[P0]`): the ticket's points. Each inline comment is one finding; a review body counts as one too when it carries a tag or the review has no inline comments (otherwise it is the review's summary). The pollers map the level to a model and an effort (`levels` in olympus-agents' `agents.json`).
- **Model and effort per level** (owner decision 2026-10-31; `levels` in olympus-agents' `agents.json`): 1–2 → low, 3–5 → medium, 8–13 → high (Codex: GPT-6.1 Sol, Claude: Opus); 21 → Codex: GPT-6 Astra, high; Claude: Opus, extra high. 13 and 21 only ever split.
- **Escalation:** CI red again after a fix round, the same judge rejecting two rounds in a row, or `complexity:underestimated` (set by the implementer) followed by a red CI or a rejection raise a floor to one Fibonacci step above the level of the round that produced the head. Fix rounds never run below the floor; at 13 the PR stops with `needs:split`. The floor and each round's level are kept in a state comment on the PR (`<!-- factory-state … -->`), so re-running never raises it twice. Only a state comment by the conductor's own identity (`github-actions[bot]`) with a valid state counts; any other is ignored.
- **Risk:** judge labels on a diff that touches build files, the Gradle wrapper or version catalog, database schemas or migrations, the manifest, `.github/`, security code (a path containing `security`, `crypto` or `auth`, but not `author`), or more than 20 files come with `risk:high`: the judges run at high effort.
- The pipeline's round limits and `needs:owner` come first; escalation only sets the level of a round they still allow, and `needs:split` never replaces `needs:owner`.
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

## Ticket metrics

Q8 in issue #9 calls for per-ticket evidence that Codify can read from closed PRs. The conductor recomputes one versioned `<!-- factory-metrics … -->` state comment on **each recognized PR linked to a `factory:ready` ticket**, including closed attempts. Every copy contains the same aggregate across that ticket's recognized PRs. This is a projection of GitHub evidence, not a maintained incrementing counter. The routing `factory-state` comment remains separate and unchanged; metrics never decide labels, eligibility, escalation or merge permission.

| Field | Definition |
|---|---|
| `version` | Metric format version, currently 1 |
| `ticket`, `pull_requests`, `open_pull_requests` | Ticket number and source PR numbers; linkage uses the existing first local closing reference in the PR body |
| `points` | Ticket's current valid estimate, or null; changing an estimate changes this projection |
| `levels_recorded` | Distinct levels recorded against produced heads in trusted routing state; these do not include an unobserved initial implementation level or measure actual model execution |
| `review_rounds` | Distinct real formal review IDs by configured eligible judges, excluding author proofreads and empty thread replies; includes approvals and dismissed reviews |
| `findings` | Counts by minor/major/critical, following the same `routing.review_findings` and severity-tag conventions used for fix routing; approvals and dismissed reviews add no findings |
| `ci_failures` | Distinct check-run IDs with failure, timed_out, action_required or startup_failure, excluding the conductor's own `conduct` job; a successful retry does not erase the failed run |
| `duration_seconds` | Elapsed wall time from the earliest linked PR creation to the latest PR closure, null while any attempt is open or source timestamps are missing |

Judge eligibility for this projection excludes every recognized author of an attempt for the ticket, then takes the configured number of remaining distinct judges. Review rounds count formal review submissions, not fix rounds, number of commits, or AI calls. A tagged body and its inline findings follow the existing routing convention; this does not establish semantic independence or correctness of reported findings. Duration excludes the time before the first PR and is neither compute time nor billable time. No cost or model-quality ranking is inferred.

All API lists use the existing pagination helper. CI evidence covers retained PR commits, the current head and eligible review heads; checks on force-pushed commits with no remaining reference can be absent. Before finalization, deleted/edited reviews can change the projection. Changed PR closing references and removed `factory:ready` labels can change or stop it. Existing comments remain historical snapshots when the ticket leaves the factory; they are not a permanent ledger. Missing required evidence stops publication for that ticket instead of writing a partial count. Source fetches finish before any of that ticket's metric comments are written; publication itself is not atomic across PRs, and the next reconciliation converges after a write failure.

Only matching comments by `github-actions[bot]` are updated; other users' comments are ignored. Open snapshots have null duration, so clock advancement alone causes no writes. Once the ticket and all its attempts are closed and all observed non-conductor checks have completed, the conductor writes a trusted `<!-- factory-metrics-final … -->` checkpoint on the ticket, **after** publishing every PR copy. Failed publication leaves no matching checkpoint and is retried.

For finalized tickets, subsequent metrics runs read only the paginated PR inventory and the ticket's comments, skipping all per-attempt comments, reviews, inline findings, commits and checks. The inventory still grows with repository history, and there is one checkpoint-comment list per closed ticket; detailed evidence calls no longer grow with the accumulated commits and reviews of delivered tickets. A changed estimate, judge configuration, attempt set, author, body, head, or closure timestamp invalidates the checkpoint; an open ticket or attempt bypasses it. Repository metadata and comment edit timestamps are deliberately excluded from the signature, so the conductor's own writes cannot invalidate it.

Finalization is a snapshot boundary: reviews edited or submitted and CI reruns started after finalization are not automatically incorporated unless the inventory signature changes. Delete the conductor's checkpoint comment on the ticket to request a full refresh of historical evidence. Duration remains the earliest creation to latest closure after every attempt closes. Metrics never add routing labels. This change adds no workflow and deploys no agent runtime.
