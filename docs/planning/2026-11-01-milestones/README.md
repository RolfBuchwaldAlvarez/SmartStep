# SmartStep milestone gap review and ticket drafts

This is a **review package**, prepared November 1, 2026. It compares the owner-supplied milestone-1 specification with source commit `e4d62787f3368139243bd60df18932e2d2015ca1` and proposes small ticket drafts through milestone 4. It does not implement features, create active issues or authorize the factory to start work.

## Read in this order

1. [Milestone-1 source audit](milestone-1-audit.md): the 19 requirements, existing code and remaining gaps. Code presence is not a runtime pass.
2. [Milestone background](reference/README.md): four frozen requirement references, original PDF text extracts and selected rendered source pages. Reviewers can inspect the supplied specification without relying on a private chat attachment or unmerged Brain main content.
3. [Decision gates](decisions.md): unresolved defaults, Android behavior, tracking semantics, AI policy and reporting conventions.
4. [Ticket index](ticket-index.md): 7 decision drafts and 53 implementation/acceptance drafts (M1: 15, M2: 18, M3: 11, M4: 9).
5. [Coverage matrix](coverage.md): every one of the 65 milestone requirement IDs maps to implementation/decision drafts or an existing-code verification slice and integrated QA.

## Product progression and current code

| Product milestone | Outcome | Audited source baseline |
|---|---|---|
| 1 | Launch/onboarding, profile pickers, Home, permissions, drawer, goal, settings and Exit | Profile persistence and UI exist; routing/save ordering, optional permission dismissal, drawer/destination wiring and goal/settings/exit remain incomplete. Several lifecycle/layout behaviors need proof. |
| 2 | Real counting, edit/reset/pause, distance/kcal/time, rolling seven-day view and notification | No activity ledger, sensor listener, service, metrics or edit flow found in the source inventory. |
| 3 | Real-API insights and ephemeral Coach chat | No AI/network/Coach feature found. |
| 4 | Monday–Sunday reports with metric tabs and week navigation | No report route/query/UI found. |

These are **product** milestones. The existing GitHub "Factory pilot" milestone and issues #8–#11 cover factory readiness; they are not product milestone 1. This planning snapshot does not update their live state.

## Reviewer remit

- Read the actual source passages and the pinned code before approving the tickets. Brain PR [#193](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/pull/193) was unmerged at planning time; its frozen source commit is `14a92d572ee5c67ec7b231fe66ab7a3f5d4ec08c`. Do not assume the references already exist on Brain main.
- Challenge omissions, wrong source interpretations, excessive coupling, duplicate work, missing dependencies and acceptance criteria that cannot be demonstrated. An implementation ticket should deliver one bounded behavior; split if new information makes it larger than 8 points.
- Points are the drafter's **provisional** 2/3/5 estimates. Independent Codex/Claude planning poker and owner acceptance have not occurred. No issue gets `points:*`, `factory:estimate` or `factory:ready` from merging this documentation PR.
- A dependency is a completed prerequisite **or a stable reviewed contract** sufficient for parallel work with fakes. Integration/acceptance tickets still require the implemented prerequisites. A decision gate requires the owner's recorded answer, not an agent assumption.
- Source behavior remains binding; added error/overflow/cancellation examples are explicitly draft engineering acceptance proposals for review, not claims quoted from a PDF. These proposals can be revised before issue promotion.
- Do not mistake an acceptance-report ticket for implementing every missing feature at once. Each feature ticket includes its own regression tests; the final milestone ticket establishes cross-feature/device evidence and finds residual gaps.
- Do not replace the existing feature/MVI/Navigation 3/Koin/Room architecture simply because a PDF leaves architecture open. Existing app patterns and the Brain's Android standards apply; a new KMP core is outside this plan.
- Preserve ticket-wide judge independence. A judge that implemented any PR for a ticket must not judge it. Claude's poller is paused by owner context until November 4; never infer two eligible available judges for every author.

## Ticket promotion and ordering

1. Review this PR's background, gap analysis, decision gates, coverage and draft scopes before creating individual implementation issues.
2. Resolve D01/D02 for affected M1 work; unrelated M1 fixes can proceed after their own readiness approval. Implement dependency order from the index, then M1 acceptance. The first product ticket should fix **M1-01 initial-route selection** or **M1-02 awaited save/navigation**, subject to confirmed factory readiness and owner ticket approval; these are bounded failures already demonstrated by source.
3. Resolve D03/D04 and implement M2 storage/reducer contracts before sensor, edits, metrics and background integration. Service work needs D02's Android behavior matrix.
4. Resolve D05/D06 and external setup before M3 transport/insights/chat; no paid service or new infrastructure is provisioned by a ticket draft.
5. Resolve D07 before M4 aggregation and report acceptance. The ledger/query portions can use approved contracts/fakes before all AI UI work is complete, but full product milestone-4 acceptance follows milestone 3.
6. On issue promotion, use the foundation ticket template (Goal, Given/When/Then criteria, scope, exclusions and points), retain source IDs/dependencies and get owner approval. Do not publish all drafts as active ready work in one bulk step.

Existing factory prerequisites remain separate: activated detekt (#8 / merged #12's template), conductor judge/metrics work (#9), SmartStep AGENTS/foundation pin (#10), foundation restructuring/release and first-pilot approval (#11). This PR does not install workflows, change rulesets or claim those prerequisites complete.

## Evidence and limits

- All app source paths, resources, manifest, profile persistence and test files were inspected at the pinned commit. [Code entry points](evidence-index.md) link to that exact SHA.
- No Gradle, Android build, emulator, sensor, permission interaction or live AI call was run during planning. Android builds remain CI-only on current olympus limits. A green prior build is not evidence that these product interactions pass.
- Only template arithmetic/package-name tests exist in app test directories; Python factory tests test the conductor, not SmartStep product behavior.
- Selected PDF pages are rendered as review evidence, not screenshots of the implemented app. Exact Figma URLs and PDF fingerprints are preserved. Figma access/current contents are unverified.
- Product specification maintenance belongs in the Second Brain. These dated, frozen extracts let reviewers assess this planning PR; do not evolve them into a competing live requirements store.

## Validation of this package

Before handover, check local Markdown destinations, unique ticket/requirement IDs, all 65 requirements covered, no unknown/cyclic dependencies, no points above 8, and all ticket drafts carrying source/background, scope, criteria and QA. These are documentation integrity checks; they do not establish runtime acceptance.
