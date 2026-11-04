> Frozen review context from Second Brain PR #193, commit `14a92d572ee5c67ec7b231fe66ab7a3f5d4ec08c`. PR #193 merged on November 4, 2026 at `8f1704d159246adce6be39c0611c1866e06f47e9`; [merged requirement](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-4.md). This local snapshot is for reviewing these drafts; maintain product requirements in the Second Brain, not in two places. [Extracted original PDF text](milestone-4-source.txt) is included for independent comparison; visual layout still requires the original PDF/Figma.

# SmartStep milestone 4

## Summary

Milestone 4 adds a read-only weekly activity report with week navigation and Steps/Calories/Time/Distance tabs. It builds on the prior milestones, with Monday-to-Sunday aggregation distinct from milestone 2's rolling seven-day home view.

## Canonical state

| ID | Expected behavior / QA basis | PDF pages |
|---|---|---|
| SS-M4-01 | Home step card gains a right-side `Report` label, top-aligned with the main step value. The label is informational, with no independent interactive state. Tapping any noninteractive card area opens the report; Edit and Pause/Resume keep their own actions. | 2 |
| SS-M4-02 | Report displays one active metric at a time: Steps, Calories, Time or Distance. Summary and day list always correspond to the same selected metric/week. Top bar has centered `Report` and left Back; Back returns home and removes report/state from the stack. | 2–3 |
| SS-M4-03 | Top summary shows the active metric name, selected week's total, and `Daily average: X` with its unit. The PDF labels these Steps/Calories/Minutes/Kilometers and steps/kcal/min/km. Metric changes update title, formatting, total and average immediately. See unspecified units/rounding below. | 3 |
| SS-M4-04 | Week selector below summary has previous arrow, date range such as `Nov 16 – Nov 22`, and next arrow. Default to current calendar week; previous moves back a week, next moves forward only if that week has started, otherwise it is disabled. | 3–4 |
| SS-M4-05 | Weeks are always Monday through Sunday, seven consecutive dates, independent of installation/start date. Starting mid-week does not shorten the date range; earlier dates may have no data. | 4 |
| SS-M4-06 | Switching week refreshes summary and day list for that range while preserving active metric. Switching metric preserves selected week. | 4, 6 |
| SS-M4-07 | Daily breakdown has exactly seven noninteractive items ordered Monday–Sunday. Each shows day name, active metric value/unit and top-right status icon. | 4–5 |
| SS-M4-08 | Status icons: check for completed past days with data; clock for today in the current week; minus for inactive days with no data. Highlight today if it belongs to the selected week. See today's no-data precedence below. | 4–5 |
| SS-M4-09 | Show `Goal: 6000 steps`-style goal text only for Steps, not other metrics. Preserve milestone 2's rule that later goal changes do not recalculate historical goal progress. | 5; milestone 2 p. 7 |
| SS-M4-10 | A day with no available data, including future days or days before installation, displays primary value 0, `No data` and muted styling. Apply No data consistently across all metrics. | 5 |
| SS-M4-11 | Fixed bottom metric tabs each have icon and label; exactly one is highlighted/active. Selecting a tab updates content in place rather than navigating to another screen. Steps is the default when the report is first opened. | 5–6 |
| SS-M4-12 | Only the day list scrolls. Summary, week selector and bottom tabs remain visible/static; tabs stay fixed at the bottom. | 4, 6 |
| SS-M4-13 | At width ≥840 dp, center summary, week selector and bottom tabs, each at fixed width 394 dp. Preserve vertical hierarchy and behavior. | 6–7 |
| SS-M4-14 | Wide daily list uses two columns inside a centered max-600-dp container, retaining each item's states/visuals. Only this list scrolls. | 7 |

## Context and constraints

- **Average denominator:** totals and daily average are required, but this PDF does not state whether an incomplete current week's average divides by seven, elapsed days or days with data. Do not borrow milestone 2's explicit seven-day home denominator without identifying that as an assumption requiring a decision.
- **Imperial distance:** this PDF names Kilometers/km, while milestone 2 requires miles for imperial users. Whether weekly reports follow the user's measurement system is not reconciled here.
- **Precision:** detailed report rounding/formatting rules for totals, averages and durations are not specified beyond metric labels/units. Reuse decisions only when justified, not as if quoted from this PDF.
- **Today with no data:** the clock rule for today and minus/no-data rule overlap. Resolve icon/highlight precedence when a ticket needs that case. Recorded zero activity and absence of a record should not be silently equated.
- **Recreation vs reopening:** Back discards report state; the source does not explicitly settle rotation/process-death restoration or say which tab to restore after reopening beyond the default Steps statement.
- No bounds for earliest historical week, cross-year date-label format, or live report update while remaining on-screen are specified.
- Shared visual/source/architecture conventions are in [smartstep](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep.md).

## Relationships

- [smartstep](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep.md) — product entry point and QA traceability.
- [smartstep-milestone-2](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-2.md) — metrics, historical goals and rolling home averages.
- [smartstep-milestone-3](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-3.md) — preceding AI milestone; report behavior remains a distinct feature.

## Sources

- Owner-supplied `SmartStep_Milestone4_Requirements.pdf`, 8 pages, received November 1, 2026. Page 1 defines goals/visual conventions; pp. 2–7 define behavior; p. 8 lists learning resources. Direct PDF authority; `source_ids: []` (no separate source record).
- SHA-256: `cab5eccc3c1c8c13df85382c102c6a892284b13861bf6b92e48c9e945acd42c7`.
- [Figma node linked by the PDF](https://www.figma.com/design/aTiGCCavPLtgZNGXcV23H6/Smart-Step?node-id=67-2165); exact annotation URL. PDF includes screen examples; Figma content/access was not verified.
