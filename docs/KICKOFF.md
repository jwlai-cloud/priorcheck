# Kickoff — dispatch prompt for the build session

Run from the repo root:

```bash
cd /Users/junwei.lai/Projects/Agent/priorcheck && claude
```

`CLAUDE.md` loads automatically. Paste the prompt below as the first message.

---

## The prompt

> Read `CLAUDE.md` and `docs/PRD.md` before doing anything — they hold decisions
> already made under adversarial review. Don't re-litigate them; if you think one
> is wrong, say so in a sentence and continue.
>
> **Context.** This is Priorcheck, an agentic scene room for scripted
> production: the crew drafts a scene from the writer's intent, verifies every
> checkable claim in it against canon and the open web, surfaces flags inline
> with citations, and revises on the writer's accept/override — leaving a
> provenance record. It's a submission for the Agentic Cinema hackathon
> on the **Parallel** track. Deadline **2026-09-07 14:00 PT**; judging runs
> Sep 23 – Oct 7, so whatever we deploy has to still be alive in October. The
> repo was created inside the contest window and must stay clean-room — never
> copy code from `../scripervisor` (a pre-window research spike; read it for
> design context only).
>
> **Your objective this session: the day-5 walking skeleton.** A live, publicly
> hosted URL where an intent line goes in, a scene is drafted, one claim is
> extracted and verified through Parallel, and the flag renders on the scene.
> The BigQuery ledger stays
> **stubbed** — do not build it yet. Deploying early beats deploying well; this
> gate is the project's early-warning signal, so if it's going to slip, say so
> loudly rather than quietly building something better.
>
> **Use these skills, in roughly this order:**
> - `hackathon-engineering` — standing practice for this project: keep
>   `docs/ARCHITECTURE.md`, ADRs and a progress log current as the code changes,
>   and check current SDK docs rather than relying on training data.
> - `google-agents-cli-workflow` — the ADK development lifecycle entrypoint.
> - `google-agents-cli-scaffold` — create the project (ADK 2.x, Python).
> - `google-agents-cli-adk-code` — agent/tool/state API patterns while building.
> - `google-agents-cli-deploy` — Cloud Run or Agent Engine for the hosted URL.
> - `agent-skills:incremental-implementation` — thin vertical slices; land each
>   one working before widening.
> - `frontend-design` — when the reviewer UI starts. Design is 25% of the score
>   and most entries will ship a chat box; budget a third of the build for it.
>
> **Verify, don't trust.** Check API surfaces against the installed package or
> official docs. Cheatsheets have twice been wrong on this project: the ADK 2.5
> graph edge API is a `{route: target}` dict rather than a 3-tuple, and
> `google.adk.skills.load_skills_from_dir` doesn't exist despite being
> documented.
>
> **Housekeeping.** No `Co-Authored-By` trailers in commits. Leave one runnable
> check behind for non-trivial logic — no heavy test ceremony.
>
> **Start by** proposing a concrete plan for the skeleton: the slices, the
> deployment target, and what you're deliberately stubbing. Wait for my go
> before writing code.

---

## After the skeleton lands

Build order from `CLAUDE.md`: real Parallel integration (MCP + Search API) →
the four-agent ensemble → swap the stub for the BigQuery ledger + Agent Builder
Data Store → reviewer UI → Secret Manager and least-privilege SA → 3-minute
video (budget two full days) and the Devpost write-up.

`hackathon-submission` covers the final write-up and diagrams;
`hackathon-demo-video` covers scripting and assembling the video.
