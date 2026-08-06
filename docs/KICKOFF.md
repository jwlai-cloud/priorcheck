# Kickoff — continuing the build

```bash
cd /Users/junwei.lai/Projects/Agent/sceneroom && claude
```

`CLAUDE.md` loads automatically. Paste the prompt below as the first message.

---

## Where the build actually is (2026-08-03)

**Working, committed, and pushed.** The full loop runs locally against live
Gemini and has been driven end to end in a real browser.

| Piece | State |
|---|---|
| Agents — writer, reviser, extractor, verifier, fandom | ✅ `app/agents/` |
| Workflow — draft → extract → check → decide → revise → re-check | ✅ `app/orchestrator.py` |
| Parallel integration | ⚠️ code done (`app/services/parallel_client.py`), **running on offline fixtures — no API key yet** |
| Claims ledger | ⚠️ in-memory; BigQuery implemented behind the same Protocol, switches on `BIGQUERY_DATASET` |
| UI — script page, margin notes, provenance | ✅ `frontend/` |
| Tests | ✅ 7 unit passing, ruff clean |
| **Deployed hosted URL** | ❌ **not done — blocked on gcloud auth** |
| Imagen payoff frame | ❌ not started (`ENABLE_IMAGE` flag exists, unused) |
| Demo video + Devpost write-up | ❌ not started |

Verified rather than assumed: Gemini drafts a scene with genuinely checkable
detail, extraction returns 6–8 claims including audience-sensitivity ones, the
pinned demo scene produces two sourced contradictions, and "Keep — deliberate"
leaves the scene text untouched while recording the rationale in provenance.

### Two blockers, both needing the human

1. **`gcloud auth login`** — the token expired; non-interactive commands cannot
   refresh it. Also decide *which project*: it currently defaults to `tgds-dev`,
   which is a TrafficGuard work project, while the $100 hackathon credits are
   likely on a personal account.
2. **`PARALLEL_API_KEY`** — sign up at parallel.ai. Everything runs on offline
   fixtures until then, and the UI says so honestly. This is a *scored,
   mandatory* requirement, so it is the highest-value outstanding item.

---

## The prompt

> Read `CLAUDE.md` and `docs/PRD.md` first — they hold decisions already made
> under adversarial review. Don't re-litigate them; if you think one is wrong,
> say so in a sentence and continue. Then read the "Where the build actually is"
> section of `docs/KICKOFF.md`.
>
> **Context.** Sceneroom is an agentic scene room for scripted production: the
> crew drafts a scene from the writer's intent, extracts every checkable claim,
> checks it against fact and against what this audience already litigates (both
> via Parallel), surfaces flags inline on the page, and on the writer's decision
> either fixes and re-checks, records it as deliberate artistic licence, or
> escalates it — leaving a provenance record. Agentic Cinema hackathon,
> **Parallel track**, deadline **2026-09-07 14:00 PT**, judged **Sep 23 – Oct 7**
> so the deployment must survive into October.
>
> The core loop is already built, tested and pushed. Do not rebuild it.
>
> **Priorities, in order:**
> 1. **Deploy to Cloud Run** and get a live public URL. Cloud Run specifically,
>    not Agent Engine — Cloud Run idles at ~$0 and the service must stay up for
>    ~9 weeks on a $100 credit. This is the single most overdue item.
> 2. **Wire the real Parallel key** via Secret Manager once available, and
>    confirm live verification end to end.
> 3. **Swap the ledger to BigQuery** (`BIGQUERY_DATASET`) so the audit trail is
>    durable — this is what satisfies the "updating dynamic databases"
>    production goal.
> 4. **One Imagen payoff frame** of the corrected scene. Cut it if it threatens
>    the timeline.
> 5. **3-minute video** (budget two full days) and the Devpost write-up. The
>    video is pre-recorded; the hosted URL stays live separately for judges.
>
> **Use these skills:** `hackathon-engineering` (keep `docs/ARCHITECTURE.md`,
> ADRs and a progress log current), `google-agents-cli-deploy` (Cloud Run),
> `google-agents-cli-adk-code` (ADK patterns), `frontend-design` (UI work),
> `hackathon-demo-video` and `hackathon-submission` at the end.
>
> **Verify, don't trust.** Check APIs against the installed package or official
> docs. Cheatsheets have been wrong three times on this project: the ADK 2.5
> graph edge API is a `{route: target}` dict not a 3-tuple;
> `google.adk.skills.load_skills_from_dir` doesn't exist; and the demo button
> bug was only caught by driving the real page with Playwright, not by testing
> the API. Run the UI in a browser before believing it works.
>
> **Housekeeping.** No `Co-Authored-By` trailers. One runnable check for
> non-trivial logic, no heavy test ceremony.
>
> **Start by** running the app locally, confirming the loop still works, then
> proposing the deployment plan. Wait for my go before deploying.

---

## Running it

```bash
uv sync
uv run --with pytest pytest tests/unit -q          # 7 tests
uv run --with ruff ruff check app tests
uv run uvicorn app.fast_api_app:app --port 8080    # then open http://localhost:8080
```

`/api/health` reports whether Parallel is live and which ledger backend is
active — check it first when something looks wrong.
