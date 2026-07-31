# Priorcheck

**A pre-air factual risk sign-off system for broadcast standards desks.**

Built on Google ADK and Gemini, with verification grounded in [Parallel](https://parallel.ai).
Submission for the [Agentic Cinema hackathon](https://agentic-cinema.devpost.com) — **Parallel track**.

---

## The problem

Before a period drama airs, someone has to sign off that it won't cause an
accuracy controversy. Today that's one reviewer reading a script and catching
what they happen to know is wrong.

In June 2026, MBC's *21st Century Grand Princess* drew sustained criticism over
verification errors and historical distortion. The production team and cast
issued public apologies, and scenes were cut from the broadcast — post-air costs
for a pre-air failure.

## What Priorcheck does

Upload a script. An agent ensemble:

1. **extracts** every checkable factual, historical, and rights-bearing claim;
2. **verifies** each against the open web through Parallel, keeping the sources;
3. **classifies** it — `verified` · `contradicted` · `contested` · `unverifiable`;
4. **writes** the verdict and citations to a BigQuery claims ledger;
5. **escalates** contested claims to a named human instead of resolving them;
6. **records** the reviewer's sign-off, permanently.

## What it deliberately does not do

**It does not guarantee correctness.** Retrieval isn't omniscience, and some
disputes are contested historiography rather than facts to look up — an agent
that ruled on those would be wrong in the most damaging way available.

The promise is narrower and more useful: **no unreviewed claim ships.** Every
claim is either cited and cleared, or explicitly assigned to a person.

## Status

Early. See [`docs/PRD.md`](docs/PRD.md) for the full spec and
[`CLAUDE.md`](CLAUDE.md) for build conventions.

## License

[Apache 2.0](LICENSE).
