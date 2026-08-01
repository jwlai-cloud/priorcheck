# Priorcheck

**An agentic scene room for scripted production — where every scene the crew
writes is verified before it ships.**

Built on Google ADK and Gemini, with verification grounded in [Parallel](https://parallel.ai).
Submission for the [Agentic Cinema hackathon](https://agentic-cinema.devpost.com) — **Parallel track**.

---

## The problem

AI-native studios are producing scripted content at a velocity legacy pipelines
can't match — and without the standards & practices department broadcasters
spent decades building. Generated period detail *sounds* right, which is exactly
what makes it dangerous: the errors are introduced by the tooling, not merely
missed by a tired reader.

In June 2026, MBC's *21st Century Grand Princess* drew sustained criticism over
verification errors and historical distortion. The production team and cast
issued public apologies, and scenes were cut from the broadcast — post-air costs
for a pre-air failure.

## What it does

Give it intent — *"night scene, 1963, the detective loses her badge."*

1. The crew **drafts** the scene.
2. It **extracts** every checkable factual, historical, and rights-bearing claim.
3. It **checks canon** — the production bible, for scenes written out of order.
4. It **verifies externally** against the open web through Parallel, keeping the
   sources.
5. Flags land **inline on the scene**, with citations.
6. Anything it can't adjudicate is marked **contested** and routed to a human.
7. You accept or override; the scene is **revised**, the rationale logged, and
   the corrected scene **re-checked**.
8. One **Imagen** frame closes the loop.

You get a production-ready scene **and its provenance record** — what was
checked, against which source, decided by whom, and why.

## What it deliberately does not do

**It does not guarantee correctness.** Retrieval isn't omniscience, and some
disputes are contested historiography rather than facts to look up — an agent
that ruled on those would be wrong in the most damaging way available.

The promise is narrower and more useful: **no unreviewed claim ships.** Every
claim is either cited and cleared, or explicitly assigned to a person.

It is also not a storyboard tool, a video generator, or a replacement for a
historical consultant.

## Status

Early. See [`docs/PRD.md`](docs/PRD.md) for the full spec and
[`CLAUDE.md`](CLAUDE.md) for build conventions.

## License

[Apache 2.0](LICENSE).
