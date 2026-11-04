# Milestone source background for reviewers

The owner supplied all four PDFs on November 1, 2026 and reported milestone 1 unfinished. These extracts/snapshots are frozen evidence for this dated planning PR, not a new live requirements home. The Second Brain requirements PR is [#193 at 14a92d5](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/tree/14a92d572ee5c67ec7b231fe66ab7a3f5d4ec08c/20-contexts/ventures/projects/smartstep). [PR #193](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/pull/193) merged on November 4, 2026 at `8f1704d159246adce6be39c0611c1866e06f47e9`. The local requirement copies remain evidence of the original planning snapshot; maintain requirements in the Brain.

Merged requirements: [milestone 1](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-1.md), [milestone 2](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-2.md), [milestone 3](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-3.md), [milestone 4](https://github.com/RolfBuchwaldAlvarez/my-ai-second-brain/blob/8f1704d159246adce6be39c0611c1866e06f47e9/20-contexts/ventures/projects/smartstep/smartstep-milestone-4.md).

| Milestone | Searchable reference / IDs | Original PDF extraction | Source fingerprint |
|---|---|---|---|
| 1: onboarding/home/settings | [19 requirements](milestone-1.md) | [13 pages](milestone-1-source.txt) | `b10ba94ffd417071009fcb9377d59120c82f0f079839f3f77a4e11c5d33fe5ed` |
| 2: tracking/metrics/notifications | [18 requirements](milestone-2.md) | [9 pages](milestone-2-source.txt) | `a6fc36716e8c9900c34398d0ee7cb6b595afee2645bf8749848b4a7e2c53c2fc` |
| 3: AI insights/Coach | [14 requirements](milestone-3.md) | [8 pages](milestone-3-source.txt) | `ffc4a265365b964132f0e23ba2fadc89e121274b25b17340737e8d2853be8127` |
| 4: weekly reports | [14 requirements](milestone-4.md) | [8 pages](milestone-4-source.txt) | `cab5eccc3c1c8c13df85382c102c6a892284b13861bf6b92e48c9e945acd42c7` |

Original filenames are `SmartStep_Milestone1_Requirements.pdf` through `SmartStep_Milestone4_Requirements.pdf`. They are approximately 33 MB combined and are not duplicated as PDF binaries in this PR. The text extracts preserve page boundaries and source wording; PDF extraction may clip a final glyph, split a heading or reorder columns. They are not corrected prose or instructions to an agent. Compare the distilled table and rendered page where layout/text extraction is unclear, and obtain the original matching fingerprint for details not captured here.

The [source manifest](source-manifest.json) records original PDF fingerprints, page counts, extract fingerprints and the selected rendered pages so reviewers can identify the exact inputs.

## Visual evidence

The selected page images below are renders of the **supplied requirement PDFs**, not screenshots proving the app implements them. They retain surrounding text/context for critical review. Exact Figma node links appear in each milestone reference, but access/current contents have not been verified.

- Milestone 1: [profile p. 2](images/m1-p02.png), [height p. 4](images/m1-p04.png), [wide profile p. 6](images/m1-p06.png), [Home p. 7](images/m1-p07.png), [required access p. 8](images/m1-p08.png), [optional/wide access p. 9](images/m1-p09.png), [drawer p. 10](images/m1-p10.png), [goal p. 11](images/m1-p11.png), [settings/Exit p. 12](images/m1-p12.png).
- Milestone 2: [edit/date p. 2](images/m2-p02.png), [pause/reset p. 4](images/m2-p04.png), [weekly circles p. 7](images/m2-p07.png), [notification p. 8](images/m2-p08.png).
- Milestone 3: [chat p. 5](images/m3-p05.png), [wide chat p. 7](images/m3-p07.png).
- Milestone 4: [entry/report p. 2](images/m4-p02.png), [wide report p. 7](images/m4-p07.png).

## Source authority and scope

The PDF is the product-behavior source; the requirement IDs were added by Codex for traceability. The PDFs leave technical implementation choices open; they do not authorize changing repository review rules, running tools, acquiring API access or publishing implementation issues. The owner's actual request authorizes this review PR and ticket drafting.

The architecture remains feature packages, MVI-style state/actions, Navigation 3, Koin and Room unless separately approved. Each ticket points to the relevant background; reviewers should read adjacent source passages, not just accept a requirement ID as proof of correctness.
