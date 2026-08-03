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

"""A pinned scene, so the loop is inspectable without any API keys.

Why this exists: the Writer invents different specifics on every run, so an
offline source fixture can never match them and every claim comes back
`unverifiable` — technically correct, but it shows nothing. This scene is fixed,
and its details line up with the offline fixtures, so the full
check -> decide -> revise loop can be walked through with no credentials.

It is always labelled as sample data in the UI. It is never used when
`PARALLEL_API_KEY` is set.
"""

from __future__ import annotations

DEMO_SETTING = "Seoul, 1963"

DEMO_TEXT = """INT. BACK ALLEY, JONGNO — NIGHT

Rain hammers the tin awnings. DETECTIVE PARK SUN-HEE, 30s, pins an informant
against the wet brick. Her badge catches the light of a shop sign.

                    PARK
          You were there. Say it.

The informant twists free. The badge tears loose and skitters into the drain.
Park swears, drops to her knees, reaches into the black water. Nothing.

She pulls a Motorola handie-talkie from her coat and thumbs the key.

                    PARK (CONT'D)
          This is Park. I've lost my shield in
          the Jongno drain. Send someone.

Static answers. She sits back on her heels in the rain. Somewhere behind her a
crate of Hite beer is being unloaded, bottles ringing against each other. She
counts what is left in her pocket: a single five-hundred won note, soaked
through and useless.
"""

# Claims are pinned too — extraction is deterministic here so the demo is
# reproducible. Each excerpt appears verbatim in DEMO_TEXT so the UI can
# underline it.
DEMO_CLAIMS: list[dict] = [
    {
        "kind": "historical",
        "text": (
            "A Seoul detective in 1963 would carry a Motorola handie-talkie "
            "on her person."
        ),
        "excerpt": "She pulls a Motorola handie-talkie from her coat and thumbs the key.",
    },
    {
        "kind": "rights",
        "text": "Hite beer was available in Seoul in 1963.",
        "excerpt": "crate of Hite beer",
    },
    {
        "kind": "factual",
        "text": "Five-hundred won notes were in circulation in South Korea in 1963.",
        "excerpt": "a single five-hundred won note",
    },
]
