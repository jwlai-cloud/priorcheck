# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The revise/critique loop's wiring.

No model is called here. What is tested is the part that was silently broken
twice while building it: the critic reports by calling a tool, so the verdict
only survives if the tool writes it to state — and only if nothing else
overwrites that key afterwards.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent, LoopAgent

from app.agents.reviser_loop import MAX_ATTEMPTS, accept_revision, build_revise_loop


class FakeActions:
    def __init__(self) -> None:
        self.escalate = False


class FakeToolContext:
    """Enough ToolContext for the tool: mutable state and an actions object."""

    def __init__(self) -> None:
        self.state: dict = {}
        self.actions = FakeActions()


def test_a_landed_fix_ends_the_loop() -> None:
    ctx = FakeToolContext()
    accept_revision("fixed", "the anachronism is gone", ctx)
    assert ctx.actions.escalate is True, "ADK ends a LoopAgent on escalate"
    assert ctx.state["critique"]["verdict"] == "fixed"


def test_a_rejected_fix_keeps_the_loop_running() -> None:
    ctx = FakeToolContext()
    accept_revision("not_fixed", "the claim survives the rewrite", ctx)
    assert ctx.actions.escalate is False
    assert ctx.state["critique"]["reason"]


def test_attempts_accumulate_across_passes() -> None:
    """The caller surfaces 'accepted on attempt 2', so the count must be real."""
    ctx = FakeToolContext()
    accept_revision("not_fixed", "still wrong", ctx)
    accept_revision("fixed", "now right", ctx)
    assert ctx.state["critique"]["attempts"] == 2
    assert ctx.state["revision_attempts"] == 2


def test_the_verdict_survives_in_state() -> None:
    """The critic must not carry an output_key.

    It did, once. The agent's own final text is empty because its answer is the
    tool call, so the output_key overwrote the verdict with nothing and the
    caller's check became dead code.
    """
    loop = build_revise_loop()
    critic = next(a for a in loop.sub_agents if a.name == "revision_critic")
    assert critic.output_key is None, "an output_key here erases the tool's verdict"


def test_the_loop_is_shaped_as_expected() -> None:
    loop = build_revise_loop()
    assert isinstance(loop, LoopAgent)
    assert loop.max_iterations == MAX_ATTEMPTS
    names = [a.name for a in loop.sub_agents]
    assert names == ["reviser", "revision_critic"], "revise first, then judge it"
    reviser = loop.sub_agents[0]
    assert isinstance(reviser, LlmAgent)
    assert reviser.output_key == "revision"


def test_the_critic_cannot_search() -> None:
    """It judges whether the rewrite matches the finding — it does not re-verify.
    A model must not get to mark its own homework as verified."""
    loop = build_revise_loop()
    critic = next(a for a in loop.sub_agents if a.name == "revision_critic")
    assert [t.__name__ for t in critic.tools] == ["accept_revision"]
