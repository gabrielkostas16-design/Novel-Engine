# Third-Party Sources

This repository is the single product codebase for the novel-factory project.
It starts from one upstream base and may later absorb selected modules or
clean-room requirements from the reviewed source projects below.

The machine-readable source of truth is [`provenance.yaml`](provenance.yaml).
This document is the human-readable register.

## Incorporated base

| Source | Fixed revision | License | Incorporation status | Purpose |
|---|---|---|---|---|
| [Jackela/Novel-Engine](https://github.com/Jackela/Novel-Engine) | `3279f5c7d8b4c1d4efe03934163bff39f5af32ef` | MIT | Entire repository is the fork baseline | Web/API, immutable revisions, snapshots, proposals, jobs, reviews, imports, exports, tests, and CI |

The original MIT copyright and permission notice remain in [`LICENSE`](LICENSE)
and are summarized in [`NOTICE`](NOTICE). The upstream baseline is also marked
by the annotated Git tag `upstream-baseline-20260713`.

## Reviewed donors not yet incorporated

No code, prompts, types, examples, images, or data from the following donors
were incorporated during M0. Their entries reserve an integration boundary;
they do not grant permission to copy material beyond the stated license.

| Source | Fixed revision | Observed repository license | Planned treatment | Planned role |
|---|---|---|---|---|
| [yuanbw2025/story&#102;orge](https://github.com/yuanbw2025/story%66orge) | `05d2615f6e04` | MIT | Selective migration with per-file attribution; replace IndexedDB authority with the product API | Novel-domain workbench and structured adoption UX |
| [alfredxw/denova](https://github.com/alfredxw/denova) | `d7aadb8013cd` | Apache-2.0 | Selective migration with Apache notice review | Diff, rollback, Agent, Skill, and run-console UX |
| [wssyh339/Narraverse-Engine](https://github.com/wssyh339/Narraverse-Engine) | `f6d97d2cbeee` | MIT | Extract small models/contracts; do not import monolithic services | Story bible, canon, character state, and approval concepts |
| [Xiaoyangy/novel-studio](https://github.com/Xiaoyangy/novel-studio) | `fb8513cf60ba` | Apache-2.0 | Prefer contract/behavior rewrite until its relationship with `ainovel-cli` is closed | Long-form pipeline, quality gates, checkpoint, and recovery |
| [worldwonderer/oh-story-claudecode](https://github.com/worldwonderer/oh-story-claudecode) | `097a7505c407` | MIT | Rewrite as typed MethodPack definitions; exclude all demo material | Method registry, routing, review, and continuity organization |
| [chatfire-AI/huobao-novel](https://github.com/chatfire-AI/huobao-novel) | `a4590ebfcc76` | MIT | Method-oriented rewrite with per-file review | Chinese snowflake, chapter planning, state write-back, and consistency content pack |
| [ExplosiveCoderflome/AI-Novel-Writing-Assistant](https://github.com/ExplosiveCoderflome/AI-Novel-Writing-Assistant) | `7785b0569bb0` | AGPL-3.0-only | Clean-room evidence only; no code, prompt, type, or asset copying | L3-to-L2 run ledger, checkpoint, artifact, and recovery requirements |

## Integration rules

Before a donor file or substantial portion enters the product branch, its
change must record:

1. source repository and fixed commit;
2. original path and destination path;
3. license and required notices;
4. whether the change is retained, migrated, refactored, or clean-room;
5. material modifications;
6. third-party text, image, sample, or dataset exclusions;
7. the tests and acceptance contract that justify the integration.

Permissively licensed code is not automatically architecture-compatible.
Every donor must enter through the product's own API, revision, proposal,
artifact, workflow, and MethodPack contracts.

GPL, AGPL, source-available, and no-license materials must not be copied into a
non-copyleft product line without a separate licensing decision. Publicly
observable behavior may be translated into independently written requirements
and tests only when the clean-room boundary is documented.

## Explicit exclusions at M0

- No donor repository other than the Novel-Engine base is vendored or copied.
- No `oh-story-claudecode` demo text, cover, image, or sample is included.
- No `AI-Novel-Writing-Assistant` code, prompt, schema, or type is included.
- No `novel-studio` or `ainovel-cli` code is included before provenance review.
- No generated model output or private author content is seed data.
