# Ticket draft index

All items are review drafts, not active issues. Points are provisional; no factory labels have been applied. Dependencies form a directed acyclic graph, with decision dependencies blocking only affected work.

## Decisions

| Draft | Provisional points | Dependencies |
|---|---:|---|
| [D01 — Settle profile defaults and selector boundaries](tickets/d01.md) | 2 | — |
| [D02 — Agree permission and explicit-exit behavior on supported Android versions](tickets/d02.md) | 3 | — |
| [D03 — Settle daily sensor and manual-edit edge cases](tickets/d03.md) | 3 | — |
| [D04 — Define duration and metric-update precedence](tickets/d04.md) | 2 | — |
| [D05 — Choose a real AI integration and request-failure contract](tickets/d05.md) | 3 | — |
| [D06 — Clarify AI session and output boundaries](tickets/d06.md) | 2 | D05 |
| [D07 — Set report aggregation and empty-day conventions](tickets/d07.md) | 2 | — |

## Milestone 1

| Draft | Provisional points | Dependencies |
|---|---:|---|
| [M1-01 — Choose the initial route from persisted onboarding state](tickets/m1-01.md) | 3 | — |
| [M1-02 — Navigate only after Start or Skip has saved successfully](tickets/m1-02.md) | 3 | D01, M1-01 |
| [M1-03 — Make picker edits and unit conversion transactional](tickets/m1-03.md) | 3 | D01 |
| [M1-04 — Correct profile field selection and dialog copy](tickets/m1-04.md) | 2 | — |
| [M1-05 — Prove profile state and open editors survive rotation](tickets/m1-05.md) | 3 | M1-03, M1-04 |
| [M1-06 — Verify wide profile dimensions and fix demonstrated mismatches](tickets/m1-06.md) | 2 | M1-04 |
| [M1-07 — Make activity-permission denial and relaunch routing deterministic](tickets/m1-07.md) | 3 | D02, M1-02 |
| [M1-08 — Allow optional background-access dismissal and retry](tickets/m1-08.md) | 3 | D02, M1-07 |
| [M1-09 — Enforce required prompt blocking on phone and wide layouts](tickets/m1-09.md) | 2 | M1-07, M1-08 |
| [M1-10 — Wire drawer actions and conditional background repair](tickets/m1-10.md) | 3 | M1-08 |
| [M1-11 — Persist the daily goal and expose it to Home](tickets/m1-11.md) | 3 | D01 |
| [M1-12 — Implement the Step Goal selection sheet](tickets/m1-12.md) | 3 | M1-10, M1-11 |
| [M1-13 — Reuse profile editing as Personal Settings](tickets/m1-13.md) | 3 | D01, M1-02, M1-03, M1-05, M1-06, M1-10 |
| [M1-14 — Implement explicit Exit confirmation and restart suppression intent](tickets/m1-14.md) | 3 | D02, M1-10 |
| [M1-15 — Record end-to-end milestone-1 acceptance evidence](tickets/m1-15.md) | 3 | M1-01, M1-02, M1-03, M1-04, M1-05, M1-06, M1-07, M1-08, M1-09, M1-10, M1-11, M1-12, M1-13, M1-14 |

## Milestone 2

| Draft | Provisional points | Dependencies |
|---|---:|---|
| [M2-01 — Store daily activity records and historical goal snapshots](tickets/m2-01.md) | 3 | D03, M1-11 |
| [M2-02 — Implement the cumulative-sensor daily reducer](tickets/m2-02.md) | 3 | D03, M2-01 |
| [M2-03 — Connect foreground sensor readings to Home](tickets/m2-03.md) | 3 | D02, M2-02 |
| [M2-04 — Add Pause and Resume without counting paused deltas](tickets/m2-04.md) | 3 | D03, M2-03 |
| [M2-05 — Build the nested date picker for manual editing](tickets/m2-05.md) | 3 | D03 |
| [M2-06 — Implement Edit Steps dialog and manual-save integration](tickets/m2-06.md) | 3 | M1-10, M2-02, M2-05 |
| [M2-07 — Implement Reset Today confirmation](tickets/m2-07.md) | 2 | M1-10, M2-02 |
| [M2-08 — Calculate distance and calorie estimates](tickets/m2-08.md) | 3 | M2-01 |
| [M2-09 — Track activity duration with the approved display rule](tickets/m2-09.md) | 3 | D04, M2-03, M2-04, M2-06 |
| [M2-10 — Schedule and render daily metric updates](tickets/m2-10.md) | 3 | D04, M2-08, M2-09 |
| [M2-11 — Query the rolling seven-day average and goal history](tickets/m2-11.md) | 3 | M2-01 |
| [M2-12 — Render Daily Average and seven goal indicators](tickets/m2-12.md) | 3 | M2-11, M2-10 |
| [M2-13 — Request notification permission without extra custom flow](tickets/m2-13.md) | 2 | D02 |
| [M2-14 — Render collapsed and expanded tracking notifications](tickets/m2-14.md) | 3 | M2-08, M2-13 |
| [M2-15 — Run permitted tracking in an app-owned foreground service](tickets/m2-15.md) | 5 | D02, M2-03, M2-04, M2-14 |
| [M2-16 — Connect background updates, pause and permission changes](tickets/m2-16.md) | 3 | M2-10, M2-15 |
| [M2-17 — Verify explicit Exit stops real background tracking](tickets/m2-17.md) | 3 | M1-14, M2-16 |
| [M2-18 — Record milestone-2 tracking acceptance evidence](tickets/m2-18.md) | 3 | M1-15, M2-06, M2-07, M2-12, M2-16, M2-17 |

## Milestone 3

| Draft | Provisional points | Dependencies |
|---|---:|---|
| [M3-01 — Expose observable network availability](tickets/m3-01.md) | 2 | — |
| [M3-02 — Implement the approved real AI transport boundary](tickets/m3-02.md) | 3 | D05 |
| [M3-03 — Generate and cache independent Home insights](tickets/m3-03.md) | 3 | D06, M2-12, M3-01, M3-02 |
| [M3-04 — Render Home insights and offline retry](tickets/m3-04.md) | 3 | M3-03 |
| [M3-05 — Model an ephemeral Coach session and automatic starter](tickets/m3-05.md) | 3 | D06, M2-10, M3-02 |
| [M3-06 — Send Coach messages through the real conversation adapter](tickets/m3-06.md) | 3 | M3-05 |
| [M3-07 — Build Coach message layout for phone and wide screens](tickets/m3-07.md) | 3 | M3-06 |
| [M3-08 — Build the expandable suggestions and multiline composer](tickets/m3-08.md) | 3 | M3-06 |
| [M3-09 — Reactively disable and restore offline Coach interaction](tickets/m3-09.md) | 2 | M3-01, M3-08 |
| [M3-10 — Connect Coach navigation and session disposal](tickets/m3-10.md) | 2 | M3-04, M3-05, M3-07, M3-09 |
| [M3-11 — Record milestone-3 real-API and offline acceptance evidence](tickets/m3-11.md) | 3 | M2-18, M3-10 |

## Milestone 4

| Draft | Provisional points | Dependencies |
|---|---:|---|
| [M4-01 — Query Monday-to-Sunday report ranges](tickets/m4-01.md) | 3 | D07, M2-01 |
| [M4-02 — Aggregate weekly totals and metric-specific averages](tickets/m4-02.md) | 3 | D07, M2-08, M2-09, M4-01 |
| [M4-03 — Project seven daily report items and statuses](tickets/m4-03.md) | 3 | D07, M4-01 |
| [M4-04 — Manage report metric and selected-week state](tickets/m4-04.md) | 3 | M4-02, M4-03 |
| [M4-05 — Render report summary and week selector](tickets/m4-05.md) | 3 | M4-04 |
| [M4-06 — Render read-only daily items and fixed metric tabs](tickets/m4-06.md) | 3 | M4-05 |
| [M4-07 — Apply the wide two-column report layout](tickets/m4-07.md) | 3 | M4-06 |
| [M4-08 — Open reports from the noninteractive step-card area](tickets/m4-08.md) | 2 | M4-06 |
| [M4-09 — Record milestone-4 report acceptance evidence](tickets/m4-09.md) | 3 | M3-11, M4-07, M4-08 |
