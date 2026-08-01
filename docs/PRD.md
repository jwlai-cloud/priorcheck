# Sceneroom — PRD

_Agentic Cinema hackathon · Parallel track · deadline 2026-09-07 14:00 PT._

## 1. Problem

Scripted production keeps shipping historical and factual errors nobody meant
to make. Today the only defence is manual: someone reads the script, notices
what they happen to know is wrong, and researches it by hand. Coverage depends
on what one tired person recognises at 2am — and on generated content, the
errors arrive already sounding plausible.

The problem is **not** that productions deviate from history. Deliberate
deviation is craft. The problem is that nobody can tell the deliberate
deviations from the accidental ones until after air.

**It has a named cost.** In June 2026, MBC's *21st Century Grand Princess* drew
sustained criticism for "verification errors, historical distortions, and
Northeast Project controversy". The production team and cast issued **public
apologies** and **scenes were deleted from the broadcast**
([Korea Star Daily, 2026-06-06](https://www.koreastardaily.com/tc/news/162818)).
Those are post-air costs for a pre-air failure.

**Who it is for.** Primary: **AI-native studios producing scripted content at
volume** — e.g. [Utopai Studios](https://www.utopaistudios.com/), whose Utopai
East JV acquired a Seoul production house in Feb 2026 with 15 scripted series
and features in development. They are the sharper customer than legacy
broadcasters, structurally:

- They ship at higher velocity — that is their entire pitch.
- They have **no standards & practices department**. Broadcasters built that
  over decades; a studio founded in 2025 has not.
- Factual errors are not merely *missed*, they are **introduced** — generated
  content invents plausible period detail, so the base rate of risk is higher.
- An accuracy scandal is existential rather than embarrassing: "AI studio
  distorts history" is a story the press is already primed to write.
- They can adopt an agent/API product immediately; a broadcaster procures for
  nine months.

Secondary: broadcaster standards & compliance desks, script supervisors, and
post supervisors doing rights clearance.

**Why now.** AI-assisted production is scaling into Korean scripted content
(Utopai East, 2026) in the same year and market that demonstrated how severely
historical inaccuracy is punished (MBC, June 2026) — including on politically
charged ground like the Northeast Project, where an error is not a correction
but a diplomatic incident.

**Adjacent, not competing.** Platforms like Utopai's PAI sell on *internal*
coherence — narrative continuity and character consistency within the generated
work. Sceneroom verifies *externally*, against the real world, and produces a
cited, signed-off record. A studio generating with PAI needs this more, not
less. Expect a judge to raise the comparison; the distinction is generation tool
vs. compliance record.

## 2. What it does — a scene room that won't let a scene ship wrong

The unit of work is **developing one scene**, not auditing a finished script.

1. **Draft.** The writer gives intent — *"night scene, 1963, the detective loses
   her badge"* — and the crew drafts or expands the scene.
2. **Extract.** Every checkable claim in the draft is pulled out: factual,
   historical, rights-bearing. *("A 1963 detective carries a Motorola HT-200."
   "The cue is Clair de Lune." "Goguryeo is described as…")*
3. **Check canon.** Continuity agent compares against the production bible —
   internal consistency across scenes written out of order.
4. **Verify externally.** Verification agent checks each claim against the open
   web via **Parallel**, capturing sources.
5. **Scan the fandom.** A Fandom agent searches what this property's audience
   actually tracks and argues about — wikis, forums, reviews, past
   controversies — and flags what they are likely to catch. This is a different
   question from "is it true": something can be factually fine and still be a
   flashpoint.
6. **Classify** — `verified` · `contradicted` · **`contested`** · `unverifiable`.
   *`contested` is determined empirically:* if the web shows people actively
   disputing it, it is contested — the model is not asked to judge that itself.
7. **Surface inline** on the scene, not in a separate report. Contested claims
   route to a named human; the agent does not resolve them.
8. **Decide — three ways, not two.** Every flag offers:
   - **Fix** — an unintentional error. Scene revised, correction sourced, then
     re-checked.
   - **Keep — deliberate** — artistic license. Scene unchanged; the *choice* is
     logged as intentional with the real fact recorded beside it.
   - **Escalate** — contested history, routed to a human consultant.
9. **Payoff.** One **Imagen** frame of the corrected scene — a visual full-stop,
   not a storyboard feature.

Output: a production-ready scene **plus its provenance record** — what was
checked, against what source, decided by whom, and why.

**The principle: it's not "be accurate", it's "know what you're doing."**

A tool that flags every historical deviation is creativity police, and it would
be wrong — *Bridgerton* is deliberately anachronistic, *Inglourious Basterds*
rewrites the war on purpose. Artistic license is not an error.

The distinction that matters is **informed vs. accidental**. An informed
deviation is a creative choice; an uninformed one is the risk that ends in
apologies. The MBC case was not artistic license — it was errors nobody caught.

So the product does not constrain the writer. It makes every deviation from
reality **a decision rather than an accident**, and keeps the receipt.

**Mode setting, per project:**

- **Documentary / historical** — strict. A deviation is an error until justified.
- **Fiction / period drama** — advisory. A deviation is a choice to be logged.

Same engine, different threshold.

**Why this shape.** A pure verification tool is a compliance widget: it creates
nothing, and on video it is a table of claims. A full production crew is too
broad to finish. This is one workflow — scene development — with verification
as its spine.

## 3. Differentiation

> **A scene room that writes with you and makes every deviation from reality a
> deliberate choice on the record — instead of an accident someone finds after
> it airs.**

An LLM that fact-checks a script is obvious in 2026; Gemini with Search
grounding does a version of it. **The checking is the commodity.** The product is:

- **It creates, then checks its own work** — the crew drafts the scene and
  immediately holds it to account. Verification is inline in the writing loop,
  not a gate someone remembers to run afterwards.
- **Deviation is a first-class outcome, not a failure.** "Keep — deliberate"
  is a supported answer that gets recorded, so the tool serves fiction as
  readily as documentary.
- **A ledger that persists** — every claim, verdict, source, decision, and who
  made it.
- **Explicit escalation** of what cannot be adjudicated. An agent that knows the
  limits of its own authority is worth more than one claiming omniscience —
  a production needs "get a consultant" as much as "this date is wrong".
- **A provenance record** the studio can produce when a controversy lands:
  here is what we checked, what we chose, and why.
- **It models the people who actually catch these things.** Fans are the
  industry's de facto continuity QA — they maintain the wikis, track the props,
  and litigate the lore. The MBC errors were caught by *viewers*, not by the
  production. The Fandom agent runs that scrutiny **before** air instead of
  after, which is the whole thesis in one sentence.

**Non-goal: guaranteeing correctness.** Retrieval isn't omniscience, sources
conflict, and some disputes (Northeast Project) are contested historiography
between states, not facts to look up. The claim is **"no unreviewed claim
ships"**, and that is both defensible and demonstrable.

## 4. Architecture

Google ADK 2.x agent ensemble on Gemini (Vertex / Agent Platform).

```
Orchestrator
  ├─ Writer       — intent → scene draft; applies accepted corrections
  ├─ Extractor    — scene → structured claims
  ├─ Continuity   — claims vs. production bible (internal canon)
  ├─ Verifier     — claim → verdict + sources          [Parallel]
  ├─ Fandom       — what will this audience catch?      [Parallel]
  ├─ Rights       — asset/music/trademark clearance     [Parallel]
  └─ Adjudicator  — classify; escalate contested → human
                        ↓
        BigQuery claims ledger  ←→  Scene room UI (inline flags, sign-off)
                        ↓                      ↓
   Agent Builder Data Store            Imagen — one payoff frame
        (grounding corpus)
```

The revise loop is a real cycle: an accepted correction sends the scene back
through extraction and verification, so a fix cannot silently introduce a new
error.

**Verification playbooks are ADK Skills.** Each domain — Korean period drama,
firearms & props, music rights — ships as a loadable skill directory
(`SKILL.md` + `references/` + `scripts/`) consumed via `SkillToolset`. This
matters for three reasons:

- **Anti-hallucination.** Pinned authoritative sources in `references/` ground
  the Verifier on curated authorities rather than whatever search returns first.
- **Escalation rules become data.** "Northeast Project → always `contested`,
  never adjudicate" lives in the Korean-drama skill, not in code.
- **The customer can extend it.** A standards desk adds its own house
  guidelines as a skill without forking the system.

ADK ships the loader (`google.adk.skills`, Experimental), so this costs
packaging discipline rather than a subsystem. See `CLAUDE.md` for the verified
API surface and the frontmatter/layout rules the validator enforces.

**Partner integration:** use Parallel's **MCP server** *and* Search API. The
rules say "product or MCP server"; the main page says "MCP server". Using the
MCP server satisfies both, removing any Stage One pass/fail ambiguity.

**Google Cloud:** Gemini on Agent Platform · BigQuery (ledger + grounding) ·
Agent Builder Data Store · Cloud Run (hosted URL) · Secret Manager (Parallel
key) · least-privilege service account.

## 5. How this satisfies the judged criteria

| Criterion (equal weight) | How |
|---|---|
| **Technological Implementation** | ADK 2.x multi-agent ensemble, Parallel MCP, BigQuery ledger, Data Store grounding, Cloud Run, Secret Manager. |
| **Design** | A reviewer's working surface — claim queue, citations, contested lane, sign-off. Not a chat box, not a terminal. Gets a third of the build budget. |
| **Potential Impact** | Named user (standards desk), named cost (MBC, June 2026), and the demo shows the actual catch. |
| **Quality of the Idea** | Non-obvious framing: a *system of record and escalation*, not a fact-checker. The "knows what it can't decide" behaviour is the original part. |

Devpost's Production Goals: **action-driven** (writes verdicts and sign-offs to
BigQuery, assigns escalations — not a report generator) · **multi-agent
ensemble** with distinct sub-tasks and shared ledger state · **studio-grade
security** (Secret Manager, least privilege, every verdict grounded in cited
sources).

## 6. Scope

**In:** scene drafting from intent · claim extraction · continuity check against
the production bible · Parallel verification with citations · four-way
classification · inline flags on the scene · accept/override with logged
rationale · scene revision + re-check loop · BigQuery ledger · contested
escalation · **one Imagen payoff frame** · deployed hosted URL.

**Out:** **a screenplay application** — no formatting, act structure, character
or arc tools, multi-scene document management, collaboration, or Final Draft
export · a storyboard *feature* (multi-frame, variants, shot boards) · video
generation · full-script batch auditing · a DAM or rights-management system ·
real broadcaster/studio integrations · mobile.

**The scope line is one scene, not a screenplay.** The drafting capability is
deliberately thin — it exists to give the loop something to check and something
to revise. Depth belongs to verification, the three-way decision, and the
provenance record. This is not an editor with a checker bolted on; it is closer
to a code-review tool that can also apply the fix. Drifting into "script-writing
app" is the failure mode that loses the remaining time.

The single Imagen frame is a demo full-stop, not a product surface. If it
threatens the timeline, cut it — the scene + provenance record is the product.

## 7. Risks

| Risk | Mitigation |
|---|---|
| **Timeline — the biggest one.** 37 days, zero code. | Walking skeleton with live URL by day 5, ledger stubbed. Treat a slip as an early-warning signal. |
| Live Parallel call fails during judging | 3-min video is **pre-recorded**; the hosted URL stays live separately for judges. |
| Hosted URL dies before judging ends (Oct 7) | **Deploy to Cloud Run, not Agent Engine.** Cloud Run scales to zero (~$0 idle); Agent Engine bills continuously. Budget is a $100 credit and the service must survive ~9 weeks after work stops. Verify uptime through the judging window. |
| Reads as creativity police | Three-way disposition (fix / keep-deliberate / escalate) and the per-project mode setting. Never assert that a deviation is wrong — assert what was true. |
| Reads as a generic fact-checker | Pitch discipline — sign-off system, always. See §3. |
| Agent takes a side on contested history | Hard product rule: `contested` → human. Never resolved by the agent. |
