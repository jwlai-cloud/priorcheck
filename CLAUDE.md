# Priorcheck — standing instructions

Read this before doing anything. It encodes decisions already made; don't
re-litigate them.

## What this is

**Priorcheck** — a pre-air factual risk sign-off system for broadcast standards
desks. Submission for the [Agentic Cinema hackathon](https://agentic-cinema.devpost.com),
**Parallel track**.

A reviewer submits a script. An agent ensemble extracts every checkable
factual / historical / rights claim, verifies each against the open web via
**Parallel**, writes the verdict and its sources into a **BigQuery claims
ledger**, escalates what it cannot adjudicate to a named human, and records the
sign-off permanently.

Full spec: [`docs/PRD.md`](docs/PRD.md).

## Hard rules

1. **Clean-room. Never copy code from the `scripervisor` repo** (a pre-window
   research spike that lives at `../scripervisor`). Reading it for *design*
   context is fine; copying files is not. The rules require this project be
   "newly created… not a modification or extension of… existing work". This repo
   was created 2026-07-31, four days inside the window — keep it that way.
2. **Google Cloud AI only at runtime.** Gemini via Vertex / Agent Platform,
   `google-adk`, `google-genai`, Imagen. Plus the Partner's own AI features
   (Parallel). **No other AI models, agent frameworks, or AI APIs** — the rules
   name OpenAI, Anthropic, AWS and Microsoft as prohibited. Non-AI third-party
   services (hosting, databases, web frameworks) are fine.
3. **No `Co-Authored-By` trailers in commits.** Write the commit body and stop.
4. **Never adjudicate contested history.** If a claim touches disputed
   historiography or attribution, mark it `contested` and route it to a human.
   Do not have the agent pick a side. This is a core product behaviour, not a
   caveat.
5. **Pitch it as a sign-off system, never as an "AI fact-checker."** The
   fact-checking is commodity; the workflow, the ledger and the audit trail are
   the product. Getting this wrong loses the *Quality of the Idea* criterion.

## Build order (the gate matters)

**Deadline: 2026-09-07 14:00 PT.** Judging 2026-09-23 → 10-07, so the hosted URL
must still be alive in October.

1. **Walking skeleton with a live hosted URL — target day 5.** Script in →
   one claim verified via Parallel → result on screen. Ledger **stubbed**.
   *If this slips, say so loudly; it is the project's early-warning signal.*
2. Real Parallel integration (MCP server + Search API).
3. Agent ensemble: Extractor → Verifier → Rights → Adjudicator, under an
   orchestrator. Distinct sub-tasks, shared ledger state.
4. Swap the stub for the **BigQuery** ledger; add an Agent Builder Data Store
   for grounding.
5. Reviewer UI — sign-off, citations, contested queue. **Design is 25% of the
   score; budget a third of the build for it, not the leftovers.**
6. Secret Manager, least-privilege service account.
7. 3-minute video (budget 2 full days) + Devpost write-up.

## Verification playbooks = ADK Skills

Domain verification methodology ships as **ADK Skills**, loaded at runtime — not
hardcoded prompts. This is how escalation rules and authoritative sources become
data the user can extend.

```
skills/
  korean-period-drama/
    SKILL.md          # required, UPPERCASE
    references/*.md   # pinned authoritative sources, known-contested topics
    assets/*          # templates, schemas
    scripts/*.py      # deterministic checks, run via run_skill_script
```

```python
from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset

skill = load_skill_from_dir(pathlib.Path(__file__).parent / "skills" / "korean-period-drama")
toolset = skill_toolset.SkillToolset(skills=[skill], additional_tools=[...])
```

**Verified against installed google-adk 2.5.0** — do not trust cheatsheets here:

- `load_skill_from_dir` exists. **`load_skills_from_dir` (plural) does NOT** —
  loop over dirs, or use `SkillRegistry`.
- `SkillToolset(skills=None, *, registry=None, code_executor=None,
  script_timeout=300, additional_tools=None, tool_name_prefix=None,
  tool_filter=None)`.
- Injected tools: `ListSkillsTool`, `SearchSkillsTool`, `LoadSkillTool`,
  `LoadSkillResourceTool`, `RunSkillScriptTool`. Plus
  `DEFAULT_SKILL_SYSTEM_INSTRUCTION`.
- **Marked Experimental.** Acceptable for this, but keep the agent working if
  skill loading fails.

**Packaging rules the validator enforces** (Claude Code tolerates violations,
ADK does not):

- `SKILL.md` — **uppercase**. A lowercase `skill.md` works on macOS and fails on
  any case-sensitive filesystem (i.e. in the container).
- YAML frontmatter required: `name` must equal the directory name, lowercase
  kebab-case, ≤64 chars, no leading/trailing/consecutive hyphens; `description`
  non-empty, ≤1024 chars.
- Only `references/`, `assets/`, `scripts/` are recognised. A `resources/` dir
  is unreachable via `load_skill_resource`.

**Scope discipline:** skills land at build step 3–4. They must not delay the
day-5 walking skeleton.

## Working preferences

- Use the ADK skills before writing agent code: `google-agents-cli-scaffold`
  (new project), `google-agents-cli-adk-code` (API patterns),
  `google-agents-cli-deploy` (Cloud Run / Agent Engine). ADK 2.x is GA — the
  graph `Workflow` API lives in `references/adk-workflows.md`.
- Verify SDK/API details against installed packages or official docs. Cheatsheets
  have been wrong before (the ADK 2.5 edge API is a `{route: target}` dict, not
  the 3-tuple one cheatsheet showed).
- Leave one runnable check behind for non-trivial logic. No heavy test ceremony.
- Prefer the boring, shortest solution that works.

## Don't

- Don't build a storyboard/image-generation feature. It's the crowded lane and
  it is not this product.
- Don't claim the system guarantees correctness. It doesn't and can't. The claim
  is "no unreviewed claim ships".
- Don't put the claims ledger in session state — the rules explicitly want
  "updating dynamic databases", and session state reads as a toy.
