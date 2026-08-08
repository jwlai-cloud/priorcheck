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

## What the probe got wrong

The first reading of this was that a `Workflow` node "cannot see context",
because `run_llm_agent_as_node` sets an `LlmAgent` node to `mode='single_turn'`
with `include_contents='none'`, and the probe's reviser returned a placeholder
saying its context was missing.

Reading the current documentation (adk.dev, not the stale cached copy) corrects
that:

- **State does persist across nodes.** The docs list three channels — `output`
  passes data node to node, `message` is the user-facing response, and `state`
  is "data automatically persisted across nodes via Events throughout an ADK
  session". Nothing is lost; the reviser simply was not given its input the way
  a node receives one.
- **Routing is not done from inside an LlmAgent.** The idiomatic shape is an
  LlmAgent that classifies, followed by a plain function node that returns
  `Event(route=[...])`, with the dict edge dispatching on that. The probe tried
  to route from a tool on the agent itself and fed the model's free-text verdict
  in as the key, which is why `"Not Fixed"` never matched `"not_fixed"`.

So the port is smaller than it first looked, and it fits this codebase better
than `LoopAgent` does: the routing decision becomes a deterministic function
node, which is exactly the argument in ADR 002. The docs describe the point of
the graph API in those terms — "switching between non-deterministic AI-powered
agents and deterministic code as needed".

The shape would be:

    Workflow(edges=[
        (START, reviser, critic),
        (critic, route_fn),                       # returns Event(route=[...])
        (route_fn, {"not_fixed": reviser}),       # no edge for "fixed" -> ends
    ])

with the claim and sources in state, and the scene passed node to node.

## Decision

Keep the `LoopAgent` **for this submission**. It works, it is covered by tests,
and the container pins ADK 2.5, so a future removal cannot break the deployment
during judging. The port above is understood and small, but it is a rewrite of a
working path four weeks from a deadline, and nothing about the product improves
by doing it now.

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
