# Progress

_Deadline **2026-09-07 14:00 PT**. Judging **2026-09-23 → 10-07**, so the URL
must survive into October._

**Live:** <https://sceneroom-320877670799.us-central1.run.app> · access code is
on the submission page · revision `sceneroom-00010-7gm`

## Done

| | Evidence |
|---|---|
| Cloud Run deployment, scale-to-zero | `min-instances 0`, `max-instances 3`, `--timeout 600` |
| Seven-agent crew | writer/reviser, extractor, continuity, verifier, fandom, rights, adjudicator |
| Deterministic escalation | `route()` is a pure function; 6 tests |
| Streamed runs | SSE, real per-agent timings, ~30s pass |
| Console UI | inline flags, claim↔note bridge, 3 themes, contested lane |
| **Parallel Search API** | Verifier + Rights, orchestrator-retrieved |
| **Parallel MCP** | Fandom agent searches for itself |
| **BigQuery ledger** | `agent-era.sceneroom.{claims_ledger,scenes}`, append-only |
| Secret Manager + least privilege | no key material in the container; dataset-scoped WRITER |
| Access gate | cookie-based, guards the five endpoints that spend money |
| One payoff frame | `gemini-3.1-flash-image`, only once nothing is open |
| Tests | 30 unit, ruff clean |
| Docs | `ARCHITECTURE.md`, 7 ADRs, `SUBMISSION.md`, `VIDEO.md` |
| Teaching artefact | `tutorial.html` — navigable page, + `TUTORIAL.md` |
| Diagrams | topology + handshake sequence, both 9/9 showcase checks |
| Revise graph | ✅ ADK `Workflow` — reviser → critic → route, retry once |
| ADK / scaffold | ✅ 2.6.1, migrated to `agents-cli-manifest.yaml` |
| Demo video | ✅ 2:54, `tools/video/` rebuilds it in three commands |
| Recent scenes + record export | reopen past work; download the provenance record |
| Continuity actually fires | the bible example produces canon claims |

Verified by driving the deployed page in a browser, not by reading code: a live
run streams all seven agents, produces cited verdicts including `contradicted`
and `contested`, records the decision to BigQuery, and renders the frame.

## Left

| | Notes |
|---|---|
| **3-minute video** | v3 cut exists and plays. Awaiting your notes. |
| **Devpost write-up** | Written: `docs/SUBMISSION.md`. Paste and submit. |
| Verification quality | `pro` processor + tightened objectives landed. Still conservative — an eval set would turn "it feels better" into a number. |
| Named escalation human | UI says "Standards desk". A real name would land better on video. |

## What is deliberately not being built

Recorded so it stops being re-proposed:

- **A storyboard.** One frame, no grid, no variants. Image generation is the
  crowded lane.
- **Multi-scene storybook / scene management / plot tools.** The scope line is
  one scene, not a screenplay. This is the failure mode that eats the remaining
  time.
- **Video generation.** Out since the PRD.

Good v2 ideas, filed for "What's next" rather than built: multi-scene
continuity (the Continuity agent already checks a bible; checking scene 12
against scenes 1–11 is the obvious next step), and house-style skills a
standards desk could add without forking.

## Traps this project has already paid for

1. `GOOGLE_APPLICATION_CREDENTIALS` in the shell profile points at a
   TrafficGuard key and overrides ADC — local runs silently bill the wrong
   project. Use `env -u GOOGLE_APPLICATION_CREDENTIALS`.
2. The Dockerfile copied `app/` but not `frontend/`. The static mount is guarded
   by `FRONTEND.is_dir()`, so the container started healthy and served 404 at
   `/` — a successful-looking deploy with no product in it.
3. `/api/scenes/stream` was shadowed by `/api/scenes/{scene_id}` and 404'd as
   "No such scene".
4. `mcp` 2.x moved `mcp.shared.session`; ADK imports it, catches the
   ImportError, and logs at debug — the MCP toolset vanishes silently. Pinned
   `<2.0`.
5. `imagen-*` publisher models are not available to this project in any region
   tried, and `generate_images` is deprecated. Listing the models the project
   can actually see was the only reliable way to find that out.
6. Scenes lived only in the instance that drafted them, so a decision could 404
   on another instance. Fixed by persisting scenes to BigQuery.

Every one was found by running the thing, not by reading about it.
