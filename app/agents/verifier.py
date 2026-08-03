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

"""Verifier and Fandom — the two agents grounded in Parallel.

They ask different questions:

- **Verifier**: is this true? Evidence for or against the claim itself.
- **Fandom**:   will this audience object? What comparable productions were
                criticised for, whether or not the claim is factually fine.

Both are given sources and asked to judge only those sources. Neither is asked
to rule on a dispute: if the evidence itself disagrees, the verdict is
`contested` and a human decides.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

from app.config import MODEL


class VerificationResult(BaseModel):
    verdict: str = Field(
        description="One of: verified, contradicted, contested, unverifiable."
    )
    reasoning: str = Field(description="One or two sentences, citing the sources.")


class FandomResult(BaseModel):
    is_flashpoint: bool = Field(
        description="True if this audience is known to scrutinise or dispute this."
    )
    precedent: str = Field(
        description=(
            "What comparable productions were criticised for, with specifics. "
            "Empty string if no precedent was found."
        )
    )
    reasoning: str = Field(description="One or two sentences, citing the sources.")


VERIFIER_INSTRUCTION = """
You judge a single claim against a set of sources you are given. You do not use
prior knowledge as evidence — only what the sources say.

Choose exactly one verdict:

- verified      — the sources support the claim.
- contradicted  — the sources show the claim is wrong. Say what is actually
                  true, specifically, so it can be corrected.
- contested     — the sources genuinely disagree with each other, or the topic
                  is an active dispute between credible parties. Use this for
                  matters of contested historiography or politics. It is not a
                  fallback for "unsure".
- unverifiable  — no sources, or nothing that speaks to the claim. Never treat
                  absence of evidence as support.

Critical: when the topic is contested, your job is to say so — not to pick the
side you find more persuasive. Taking a position on a live historical or
political dispute is the single worst thing this system can do.

Keep the reasoning to one or two sentences, and refer to what the sources
actually said.
""".strip()


FANDOM_INSTRUCTION = """
You assess whether an audience is likely to object to something in a scene.

This is a different question from whether it is true. Something can be
factually correct and still be a flashpoint, and something can be a harmless
invention that nobody will care about.

You are given sources about how audiences and critics have responded to
comparable productions. Report **precedent, not prediction**: what has actually
drawn complaints before, with specifics — which kinds of production, what the
objection was, what the consequence was.

Good: "Several period dramas since 2023 drew formal complaints over depictions
touching this dispute; in some cases scenes were re-edited after broadcast."
Bad:  "Fans will probably be annoyed by this."

If the sources show no precedent, say so plainly and set is_flashpoint false.
Do not invent an audience reaction. Do not speculate about sentiment.
""".strip()


def build_verifier() -> LlmAgent:
    return LlmAgent(
        name="verifier",
        model=MODEL,
        description="Judges a claim against retrieved sources.",
        instruction=VERIFIER_INSTRUCTION,
        output_schema=VerificationResult,
        output_key="verification",
    )


def build_fandom() -> LlmAgent:
    return LlmAgent(
        name="fandom",
        model=MODEL,
        description="Assesses audience flashpoint risk from documented precedent.",
        instruction=FANDOM_INSTRUCTION,
        output_schema=FandomResult,
        output_key="fandom_check",
    )
