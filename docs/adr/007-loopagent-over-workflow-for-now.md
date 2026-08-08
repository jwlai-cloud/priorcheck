# 007 — LoopAgent over Workflow, for now

**Status:** Accepted, with a known expiry · 2026-08-08

## Context

The revise/critique cycle is built as an ADK `LoopAgent`. ADK 2.5 emits:

> `LoopAgent is deprecated in favor of Workflow and will be removed in a future
> version. Workflow cannot yet be used as an LlmAgent sub-agent.`

So the primitive we used is on the way out, and the question "are you using ADK
properly?" has a sharper edge than it looks.

## What was actually checked

Not assumed — probed against the installed package:

- `google.adk.workflow` exists and exports `Workflow`, `Node`, `FunctionNode`,
  `JoinNode`, `START`, `DEFAULT_ROUTE`, `Edge`.
- Edges are tuple chains, and a `dict` inside a chain is a routing map —
  `(critic, {"not_fixed": reviser})`. This matches the note in `CLAUDE.md` that
  the 2.5 edge API is a `{route: target}` dict rather than a 3-tuple.
- **A cycle is accepted.** `Workflow(edges=[(START, reviser), (reviser, critic),
  (critic, {"not_fixed": reviser})])` builds, three edges, no complaint. The
  loop shape is not the obstacle.
- A node routes by setting `tool_context.actions.route`, and the key must match
  the edge exactly. The first probe emitted `"Not Fixed"` against a
  `"not_fixed"` edge and ADK logged *"none were matched by the emitted route(s)
  ... The branch will end."*

## The actual blocker

`run_llm_agent_as_node` sets an `LlmAgent` used as a node to
`mode='single_turn'` and `include_contents='none'`. **A node does not see the
conversation.** Input arrives as `node_input` — the previous node's output.

That is a cleaner data flow than `LoopAgent`'s shared session state, and it is
not a drop-in swap:

- The reviser must receive the prompt as workflow input rather than as a user
  message.
- The critic's `node_input` would be the reviser's output alone, so the flagged
  claim and what the sources establish — which is the entire basis for judging
  the revision — have to move into workflow state with a `state_schema`.
- `run_agent_state` reads session state after the run; a Workflow's result is
  threaded through nodes, so the caller changes too.

In the probe, the reviser returned a placeholder saying its context was missing.
That was the API behaving as designed, not a defect.

## Decision

Keep the `LoopAgent`. It works, it is covered by tests, and the container pins
ADK 2.5, so a future removal cannot break the deployment during judging.

## Consequences

- A deprecation warning appears in logs. It is noise, not a fault, and this
  record is the answer to anyone who spots it.
- The port is understood rather than deferred blindly. The work is: move the
  claim and sources into workflow state, thread the prompt as node input, and
  normalise the route key at the point it is emitted rather than trusting the
  model's wording.

## What would change this

Pinning a later ADK where `LoopAgent` is actually removed, or needing a shape
`LoopAgent` cannot express — a branch that skips the critic, or a join across
several revision attempts. Both are `Workflow`'s natural territory and neither
is needed today.
