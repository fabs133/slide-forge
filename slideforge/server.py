"""FastAPI server — REST API for presentation CRUD and PPTX export."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.background import BackgroundTask

from .models import Presentation
from .renderer import render_pptx
from .storage import ProjectStore


class CreateProjectRequest(BaseModel):
    """Request body for creating a new project."""

    name: str = "Untitled"


app = FastAPI(title="Slide Forge", version="0.1.0")

_PROJECTS_DIR = Path(__file__).parent.parent / "projects"
store = ProjectStore(_PROJECTS_DIR)

# Available layouts (populated on first request or at import time)
_LAYOUT_NAMES = [
    "SP_Title",
    "SP_Content",
    "SP_Intro",
    "SP_Closing",
    "SP_Sources",
    "SP_SectionBreak",
    "SP_Code",
]


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------


@app.get("/api/projects")
def list_projects():
    """List all presentations (summary only)."""
    return [{"id": p.id, "name": p.name, "slide_count": len(p.slides)} for p in store.list_projects()]


@app.post("/api/projects", status_code=201)
def create_project(body: CreateProjectRequest):
    """Create a new presentation."""
    pres = Presentation(name=body.name)
    store.save(pres)
    return pres.model_dump()


@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    """Load a full presentation by ID."""
    pres = store.get(project_id)
    if not pres:
        raise HTTPException(404, "Project not found")
    return pres.model_dump()


@app.put("/api/projects/{project_id}")
def update_project(project_id: str, body: Presentation):
    """Full replacement save of a presentation."""
    if body.id != project_id:
        raise HTTPException(400, "ID in body does not match URL")
    store.save(body)
    return body.model_dump()


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: str):
    """Delete a presentation."""
    if not store.delete(project_id):
        raise HTTPException(404, "Project not found")


# ---------------------------------------------------------------------------
# Approval (used by schulpipeline --review flow)
# ---------------------------------------------------------------------------

_approved: dict[str, bool] = {}


@app.post("/api/projects/{project_id}/approve", status_code=200)
def approve_project(project_id: str):
    """Mark a project as approved (user clicked 'Fertig')."""
    pres = store.get(project_id)
    if not pres:
        raise HTTPException(404, "Project not found")
    _approved[project_id] = True
    return {"approved": True}


@app.get("/api/projects/{project_id}/approved")
def check_approved(project_id: str):
    """Check if a project has been approved."""
    return {"approved": _approved.get(project_id, False)}


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


@app.get("/api/projects/{project_id}/export")
def export_pptx(project_id: str):
    """Render and download as .pptx."""
    pres = store.get(project_id)
    if not pres:
        raise HTTPException(404, "Project not found")
    tmp = tempfile.NamedTemporaryFile(suffix=".pptx", delete=False)
    tmp.close()
    render_pptx(pres, Path(tmp.name))
    return FileResponse(
        tmp.name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"{pres.name}.pptx",
        background=BackgroundTask(os.unlink, tmp.name),
    )


# ---------------------------------------------------------------------------
# Layout metadata
# ---------------------------------------------------------------------------


@app.get("/api/layouts")
def list_layouts():
    """List available slide layout names."""
    return _LAYOUT_NAMES


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------

_FRONTEND = Path(__file__).parent.parent / "frontend"
if _FRONTEND.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND), html=True), name="frontend")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main():
    """Starts the SlideForge server using Uvicorn."""
    import uvicorn

    uvicorn.run("slideforge.server:app", host="127.0.0.1", port=8000, reload=True)
