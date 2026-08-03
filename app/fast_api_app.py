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

"""HTTP API + static hosting for the Sceneroom UI."""

from __future__ import annotations

import logging
import pathlib

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import orchestrator
from app.config import ENABLE_IMAGE, MODEL, PROJECT_ID
from app.models import Disposition, Mode, Scene
from app.services import parallel_client
from app.services.ledger import get_ledger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sceneroom",
    description="An agentic scene room: write a scene, then hold it to account.",
)

FRONTEND = pathlib.Path(__file__).resolve().parent.parent / "frontend"


class DraftRequest(BaseModel):
    intent: str = Field(min_length=3, max_length=2000)
    project: str = "untitled"
    setting: str = ""
    mode: Mode = Mode.FICTION


class DecisionRequest(BaseModel):
    claim_id: str
    disposition: Disposition
    rationale: str = ""
    decided_by: str = "writer"


@app.get("/api/health")
def health() -> dict:
    """Also surfaces whether Parallel is live, so a demo can never pass off
    fixture data as real search without saying so."""
    return {
        "status": "ok",
        "model": MODEL,
        "project": PROJECT_ID or None,
        "parallel_live": parallel_client.is_live(),
        "ledger": get_ledger().backend,
        "image_enabled": ENABLE_IMAGE,
    }


@app.post("/api/scenes")
async def create_scene(req: DraftRequest) -> Scene:
    """Draft a scene, then extract and check every claim in it."""
    scene = await orchestrator.draft_scene(
        intent=req.intent, project=req.project, mode=req.mode, setting=req.setting
    )
    if not scene.text:
        raise HTTPException(502, "Scene drafting failed — check model credentials.")
    return await orchestrator.check_claims(scene)


@app.post("/api/scenes/demo")
async def create_demo_scene() -> Scene:
    """Load the pinned sample scene. Lets the full loop be demonstrated with no
    API keys; the UI labels it as sample data."""
    return await orchestrator.load_demo_scene()


@app.get("/api/scenes")
def list_scenes() -> list[Scene]:
    return get_ledger().list_scenes()


@app.get("/api/scenes/{scene_id}")
def get_scene(scene_id: str) -> Scene:
    scene = get_ledger().get_scene(scene_id)
    if scene is None:
        raise HTTPException(404, "No such scene.")
    return scene


@app.post("/api/scenes/{scene_id}/decide")
async def decide(scene_id: str, req: DecisionRequest) -> Scene:
    """Record the human's decision on one flag, and revise if they chose to fix."""
    scene = get_ledger().get_scene(scene_id)
    if scene is None:
        raise HTTPException(404, "No such scene.")
    if req.disposition == Disposition.KEEP_DELIBERATE and not req.rationale.strip():
        # The rationale is the product. Keeping something deliberately without
        # saying why defeats the entire audit trail.
        raise HTTPException(400, "A rationale is required to keep this deliberately.")
    return await orchestrator.decide(
        scene=scene,
        claim_id=req.claim_id,
        disposition=req.disposition,
        rationale=req.rationale,
        decided_by=req.decided_by,
    )


@app.get("/api/scenes/{scene_id}/provenance")
def provenance(scene_id: str) -> list:
    """The audit trail: what was checked, decided, and why."""
    return get_ledger().revisions(scene_id)


# --- static UI --------------------------------------------------------------

if FRONTEND.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(str(FRONTEND / "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
