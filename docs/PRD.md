# Priorcheck — PRD

_Agentic Cinema hackathon · Parallel track · deadline 2026-09-07 14:00 PT._

## 1. Problem

A broadcaster's **standards / compliance reviewer** has to sign off that a
period drama won't trigger a public accuracy controversy before it airs. Today
that is manual: someone reads the script, notices what they happen to know is
wrong, and researches it by hand. Coverage depends on what one tired person
recognises at 2am.

**It has a named cost.** In June 2026, MBC's *21st Century Grand Princess* drew
sustained criticism for "verification errors, historical distortions, and
Northeast Project controversy". The production team and cast issued **public
apologies** and **scenes were deleted from the broadcast**
([Korea Star Daily, 2026-06-06](https://www.koreastardaily.com/tc/news/162818)).
Those are post-air costs for a pre-air failure.

**Who it is for:** standards & practices reviewers, compliance leads, and the
producers who answer to them. Secondary: script supervisors and post supervisors
doing rights clearance.

## 2. What it does

A reviewer uploads a script or scene. The system then:

1. **Extracts** every checkable claim — factual, historical, rights-bearing.
   ("A 1963 detective carries a Motorola HT-200." "This score cue is *Clair de
   Lune*." "Goguryeo is described as…")
2. **Verifies** each claim against the open web via **Parallel**, capturing the
   sources.
3. **Classifies** each into `verified` · `contradicted` · **`contested`** ·
   `unverifiable`.
4. **Writes** the claim, verdict, sources, and timestamp into a **BigQuery
   claims ledger**.
5. **Escalates** `contested` claims to a named human — it does not resolve them.
6. **Records** the reviewer's decision and rationale against the claim,
   permanently.

Output is a reviewed script where every claim is either cited-and-cleared or
explicitly assigned to a person.

## 3. Differentiation

> **A sign-off system of record for pre-air factual risk — it doesn't tell you
> the answer, it tells you what's checked, what's cited, and what a human still
> has to decide.**

An LLM that fact-checks a script is obvious in 2026; Gemini with Search
grounding does a version of it. **The checking is the commodity.** The product is:

- **Coverage** across a whole script, not one question at a time.
- **A ledger that persists** — every claim, verdict, source, reviewer, timestamp.
- **Explicit escalation** of what cannot be adjudicated. An agent that knows the
  limits of its own authority is more useful to a standards desk than one that
  claims omniscience — the desk needs "get a consultant" as much as "this date
  is wrong".
- **An audit trail** the broadcaster can produce when a controversy lands.

**Non-goal: guaranteeing correctness.** Retrieval isn't omniscience, sources
conflict, and some disputes (Northeast Project) are contested historiography
between states, not facts to look up. The claim is **"no unreviewed claim
ships"**, and that is both defensible and demonstrable.

## 4. Architecture

Google ADK 2.x agent ensemble on Gemini (Vertex / Agent Platform).

```
Orchestrator
  ├─ Extractor    — script → structured claims
  ├─ Verifier     — claim → verdict + sources        [Parallel]
  ├─ Rights       — asset/music/trademark clearance   [Parallel]
  └─ Adjudicator  — classify; escalate contested → human
                        ↓
              BigQuery claims ledger  ←→  Reviewer UI (sign-off)
                        ↓
              Agent Builder Data Store (grounding corpus)
```

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

**In:** claim extraction · Parallel verification with citations · four-way
classification · BigQuery ledger · contested escalation · reviewer sign-off UI ·
audit trail · deployed hosted URL.

**Out:** storyboard / image generation · video generation · script *rewriting* ·
a full DAM or rights-management system · real broadcaster integrations · mobile.

## 7. Risks

| Risk | Mitigation |
|---|---|
| **Timeline — the biggest one.** 37 days, zero code. | Walking skeleton with live URL by day 5, ledger stubbed. Treat a slip as an early-warning signal. |
| Live Parallel call fails during judging | 3-min video is **pre-recorded**; the hosted URL stays live separately for judges. |
| Hosted URL dies before judging ends (Oct 7) | Cloud Run scale-to-zero; verify uptime through the judging window. |
| Reads as a generic fact-checker | Pitch discipline — sign-off system, always. See §3. |
| Agent takes a side on contested history | Hard product rule: `contested` → human. Never resolved by the agent. |
