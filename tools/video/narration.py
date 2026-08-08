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

"""The narration, as data.

Written to be *spoken*, not read: short sentences, one idea each, no clause
stacking. The capture script keys off the same beat ids, so the picture and the
voice cannot drift apart.

`hold` is the minimum seconds a beat stays on screen. The real duration is
whichever is longer, the audio or the hold, so a beat is never cut off
mid-sentence.
"""

from __future__ import annotations

BEATS: list[dict] = [
    {
        "id": "problem",
        "hold": 5,
        "text": (
            "In June, a Korean drama apologised on air and cut scenes after "
            "broadcast. Viewers had caught errors the production missed. But the "
            "errors were not the real problem. Nobody could tell which deviations "
            "were deliberate. Bridgerton is anachronistic on purpose. Informed is "
            "not accidental."
        ),
    },
    {
        "id": "brief",
        "hold": 5,
        "text": (
            "Sceneroom. A writer gives a brief — Seoul, nineteen sixty-three — and "
            "the production bible, so the room knows our own canon."
        ),
    },
    {
        "id": "crew-start",
        "hold": 7,
        "text": (
            "Seven agents go to work, and you watch them do it. The writer drafts. "
            "The extractor pulls out every claim that can be checked."
        ),
    },
    {
        "id": "crew-checks",
        "hold": 9,
        "text": (
            "Then three agents ask three different questions. Is it true — against "
            "the live web, through Parallel. Does using it need permission. And "
            "what has this audience already argued about? That one uses Parallel's "
            "MCP server to search and read for itself."
        ),
    },
    {
        "id": "continuity",
        "hold": 6,
        "text": (
            "Continuity checks what the web cannot. Our bible says Detective Park "
            "carries a revolver, never an automatic. The draft gave her an "
            "automatic. Caught, against our own canon."
        ),
    },
    {
        "id": "flags",
        "hold": 6,
        "text": (
            "Flags land on the page itself. Click a line, and the card judging it "
            "comes forward with its sources."
        ),
    },
    {
        "id": "rights",
        "hold": 5,
        "text": (
            "Rights found a song needing a sync licence. It will never say cleared. "
            "Clearance is a signature, not a model's opinion."
        ),
    },
    {
        "id": "contested",
        "hold": 10,
        "text": (
            "This is the one that matters. The agent found real precedent — a drama "
            "that drew three hundred thousand petition signatures and lost its "
            "sponsors. But credible sources disagree. So the system refuses to rule. "
            "It states both positions and routes it to a named human. An agent that "
            "knows the limit of its own authority beats one claiming omniscience."
        ),
    },
    {
        "id": "decide",
        "hold": 8,
        "text": (
            "Three answers, not two. Fix it, and the scene is rewritten then checked "
            "again, so a correction cannot smuggle in a new error. Escalate. Or keep "
            "it deliberately — licence recorded as a choice, with the real fact "
            "beside it. The reason is required. The reason is the product."
        ),
    },
    {
        "id": "ledger",
        "hold": 7,
        "text": (
            "Every verdict and decision is appended to BigQuery. Append-only, "
            "because a record you can edit is not provenance. And you can hand it "
            "over as a document."
        ),
    },
    {
        "id": "eval",
        "hold": 9,
        "text": (
            "We built an evaluation set: fifteen claims with known answers. It told "
            "us what we did not want to hear. Our better search setting scored "
            "higher — and ruled on a live historical dispute. The one thing this "
            "must never do. Fixed: zero wrong calls. Some claims still come back "
            "unverifiable, and that is fine. Unverifiable costs a decision. A wrong "
            "call ships an error."
        ),
    },
    {
        "id": "architecture",
        "hold": 8,
        "text": (
            "Seven Gemini agents on Vertex, orchestrated deterministically. "
            "Retrieval lives in the pipeline, not the models, so citations cannot be "
            "hallucinated. And whether a claim reaches a human is not a prompt. It is "
            "a pure function, unit tested. A guarantee written as a prompt is not a "
            "guarantee."
        ),
    },
    {
        "id": "frame",
        "hold": 7,
        "text": (
            "One frame of the scene as signed off. Look at what she is holding. That "
            "handie-talkie is the anachronism the writer chose to keep. The picture "
            "shows the decision. The ledger says why."
        ),
    },
    {
        "id": "close",
        "hold": 5,
        "text": (
            "Sceneroom does not promise your scene is correct. It promises no claim "
            "shipped unreviewed."
        ),
    },
]


def total_words() -> int:
    return sum(len(b["text"].split()) for b in BEATS)


if __name__ == "__main__":
    words = total_words()
    # ~155 wpm is a comfortable documentary pace for these voices.
    print(f"{len(BEATS)} beats · {words} words · ~{words / 155 * 60:.0f}s spoken")
    for b in BEATS:
        w = len(b["text"].split())
        print(f"  {b['id']:<14} {w:>3}w  ~{w / 155 * 60:>4.0f}s  hold {b['hold']}s")
