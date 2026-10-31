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

- **Points:** every `factory:ready` ticket carries exactly one `points:<n>` label, its complexity in Fibonacci points (1, 2, 3, 5, 8, 13, 21) – how hard it is to do, not how long the ticket is. The owner approves it with the ticket. Without valid points the conductor sets `needs:points` and nothing starts; 13 or more gets `needs:split`, on the ticket and on an agent's open PR for it.
- **Levels:** the implement label comes with `level:<points>`; a fix label with `level:<n>` by the open findings' severity – only `[minor]` findings (or `[non-blocking]`, `[P3]`): 2, at least one `[major]` (or `[blocking]`, `[P1]`, `[P2]`, untagged): one Fibonacci step below the ticket, at least 2, at least one `[critical]` (or `[P0]`): the ticket's points. Each inline comment is one finding; a review body counts as one too when it carries a tag or the review has no inline comments (otherwise it is the review's summary). The pollers map the level to a model and an effort (`levels` in olympus-agents' `agents.json`).
- **Escalation:** CI red again after a fix round, the same judge rejecting two rounds in a row, or `complexity:underestimated` (set by the implementer) followed by a red CI or a rejection raise a floor to one Fibonacci step above the level of the round that produced the head. Fix rounds never run below the floor; at 13 the PR stops with `needs:split`. The floor and each round's level are kept in a state comment on the PR (`<!-- factory-state … -->`), so re-running never raises it twice. Only a state comment by the conductor's own identity (`github-actions[bot]`) with a valid state counts; any other is ignored.
- **Risk:** judge labels on a diff that touches build files, the Gradle wrapper or version catalog, database schemas or migrations, the manifest, `.github/`, security code (a path containing `security`, `crypto` or `auth`, but not `author`), or more than 20 files come with `risk:high`: the judges run at high effort.
- The pipeline's round limits and `needs:owner` come first; escalation only sets the level of a round they still allow, and `needs:split` never replaces `needs:owner`.
- The owner's PRs get no level, no `needs:split` and no state comment: a ticket he implements himself needs no points.

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
