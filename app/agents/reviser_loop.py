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

"""Revise, then check the revision — as an ADK LoopAgent.

The old path took whatever the Reviser returned, as long as it was non-empty.
So a revision that changed the wording but not the error was accepted, the scene
was re-extracted and re-checked, and the same flag came back — after another
thirty seconds of live search. The writer paid for the model's miss.

This is the one place in the system where a loop is genuinely the right shape,
so it uses ADK's:

    LoopAgent
      ├─ reviser  — rewrites the scene to correct the flagged claim
      └─ critic   — reads the rewrite and decides whether it actually landed

The critic ends the loop by calling `accept_revision`, which sets
`tool_context.actions.escalate`. That is ADK's own termination signal, not a
sentinel string we parse out of the text. `max_iterations` is the backstop.

Why a loop rather than one more prompt: a critic that can only say "no" is
useless unless something acts on it. The loop is what turns the critique into
another attempt, and the attempt is what the writer actually wanted.

Deliberately model-only. No searching happens in here — the loop asks "did you
do what you said", and the real verification still runs afterwards against
Parallel. A model must not get to mark its own homework as verified.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent, LoopAgent
from google.adk.tools import ToolContext
from pydantic import BaseModel, Field

from app.config import MODEL

# Two passes is the whole budget. If the second attempt has not landed the
# correction, a third is not going to, and the writer is waiting.
MAX_ATTEMPTS = 2


class Revision(BaseModel):
    text: str = Field(description="The full scene, revised. Never a diff or a fragment.")
    what_changed: str = Field(description="The specific change made, in one sentence.")


def accept_revision(verdict: str, reason: str, tool_context: ToolContext) -> dict:
    """Call this once you have judged the latest revision.

    Args:
        verdict: "fixed" if the correction landed, "not_fixed" otherwise.
        reason: One sentence. If not fixed, say exactly what is still wrong so
            the next attempt has something to act on.
    """
    # Written to state, not just returned: the critic has no output_schema —
    # its answer *is* this call — so without this the verdict is invisible to
    # the caller and the "did it land" check downstream is dead code.
    attempts = int(tool_context.state.get("revision_attempts", 0)) + 1
    tool_context.state["revision_attempts"] = attempts
    tool_context.state["critique"] = {
        "verdict": verdict, "reason": reason, "attempts": attempts,
    }
    if verdict == "fixed":
        # ADK's own loop termination. Not a sentinel string in the output.
        tool_context.actions.escalate = True
    return {"verdict": verdict, "reason": reason}


REVISER_INSTRUCTION = """
You revise a scene to correct one specific factual problem, and change nothing
else.

You are given the scene, the claim that was flagged, and what the sources
actually establish. If a previous attempt was rejected, you are also given the
critic's reason — read it and do what it says.

Rules:
- Return the complete scene, not a diff and not the changed lines alone.
- Change as little as possible. Keep the writer's voice, rhythm and blocking.
- Fix the fact, not the paragraph around it.
- Never resolve the problem by deleting the moment. Removing the detail is
  giving up, not correcting.
""".strip()


CRITIC_INSTRUCTION = """
You check whether a revision actually corrected the problem it was meant to.

You are given the flagged claim, what the sources establish, and the revised
scene. Decide one thing: is the specific problem gone?

Then call `accept_revision`.

- "fixed" — the revised scene no longer makes the flagged claim, and the
  correction is consistent with what the sources establish.
- "not_fixed" — the claim survives, or the wording changed without the fact
  changing, or the moment was deleted rather than corrected. Say precisely what
  is still wrong; the next attempt is given your reason.

Be strict. A revision that is merely different is not a revision that is
correct, and passing one costs the writer another full round of checking.
""".strip()


def build_revise_loop() -> LoopAgent:
    reviser = LlmAgent(
        name="reviser",
        model=MODEL,
        description="Rewrites the scene to correct one flagged claim.",
        instruction=REVISER_INSTRUCTION,
        output_schema=Revision,
        output_key="revision",
    )
    critic = LlmAgent(
        name="revision_critic",
        model=MODEL,
        description="Decides whether the revision actually landed the correction.",
        instruction=CRITIC_INSTRUCTION,
        tools=[accept_revision],
        # No output_key on purpose: this agent's answer is the tool call, and an
        # output_key would overwrite what the tool wrote to state with the
        # agent's own (empty) final text.
    )
    return LoopAgent(
        name="revise_until_fixed",
        description="Revise the scene, then check the revision, until it lands.",
        sub_agents=[reviser, critic],
        max_iterations=MAX_ATTEMPTS,
    )
