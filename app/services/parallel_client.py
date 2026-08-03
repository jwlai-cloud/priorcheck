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

"""Parallel Search — the partner integration.

One seam: `search()`. With `PARALLEL_API_KEY` set it calls Parallel's Search API
for real; without one it serves a small fixture so the rest of the system can be
built and demoed offline. Swapping is an env var, never a code change.

# ponytail: the offline path is a dict of canned results, deliberately. It exists
# so the build is not blocked on a key, not to simulate the web.
"""

from __future__ import annotations

import logging
import os

import httpx

from app.models import Source

logger = logging.getLogger(__name__)

PARALLEL_API_KEY = os.getenv("PARALLEL_API_KEY", "")
PARALLEL_SEARCH_URL = "https://api.parallel.ai/v1beta/search"
# "base" is the fast/cheap processor; "pro" is higher accuracy. Base is right
# for claim checking at scene scale.
PARALLEL_PROCESSOR = os.getenv("PARALLEL_PROCESSOR", "base")

_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def search(objective: str, queries: list[str] | None = None, max_results: int = 5) -> list[Source]:
    """Search the live web for evidence about `objective`.

    Args:
        objective: What we're trying to establish, in natural language. Parallel
            ranks by intent, so a full sentence beats keywords.
        queries: Optional explicit search strings to seed the search.
        max_results: Cap on returned sources.

    Returns:
        Sources with title, url and an excerpt. Empty list on failure — callers
        must treat "no sources" as unverifiable rather than as agreement.
    """
    if not PARALLEL_API_KEY:
        return _offline(objective, max_results)

    payload: dict = {
        "objective": objective,
        "processor": PARALLEL_PROCESSOR,
        "max_results": max_results,
    }
    if queries:
        payload["search_queries"] = queries

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                PARALLEL_SEARCH_URL,
                headers={
                    "x-api-key": PARALLEL_API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # network, auth, rate limit, schema drift
        logger.warning("Parallel search failed for %r: %s", objective[:80], exc)
        return []

    return _parse(data, max_results)


def _parse(data: dict, max_results: int) -> list[Source]:
    """Pull sources out of the response, tolerating field-name drift."""
    raw = data.get("results") or data.get("search_results") or []
    out: list[Source] = []
    for item in raw[:max_results]:
        if not isinstance(item, dict):
            continue
        excerpts = item.get("excerpts") or []
        snippet = ""
        if isinstance(excerpts, list) and excerpts:
            snippet = str(excerpts[0])
        else:
            snippet = str(item.get("excerpt") or item.get("snippet") or "")
        out.append(
            Source(
                title=str(item.get("title") or item.get("url") or "source"),
                url=str(item.get("url") or ""),
                snippet=snippet[:500],
            )
        )
    return out


# --- Offline fixture -------------------------------------------------------
# Keyed by substring so the demo scene (Seoul, 1963 / Joseon) returns something
# recognisable without a key. Everything else returns empty -> "unverifiable",
# which is the honest answer when we have no evidence.

_FIXTURE: dict[str, list[Source]] = {
    # Keyed on distinctive terms a 1963-Seoul or Joseon scene tends to produce.
    "radio": [
        Source(
            title="Portable two-way radio adoption in East Asian police forces",
            url="https://example.org/police-radio-history",
            snippet=(
                "Compact handheld transceivers did not enter routine police use "
                "in the region until the late 1960s. In 1963 Korean patrol units "
                "relied on vehicle-mounted sets and call boxes; a handheld unit "
                "carried on the person would be an anachronism."
            ),
        )
    ],
    "motorola": [
        Source(
            title="Motorola HT-220 handie-talkie — introduction date",
            url="https://example.org/motorola-ht-220",
            snippet=(
                "The HT-220 series was introduced in 1969. No Motorola handheld "
                "of that form factor was available in 1963, and none were in "
                "service with Korean police at that date."
            ),
        )
    ],
    "won": [
        Source(
            title="South Korean currency reform of 1962",
            url="https://example.org/krw-1962-reform",
            snippet=(
                "The June 1962 reform replaced the hwan with the won at 10:1. "
                "Won-denominated notes were in circulation by 1963."
            ),
        )
    ],
    "beer": [
        Source(
            title="Brewing brands in postwar South Korea",
            url="https://example.org/kr-brewing",
            snippet=(
                "OB and Crown were the dominant brands through the 1960s. The "
                "Hite brand name was not introduced until 1993."
            ),
        )
    ],
    "goguryeo": [
        Source(
            title="Northeast Project — an active historiographical dispute",
            url="https://example.org/northeast-project",
            snippet=(
                "Characterisations of Goguryeo remain actively disputed between "
                "states. Credible scholarship disagrees, and the question is "
                "politically sensitive rather than settled."
            ),
        ),
        Source(
            title="Korean period dramas and historical-distortion complaints",
            url="https://example.org/kr-drama-complaints",
            snippet=(
                "Several productions since 2023 drew formal complaints over "
                "depictions touching this dispute. In multiple cases the "
                "broadcaster apologised and scenes were re-edited after air."
            ),
        ),
    ],
    "northeast project": [
        Source(
            title="Northeast Project — an active historiographical dispute",
            url="https://example.org/northeast-project",
            snippet=(
                "An actively disputed matter of historiography between states; "
                "characterisations are contested and politically sensitive."
            ),
        ),
        Source(
            title="Korean period dramas and historical-distortion complaints",
            url="https://example.org/kr-drama-complaints",
            snippet=(
                "Productions since 2023 drew formal complaints; in several cases "
                "scenes were re-edited after broadcast following viewer campaigns."
            ),
        ),
    ],
    "hanbok": [
        Source(
            title="Costume accuracy complaints in period dramas",
            url="https://example.org/hanbok-accuracy",
            snippet=(
                "Audiences scrutinise silhouette, collar and colour conventions "
                "closely; several dramas issued corrections after viewer "
                "complaints about anachronistic hanbok."
            ),
        )
    ],
}


def _offline(objective: str, max_results: int) -> list[Source]:
    low = objective.lower()
    for key, sources in _FIXTURE.items():
        if key in low:
            return sources[:max_results]
    return []


def is_live() -> bool:
    """True when calls hit the real Parallel API. Surfaced in the UI so a demo
    never silently passes off fixture data as live search."""
    return bool(PARALLEL_API_KEY)
