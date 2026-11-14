> Frozen review context from Second Brain PR #193, commit `14a92d572ee5c67ec7b231fe66ab7a3f5d4ec08c`. PR #193 merged on November 4, 2026 at `8f1704d159246adce6be39c0611c1866e06f47e9`; [merged requirement](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-3.md). This local snapshot is for reviewing these drafts; maintain product requirements in the Second Brain, not in two places. [Extracted original PDF text](milestone-3-source.txt) is included for independent comparison; visual layout still requires the original PDF/Figma.

# SmartStep milestone 3

## Summary

Milestone 3 adds real-API activity insights and a short-lived AI Coach conversation on top of [smartstep-milestone-2](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-2.md). Home insights are independent, history-free messages; chat is conversational but discarded when leaving its screen. The two AI behaviors have different output requirements.

## Canonical state

### Home insights

| ID | Expected behavior / QA basis | PDF pages |
|---|---|---|
| SS-M3-01 | Place an informational AI insights block below Daily Average; give concise analytical/motivational feedback from current activity. `More` opens AI Coach chat. | 2 |
| SS-M3-02 | Refresh on first app launch of the session, return from background, reaching the daily goal, or changing the daily goal, with home activation as described in the source. Do not regenerate for minor step changes or on a timer; otherwise reuse the existing insight. | 2 |
| SS-M3-03 | Use a real public LLM API; simulated AI behavior is prohibited. The source permits an API with a free tier and recommends Google Gemini, without selecting an exact provider/model as binding. | 2 |
| SS-M3-04 | Every home-insight request uses the same predefined structured context: today's steps, daily goal, completion percentage and time-of-day context. No additional/dynamic parameters are required. | 3 |
| SS-M3-05 | Return one short motivational/analytical message interpreting activity, without medical advice or repetition of raw numeric values. Do not ask questions, continue a conversation or rely on/store history for this block; each message is independent. See the conflicting numeric example below. | 3 |
| SS-M3-06 | On home activation without internet, send no API request, keep the block visible, show static connection information, hide More and show Try Again with refresh icon. Suggested message: `Connect to the internet to get AI insights`. Try Again checks connectivity; online regenerates/replaces and restores More, offline stays unchanged without an error. | 3–4 |

### AI Coach chat

| ID | Expected behavior / QA basis | PDF pages |
|---|---|---|
| SS-M3-07 | Chat top bar has centered `AI Coach` and left Back. Back returns home and removes the chat screen/state from the back stack. Reopening starts a fresh session, without restoring the prior conversation. | 4, 6 |
| SS-M3-08 | On opening, start with empty history and automatically generate a concise starter from a predefined prompt: greeting, personal fitness-coach introduction, brief current activity context and a short question asking how to help; no detailed recommendations. No user action is needed. | 4–6 |
| SS-M3-09 | Append sent/received messages immediately in chronological order. AI bubbles align left, user bubbles right. On mobile, AI bubbles use available width within horizontal padding; user bubbles fit short text and grow only to 75% of screen width before wrapping, not a fixed dp width. | 5 |
| SS-M3-10 | Below history, provide an expandable/collapsible Quick suggestions section with exactly three fixed buttons: `Recommend workout`, `Explain today’s trend`, `How to reach today’s goal?`. Selecting one immediately adds its corresponding prompt as a user message and triggers an AI response. | 5 |
| SS-M3-11 | Bottom input begins at one line, expands to at most five lines and then scrolls. Sending requires at least one non-whitespace character after trimming. | 6 |
| SS-M3-12 | Offline: input remains visible but disabled/unfocusable, opens no keyboard, uses `Online connection required`, includes an inline disabled/connection icon, and has a muted disabled send button. Observe system connectivity; restoration automatically re-enables input/default placeholder and send availability without refresh/navigation, still subject to nonblank-input validation. | 6 |

### Wide screens

| ID | Expected behavior / QA basis | PDF pages |
|---|---|---|
| SS-M3-13 | On wide screens, center message history in a max-600-dp container. AI bubbles may fill it; user bubbles fit content up to 400 dp. Preserve alignment and wrapping. | 7 |
| SS-M3-14 | Center Quick Suggestions, input and send area at fixed 400 dp width; retain mobile interaction and resizing behavior. | 7 |

## Context and constraints

- **Numeric-output conflict:** p. 2 gives the example `You are slightly behind today’s pace — 1.2k steps needed.`; p. 3 prohibits repeating raw numeric values. Retain the prohibition as written and flag the example conflict for the owner; do not claim the specification is internally consistent.
- **Connectivity vs failures:** offline UI is defined; API timeouts, quota/rate limiting, server errors, cancellation, duplicate sends and loading indicators are not. Decide these in a scoped ticket before treating any invented behavior as acceptance.
- **Starter while offline:** the document requires an automatic starter on entry but also an offline mode; it does not say whether to defer the starter until connectivity returns or show a particular placeholder.
- **Session definition:** chat state is discarded on leaving/back/reopening. Configuration-change retention, process death and the exact meaning of an app session for insight refresh are not fully defined.
- **Security and privacy:** this source does not choose API credential delivery, server/client integration or additional data-disclosure policy. Its real-API requirement does not authorize embedding provider secrets in an app or sending extra personal data. Keep such implementation decisions separate from this product specification.
- Shared visual/architecture rules: [smartstep](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep.md). A product test must exercise a real integration for acceptance of SS-M3-03; deterministic test doubles in isolated automated tests are a separate engineering concern.

## Relationships

- [smartstep](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep.md) — product scope, source authority and QA traceability.
- [smartstep-milestone-2](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-2.md) — activity context and metrics.
- [smartstep-milestone-4](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-4.md) — later weekly analytics.

## Sources

- Owner-supplied `SmartStep_Milestone3_Requirements.pdf`, 8 pages, received November 1, 2026. Page 1 defines goals/visual conventions; pp. 2–7 define behavior; p. 8 lists learning resources. Direct PDF authority; `source_ids: []` (no separate source record).
- SHA-256: `ffc4a265365b964132f0e23ba2fadc89e121274b25b17340737e8d2853be8127`.
- [Figma node linked by the PDF](https://www.figma.com/design/aTiGCCavPLtgZNGXcV23H6/Smart-Step?node-id=57-1002); exact annotation URL. Embedded screen examples are in the PDF; Figma content/access was not verified.
