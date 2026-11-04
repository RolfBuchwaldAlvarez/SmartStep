# Product decision gates

These are unresolved specification questions, not newly adopted product decisions. Each gate has a small [draft decision ticket](ticket-index.md), with acceptance requiring the owner's recorded answer. A dependent ticket must not be promoted on an unspoken assumption. Unrelated work can continue using a reviewed interface/contract.

| Gate | Source ambiguity / missing decision | Affected work |
|---|---|---|
| [D01](tickets/d01.md) | M1 p. 3 gives 170 cm/60 kg; picker sections pp. 4–5 give 175 cm/65 kg. Picker bounds, goal increment/default, unit-system Cancel scope and settings save/return behavior are unspecified. | Profile defaults/conversions, settings and goal selector. |
| [D02](tickets/d02.md) | Required denial counts/settings vs actual Android rules; optional battery exemption vs notification permission; unavailable sensor; Exit's full-process wording vs supported stop/suppression. | Permission flows and background/Exit behavior. |
| [D03](tickets/d03.md) | M2 calls editing today-only but provides a date picker. Historical edits must not unexpectedly replace today's sensor baseline; sensor reset, paused deltas, rollover and time-zone semantics need examples. | Daily ledger, reducer, sensor, edits/reset/pause. |
| [D04](tickets/d04.md) | Duration below one minute = zero vs nearest-minute rounding; activity-gap threshold/manual-edit time; metrics frozen during pause vs mandatory edit/reset recalculation. | Duration and metric update policy. |
| [D05](tickets/d05.md) | Real AI is mandatory but provider/model, credential architecture, HTTP/quota/error policy and external setup are not selected. | Real transport and live acceptance. |
| [D06](tickets/d06.md) | Numeric example conflicts with no-raw-numbers output rule. Session boundaries, offline starter, quick suggestions offline and concurrent sends are incomplete. | Insight triggers and ephemeral chat. |
| [D07](tickets/d07.md) | Whether past distance/kcal use the profile from that day or the current profile (including same-day edits and required stored inputs/metrics); report denominator, imperial distance, today-with-no-data status precedence, rounding and reopening/recreation behavior are not settled. | M2 ledger schema and metrics, weekly aggregation, report state and QA. |

The PDF introductory "up to 840 dp" wording overlaps explicit wide-screen ≥840-dp sections. Draft layout tests use the explicit ≥840-dp rule (839 narrow / 840 wide); reviewers should reject a different hidden boundary.

Settings save/return behavior is covered by D01 and is an explicit gate for M1-13. This is intentionally not an excuse to implement a second onboarding flow. The selected source passages and their full page text are in [reference](reference/README.md).
