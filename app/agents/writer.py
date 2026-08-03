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

"""Writer — drafts a scene, and applies accepted corrections.

Deliberately thin. It exists to give the verification loop something to check
and something to revise; it is not a screenwriting tool.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

from app.config import MODEL


class SceneDraft(BaseModel):
    text: str = Field(description="The scene, in screenplay-ish prose.")
    setting: str = Field(description="Period and place, e.g. 'Seoul, 1963'.")


DRAFT_INSTRUCTION = """
You are a screenwriter drafting a single scene from a brief.

Write 150-250 words of vivid, concrete, filmable prose. Include specific,
checkable detail — named objects, dates, places, technology, clothing, music.
Those specifics are the point: they are what the crew will verify.

Do not hedge or write vaguely to stay safe. A scene full of nothing checkable
is useless here. Write it as you would mean it, and let the checkers do their
job.

Return the scene text and the setting (period and place).
""".strip()


REVISE_INSTRUCTION = """
You are a screenwriter revising one scene to correct a specific factual problem.

You will be given the current scene, the claim that was wrong, and the sourced
correction.

Change as little as possible. Fix the specific detail, keep the voice, the
blocking and the emotional beat exactly as they are. Do not rewrite the scene,
do not improve unrelated lines, do not add new checkable claims that were not
there before.

Return the full revised scene text and the unchanged setting.
""".strip()


def build_writer() -> LlmAgent:
    return LlmAgent(
        name="writer",
        model=MODEL,
        description="Drafts a scene from the writer's intent.",
        instruction=DRAFT_INSTRUCTION,
        output_schema=SceneDraft,
        output_key="scene_draft",
    )


def build_reviser() -> LlmAgent:
    return LlmAgent(
        name="reviser",
        model=MODEL,
        description="Applies one sourced correction to a scene, minimally.",
        instruction=REVISE_INSTRUCTION,
        output_schema=SceneDraft,
        output_key="scene_revision",
    )
