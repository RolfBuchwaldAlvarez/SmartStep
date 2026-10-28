# Factory conductor

This repository is a factory repository (`../factory.yml`, my-ai-second-brain#173): the agents' review pollers work here in label mode.

- `conductor.py` reads the state from GitHub and sets labels `next:<task>:<agent>`, `needs:owner` and `step:acceptance`; the agents act only on labels addressed to them. Its docstring lists the rules.
- `test_conductor.py`: `python3 -m unittest discover -s .github/factory`.
- `workflows/`: templates for `.github/workflows/`, which only the owner can change: `factory-conductor.yml` runs the conductor on every relevant event and every 15 minutes; `factory-tests.yml` runs the tests on PRs that change the factory files.

## Flow

1. The owner writes or approves a ticket and labels it `factory:ready`.
2. The conductor sets `next:implement:codex`; Codex opens a PR that starts with `Closes #<ticket>`.
3. Codex proofreads it, then Claude and Hermes judge (`next:judge:*`), Codex fixes (`next:fix:codex`) once both have judged the head (red CI too) until both approve the head and CI is green.
4. `next:merge:codex`: Codex merges (no owner approval needed, owner decision 2026-10-28; workflow files stay with the owner, because the agents' Apps may not change them).
5. The ticket closes with the merge and gets `step:acceptance`; the owner accepts by adding `accepted`. A ticket closed without a merged PR gets no `step:acceptance`.

Removing `factory:ready` from an open ticket stops the factory there: the conductor removes its labels from the ticket and its PR.

A judge at the round limit → `needs:owner` and one comment; the agents pause on that PR until the owner decides (merges, closes, or changes the PR).
