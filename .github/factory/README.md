# Factory conductor

This repository is a factory repository (`../factory.yml`, my-ai-second-brain#173): the agents' review pollers work here in label mode.

- `conductor.py` reads the state from GitHub and sets labels `next:<task>:<agent>`, `needs:owner` and `step:acceptance`; the agents act only on labels addressed to them. Its docstring lists the rules.
- `test_conductor.py`: `python3 -m unittest discover -s .github/factory`.
- The workflows, which only the owner can change: `factory-conductor.yml` runs the conductor on every relevant event and every 15 minutes; `factory-tests.yml` runs the tests on PRs that change the factory files. They were drafted in `workflows/` here; the owner moved them to `.github/workflows/` in #3.

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

**CI for the merge:** `required_checks` in `../factory.yml` names the checks that count; a PR without them stays pending. The conductor's own `conduct` job never counts. Until the Android CI workflow exists (build, unit tests, lint), no ticket gets `factory:ready`.

PRs by the owner get no proofread; updating, fixing and merging them stays with him – the conductor only asks the judges.

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
