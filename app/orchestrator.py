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

"""The Sceneroom workflow.

    intent -> draft -> extract -> check (canon | fact | fandom) -> decide
           -> revise -> re-check -> provenance

Claims are checked concurrently — they're independent, and a scene has 3-8 of
them, so doing it serially would triple the demo's latency for no reason.

The human decision in the middle is not a formality: agents never set a
`Disposition`, and `keep_deliberate` is how artistic licence gets recorded
rather than corrected.
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from app.agents.extractor import build_extractor
from app.agents.verifier import build_fandom, build_verifier
from app.agents.writer import build_reviser, build_writer
from app.models import (
    Claim,
    ClaimKind,
    Disposition,
    Mode,
    RevisionEntry,
    Scene,
    Source,
    Verdict,
)
from app.services import parallel_client
from app.services.ledger import get_ledger
from app.services.runner import run_agent

logger = logging.getLogger(__name__)

# A scene has a handful of claims; cap concurrency so a long scene can't fan out
# into a rate-limit wall.
_MAX_CONCURRENT_CHECKS = 6


async def draft_scene(intent: str, project: str, mode: Mode, setting: str = "") -> Scene:
    """Step 1: turn the writer's brief into a scene."""
    prompt = f"Brief: {intent}"
    if setting:
        prompt += f"\nSetting: {setting}"

    out = await run_agent(build_writer(), prompt)
    scene = Scene(
        id=f"sc-{uuid.uuid4().hex[:8]}",
        project=project,
        mode=mode,
        intent=intent,
        setting=out.get("setting") or setting,
        text=out.get("text", ""),
    )
    get_ledger().save_scene(scene)
    get_ledger().append_revision(
        RevisionEntry(
            revision=1,
            scene_id=scene.id,
            what_changed="Scene drafted from brief",
            why=intent,
        )
    )
    return scene


async def load_demo_scene(project: str = "demo", mode: Mode = Mode.FICTION) -> Scene:
    """A pinned scene whose details match the offline fixtures, so the loop can
    be walked through without credentials. Always labelled as sample data."""
    from app import demo

    scene = Scene(
        id=f"sc-{uuid.uuid4().hex[:8]}",
        project=project,
        mode=mode,
        intent="Sample scene — a detective loses her badge in a Jongno alley.",
        setting=demo.DEMO_SETTING,
        text=demo.DEMO_TEXT.strip(),
        claims=[
            Claim(
                id=f"cl-{uuid.uuid4().hex[:8]}",
                kind=ClaimKind(c["kind"]),
                text=c["text"],
                excerpt=c["excerpt"],
            )
            for c in demo.DEMO_CLAIMS
        ],
    )
    get_ledger().save_scene(scene)
    get_ledger().append_revision(
        RevisionEntry(
            revision=1,
            scene_id=scene.id,
            what_changed="Sample scene loaded",
            why="Demonstration without live search credentials",
        )
    )
    return await check_claims(scene)


async def extract_claims(scene: Scene) -> list[Claim]:
    """Step 2: pull out everything checkable."""
    prompt = (
        f"Setting: {scene.setting}\n"
        f"Production type: {scene.mode.value}\n\n"
        f"Scene:\n{scene.text}"
    )
    out = await run_agent(build_extractor(), prompt)

    claims: list[Claim] = []
    for raw in out.get("claims", []):
        kind_str = str(raw.get("kind", "factual")).lower().strip()
        try:
            kind = ClaimKind(kind_str)
        except ValueError:
            kind = ClaimKind.FACTUAL
        claims.append(
            Claim(
                id=f"cl-{uuid.uuid4().hex[:8]}",
                kind=kind,
                text=str(raw.get("text", "")).strip(),
                excerpt=str(raw.get("excerpt", "")).strip(),
            )
        )
    return [c for c in claims if c.text]


async def _check_one(claim: Claim, scene: Scene, sem: asyncio.Semaphore) -> Claim:
    """Verify one claim, and — where relevant — check audience precedent too."""
    async with sem:
        if claim.kind == ClaimKind.FANDOM:
            await _check_fandom(claim, scene)
        else:
            await _check_factual(claim, scene)
    return claim


async def _check_factual(claim: Claim, scene: Scene) -> None:
    objective = (
        f"Establish whether this is accurate for {scene.setting or 'the period'}: "
        f"{claim.text}"
    )
    sources = await parallel_client.search(objective)
    claim.sources = sources

    if not sources:
        claim.verdict = Verdict.UNVERIFIABLE
        claim.reasoning = "No sources found. Absence of evidence is not support."
        return

    prompt = (
        f"Claim: {claim.text}\n"
        f"Setting: {scene.setting}\n\n"
        f"Sources:\n{_format_sources(sources)}"
    )
    out = await run_agent(build_verifier(), prompt)
    claim.verdict = _parse_verdict(out.get("verdict"))
    claim.reasoning = str(out.get("reasoning", ""))


async def _check_fandom(claim: Claim, scene: Scene) -> None:
    # Precedent, not prediction: ask what comparable productions were criticised
    # for, which is a real, indexed question.
    objective = (
        f"Find documented audience or critical objections to how productions "
        f"set in {scene.setting or 'this period'} have handled: {claim.text}. "
        f"Include past controversies and their consequences."
    )
    sources = await parallel_client.search(objective)
    claim.sources = sources

    if not sources:
        claim.verdict = Verdict.UNVERIFIABLE
        claim.reasoning = "No documented precedent found."
        return

    prompt = (
        f"Subject: {claim.text}\n"
        f"Setting: {scene.setting}\n\n"
        f"Sources:\n{_format_sources(sources)}"
    )
    out = await run_agent(build_fandom(), prompt)
    claim.precedent = str(out.get("precedent", ""))
    claim.reasoning = str(out.get("reasoning", ""))
    # A flashpoint with documented precedent is contested by definition: people
    # are actively arguing about it. That is an empirical call, not a judgement.
    claim.verdict = (
        Verdict.CONTESTED if out.get("is_flashpoint") else Verdict.VERIFIED
    )


async def check_claims(scene: Scene) -> Scene:
    """Step 3: check every claim concurrently, then persist."""
    if not scene.claims:
        scene.claims = await extract_claims(scene)

    sem = asyncio.Semaphore(_MAX_CONCURRENT_CHECKS)
    await asyncio.gather(*(_check_one(c, scene, sem) for c in scene.claims))

    get_ledger().save_scene(scene)
    return scene


async def decide(
    scene: Scene,
    claim_id: str,
    disposition: Disposition,
    rationale: str,
    decided_by: str = "writer",
) -> Scene:
    """Step 4: the human decision, and the revision it triggers.

    `fixed` rewrites the scene and re-checks it — a correction must not be able
    to introduce a new error silently. `keep_deliberate` leaves the scene alone
    and records the choice, which is the whole point of the product.
    """
    claim = next((c for c in scene.claims if c.id == claim_id), None)
    if claim is None:
        return scene

    claim.disposition = disposition
    claim.rationale = rationale
    claim.decided_by = decided_by

    ledger = get_ledger()

    if disposition == Disposition.FIXED:
        prompt = (
            f"Current scene:\n{scene.text}\n\n"
            f"Problem: {claim.text}\n"
            f"What the sources establish: {claim.reasoning}\n\n"
            f"Revise minimally to correct this."
        )
        out = await run_agent(build_reviser(), prompt)
        new_text = out.get("text", "").strip()
        if new_text:
            scene.text = new_text
            scene.revision += 1
            what = f"Corrected: {claim.text}"
            # Re-check: the fix may have introduced something new.
            scene.claims = await extract_claims(scene)
            await check_claims(scene)
        else:
            what = f"Correction attempted but no revision produced: {claim.text}"
    elif disposition == Disposition.KEEP_DELIBERATE:
        what = f"Kept as deliberate: {claim.text}"
    else:
        what = f"Escalated to a human: {claim.text}"

    ledger.append_revision(
        RevisionEntry(
            revision=scene.revision,
            scene_id=scene.id,
            claim_id=claim.id,
            what_changed=what,
            why=rationale or "(no rationale given)",
            disposition=disposition,
            sources=claim.sources,
        )
    )
    ledger.save_scene(scene)
    return scene


def _format_sources(sources: list[Source]) -> str:
    return "\n\n".join(
        f"[{i + 1}] {s.title}\n{s.url}\n{s.snippet}" for i, s in enumerate(sources)
    )


def _parse_verdict(value: object) -> Verdict:
    try:
        return Verdict(str(value).lower().strip())
    except ValueError:
        return Verdict.UNVERIFIABLE
