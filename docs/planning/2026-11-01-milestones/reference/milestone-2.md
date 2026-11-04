> Frozen review context from Second Brain PR #193, commit `14a92d572ee5c67ec7b231fe66ab7a3f5d4ec08c`. PR #193 merged on November 4, 2026 at `8f1704d159246adce6be39c0611c1866e06f47e9`; [merged requirement](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-2.md). This local snapshot is for reviewing these drafts; maintain product requirements in the Second Brain, not in two places. [Extracted original PDF text](milestone-2-source.txt) is included for independent comparison; visual layout still requires the original PDF/Figma.

# SmartStep milestone 2

## Summary

Milestone 2 extends [smartstep-milestone-1](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-1.md) with real tracking controls, editable counts, calculated metrics, seven-day insights and a foreground notification. Requirements below preserve the supplied calculation and update rules; they do not claim completed tracking behavior.

## Canonical state

### Editing, baselines and pause

| ID | Expected behavior / QA basis | PDF pages |
|---|---|---|
| SS-M2-01 | Keep the milestone-1 drawer and add Edit Steps and Reset Today's Steps. The edit action is also available through a new edit icon in the home step card. | 2, 4 |
| SS-M2-02 | Edit dialog title `Edit steps`, subtitle `Calories, distance & duration will be recalculated accordingly`, Date and Steps fields, Cancel and Save. Date displays `YYYY/MM/DD` and is selected only through a nested date dialog. Cancel discards changes; Save stores the date/count, closes and updates corresponding activity data. | 2–3 |
| SS-M2-03 | Date picker overlays rather than closes Edit Steps. Year, Month and Day scroll independently through a fixed central selection area. Cancel returns without changing the previous date; Save returns and updates the date field. Steps opens a numeric keyboard and accepts digits only, no letters, symbols or decimals. | 2–3 |
| SS-M2-04 | A manual edit stores the edited daily count and separately records the sensor reading at edit time as the new sensor baseline. Subsequent readings contribute only newly detected steps; sensor updates must not overwrite the manually set total. | 3 |
| SS-M2-05 | At a new day or first launch of the day, store the cumulative sensor reading as baseline; daily count is `currentSensorValue − baseline`. Reset Today's Steps opens `Are you sure you want to reset today’s steps?` with Cancel/Reset. Reset stores a new baseline, displays zero and refreshes home; Cancel changes nothing. | 3–4 |
| SS-M2-06 | Pause/Resume control reflects the current state. While paused, show Play, dim the count and replace the usual goal label with `Paused`; do not increase steps or record new activity until resumed. | 4–5 |

### Metrics and weekly insights

| ID | Expected behavior / QA basis | PDF pages |
|---|---|---|
| SS-M2-07 | Below the card, informational, noninteractive Distance/Calories/Time metrics each show an icon, value and unit. | 5–6 |
| SS-M2-08 | Convert height to cm; approximate step length as `height(cm) × 0.415`; distance(m) = `steps × stepLength(cm) / 100`. Display km in metric (`m / 1000`) or miles in imperial (`m / 1609.3`), including fractional values, rounded to one decimal. | 5 |
| SS-M2-09 | Convert weight to kg; `kcalPerStep = weight(kg) × 0.0005 × genderFactor`; calories = `steps × kcalPerStep`. Male factor 1.0, female factor 0.9. Display whole kcal. These are approximate informational estimates, not medical-grade measurements. | 5–6 |
| SS-M2-10 | Activity duration is based on periods of active step detection, stored internally in seconds and displayed only as minutes. Less than a minute displays `0 min`; the PDF otherwise says nearest whole minute. See ambiguity below. | 6 |
| SS-M2-11 | Recalculate metrics when steps increase by a batch of at least 10, on manual edit, on reset, or on foreground return with updated step data; not on every step. While paused, all metric values stay frozen until resumed. | 6 |
| SS-M2-12 | `Daily Average: X steps` is the arithmetic mean over the last seven calendar days including today, always including zero-activity days in the seven-day denominator. | 7 |
| SS-M2-13 | Show seven consecutive days chronologically, today rightmost. Each has a circular goal indicator, short weekday and exact daily step count. Progress starts at 12 o'clock, fills clockwise and is capped at 100%; absent activity displays zero with empty progress. | 7 |
| SS-M2-14 | Goal changes apply only to today and future days. Past days' goal progress is not recalculated using a newly changed goal. | 7 |

### Background behavior and notification

| ID | Expected behavior / QA basis | PDF pages |
|---|---|---|
| SS-M2-15 | While background tracking is allowed and actively running, show its system notification even if the UI closes. Without background access, do not start the background service or display its notification; count only in the foreground. | 8 |
| SS-M2-16 | Collapsed notification shows app icon, steps, calculated calories and horizontal progress. It updates silently without sound/vibration or additional attention. It can be swiped away and may reappear when new step data arrives. | 8 |
| SS-M2-17 | Expanded notification additionally shows app name and system last-update time (e.g. `now`, `2m`); a chevron is decorative. Tapping either notification state opens the app. Steps/calories update silently while tracking runs. | 8 |
| SS-M2-18 | For target API 33+, the source requests `POST_NOTIFICATIONS` through the standard system dialog; it requires no additional custom explanation flow. | 9 |

## Context and constraints

- **Date scope:** p. 2 frames Edit Steps as editing today, but pp. 2–3 let the user select another date. Allowed historical/future dates, validation limits and application of a live sensor baseline to a historical edit are unspecified. Preserve both statements and resolve date scope before implementing that acceptance path.
- **Duration ambiguity:** p. 6 requires all durations below one minute to show zero and also nearest-minute rounding. At 30–59 seconds those differ. Manual editing promises duration recalculation, but no step-to-duration formula is supplied; do not invent one.
- **Pause and sensor restart:** the source requires no accumulation during pause, but does not prescribe resume-baseline, device-reboot/counter-reset, time-zone or missed-midnight algorithms. Those need engineering decisions and ticket-specific acceptance tests, not claims that the PDF already settled them.
- **Frozen metrics vs edits:** the PDF both mandates immediate recalculation for edits/resets and freezes all metrics while paused. Precedence for an edit/reset during pause is not specified.
- **Notifications/platform:** the text calls the notification persistent while also allowing swipe dismissal; preserve both observed behaviors for platform-aware QA. The PDF's notification-permission wording is a specification statement, not a fresh verification of Android foreground-service rules.
- Shared visual breakpoint/icon rules are in [smartstep](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep.md). This PDF does not give additional milestone-2-specific wide-layout dimensions.

## Relationships

- [smartstep](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep.md) — entry point and QA/source rules.
- [smartstep-milestone-1](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-1.md) — prerequisite UI/profile/permission behavior.
- [smartstep-milestone-3](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-3.md), [smartstep-milestone-4](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-4.md) — consumers of tracking and metric data.

## Sources

- Owner-supplied `SmartStep_Milestone2_Requirements.pdf`, 9 pages, received November 1, 2026. Page 1 defines goals/visual conventions; pp. 2–8 define behavior; p. 9 adds the Android 13+ note and learning resources. Source authority is the PDF; `source_ids: []` (no separate source record).
- SHA-256: `a6fc36716e8c9900c34398d0ee7cb6b595afee2645bf8749848b4a7e2c53c2fc`.
- [Figma node linked by the PDF](https://www.figma.com/design/aTiGCCavPLtgZNGXcV23H6/Smart-Step?node-id=27-650); exact link annotation, not the clipped visible URL. PDF includes screen examples; Figma content/access was not verified.
