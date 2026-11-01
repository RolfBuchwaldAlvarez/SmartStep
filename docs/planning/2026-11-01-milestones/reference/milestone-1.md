> Frozen review context from Second Brain PR #193, commit `14a92d572ee5c67ec7b231fe66ab7a3f5d4ec08c`. That PR was unmerged at planning time. This local snapshot is for reviewing these drafts; maintain product requirements in the Second Brain, not in two places. [Extracted original PDF text](milestone-1-source.txt) is included for independent comparison; visual layout still requires the original PDF/Figma.

# SmartStep milestone 1

## Summary

Milestone 1 establishes initial launch, profile input, home/navigation and the permission/settings flows. These are acceptance requirements distilled from the owner's PDF, not assertions about what the app already implements. The dated starting point is `2026-11-01-smartstep-requirements-baseline` (see [review guide](../README.md)).

## Canonical state

### Launch and profile

| ID | Expected behavior / QA basis | PDF pages |
|---|---|---|
| SS-M1-01 | Splash uses a solid light-blue background without gradients and a centered minimal walking-person app logo. | 2 |
| SS-M1-02 | First launch shows profile setup after splash. Completing or skipping persists local profile/default data and completion so subsequent launches do not automatically repeat setup. DataStore, SharedPreferences or equivalent local storage is permitted. | 2–3 |
| SS-M1-03 | Onboarding has centered `My Profile`, top-right `Skip`, subtitle `This information helps calculate your activity more accurately`, and bottom `Start`. Skip applies defaults and continues; Start saves selected values, marks onboarding complete and continues. | 2–3 |
| SS-M1-04 | Gender, height and weight fields are vertically stacked in one container. Gender defaults to Female; options are Male/Female. Its anchored vertical dropdown highlights/checks the selection; choosing updates immediately and closes it. Height/weight fields open their pickers and show value plus unit. Profile-field defaults are 170 cm and 60 kg; see the conflicting picker defaults below. | 3 |
| SS-M1-05 | Configuration changes preserve selected profile values and any open dropdown or picker. Saved profile data is available for future activity calculations. | 4–5 |

### Height, weight and adaptive profile layout

| ID | Expected behavior / QA basis | PDF pages |
|---|---|---|
| SS-M1-06 | Height picker is a modal dialog over a dimmed background; outside taps cannot dismiss it. Header `Height`, subtitle `Used to calculate distance`. Metric selection is a vertical numeric column with a fixed central highlight; imperial has independently scrolling feet/inches columns with fixed indicators. Unit choices `cm`, `ft/in` highlight/check the active choice. | 4–5 |
| SS-M1-07 | Switching height units preserves the physical height, changing representation only. The picker section gives 175 cm / 5 ft 9 in defaults; close centimeter values can share an imperial representation and rounding differences of ±1 inch are allowed. Cancel discards draft edits; Ok commits and updates the profile field. Dialog/open selections survive configuration changes. | 4–5 |
| SS-M1-08 | Weight picker has title `Weight`, subtitle `Used to calculate calories`, units `kg`/`lbs`, one scrolling whole-number column and the height picker's interaction/confirmation behavior. Its section gives 65 kg / 143 lb defaults. Convert using `lbs = kg × 2.20462` and `kg = lbs ÷ 2.20462`, rounded to nearest whole number; minor rounding differences are allowed. | 5–6 |
| SS-M1-09 | Both pickers share one metric/imperial system. Switching either also changes the other's representation and recalculates its displayed units without changing the underlying physical measurement. | 6 |
| SS-M1-10 | At width ≥840 dp, center the profile subtitle/field block at fixed width 394 dp; Start is also 394 dp wide rather than stretched. Height/weight dialogs retain mobile size/appearance, centered over dimmed content. | 6 |

### Home and permissions

| ID | Expected behavior / QA basis | PDF pages |
|---|---|---|
| SS-M1-11 | Home follows onboarding. Its top bar has a left hamburger and centered `Smart Step`; hamburger opens the drawer. The step card shows today's large count, goal in the form `/6000 Steps`, and a horizontal count/goal progress bar updated from available data. Its sneaker-like accent is decorative, with no interaction. This milestone adds no further metrics or tracking controls. | 7 |
| SS-M1-12 | When home is first displayed, request required physical-activity/motion-sensor access through the real system dialog. Without it, step counting is unavailable. Custom explanation sheets must not replace or imitate system dialogs. | 7–8 |
| SS-M1-13 | First denial shows explanation sheet 1 with `Allow access`, requesting through the system dialog again. A second denial leads to sheet 2 with `Open settings`. If permission remains ungranted, counting stays unavailable and sheet 2 reappears each launch. Sheets 1/2 are not dismissible until required access is addressed. | 8 |
| SS-M1-14 | After physical-activity access is granted, explanation sheet 3 recommends optional background execution. Continue invokes `ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`. Denial must still allow app use, with possible background limitations; granting improves tracking continuity. | 8–9 |
| SS-M1-15 | At width ≥840 dp, permission explanations become centered modal dialogs on a dimmed background; sequence, conditions and blocking/nonblocking behavior remain the same. | 9 |

### Drawer, goal, settings and exit

| ID | Expected behavior / QA basis | PDF pages |
|---|---|---|
| SS-M1-16 | Drawer slides in from the left above content; swipe back, outside tap or item selection closes it. Default actions: Step Goal, Personal Settings, Exit. Without background access, prepend the higher-priority `Fix the “Stop Counting Steps” issue` action, opening the existing background explanation. Remove that action once access is granted. | 10 |
| SS-M1-17 | Step Goal opens a dimmed bottom sheet with centered title and a vertical scrolling selection from 1,000 to 40,000, fixed selection indicator, and saved goal preselected. Content can scroll if necessary. Save commits/closes/updates home; Cancel or closing without save discards draft changes. Choosing a number alone does not dismiss it. Open state and selection survive configuration changes. | 11 |
| SS-M1-18 | Personal Settings reuses onboarding fields/pickers and their interaction logic, but has no Skip or onboarding explanatory text; show `Personal Settings` instead. Entry is through the drawer. | 12 |
| SS-M1-19 | Exit opens a confirmation with a power-off-related icon and `The app will fully close and will not run in the background.` Ok explicitly ends app activity/background tracking; counting stops until relaunch, background processes must not automatically restart after that exit, and relaunch is a new session. | 12 |

## Context and constraints

- **Conflicting defaults:** p. 3 gives profile values 170 cm / 60 kg; pp. 4–5 give picker values 175 cm / 65 kg (5 ft 9 in / 143 lb). The PDF does not reconcile initial picker selection with the profile field. Do not silently overwrite a saved/current measurement with the dialog example. The owner must settle initial defaults before default-value acceptance is definitive.
- **Unspecified picker bounds:** no height/weight ranges, step-goal increment or explicit first saved goal is prescribed. `/6000 Steps` is the supplied home example; a numeric goal-default decision should identify whether it is normative.
- **Platform-sensitive requirements:** permission re-prompting/settings and explicit exit need verification against the app's target Android version. The specification is product intent, not proof that Android grants a universal "stop all processes" capability. Document any necessary owner-approved adaptation rather than quietly changing acceptance.
- **Settings completion:** the PDF says settings reuses onboarding logic but does not explicitly define its save-button label or return destination. Do not infer that it re-runs first-launch permission prompts.
- Apply shared visual/architecture constraints in `smartstep` (see [review guide](../README.md)). No extra QA requirement is inferred from a decorative screen element.

## Relationships

- `smartstep` (see [review guide](../README.md)) — entry point, source authority and QA traceability.
- `smartstep-milestone-2` (see [review guide](../README.md)) — extends this home, drawer and profile foundation.

## Sources

- Owner-supplied `SmartStep_Milestone1_Requirements.pdf`, 13 pages, received November 1, 2026. Requirements are on pp. 1–12; p. 13 lists learning resources. Source authority is the PDF itself; no separate source-record ID is assigned (`source_ids: []`).
- SHA-256: `b10ba94ffd417071009fcb9377d59120c82f0f079839f3f77a4e11c5d33fe5ed`.
- [Figma node linked by the PDF](https://www.figma.com/design/aTiGCCavPLtgZNGXcV23H6/Smart-Step?node-id=0-1); URL recovered from its link annotation, not the visually clipped URL text. Embedded screen examples are present in the PDF. Figma content/access was not verified.
