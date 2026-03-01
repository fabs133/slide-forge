"""Tests for slideforge.server."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from slideforge.server import app
from slideforge.storage import ProjectStore

TEMPLATE_DIR = Path(__file__).parent.parent / "slideforge" / "templates" / "default"


@pytest.fixture
def client(tmp_path):
    """TestClient with a temporary project store."""
    test_store = ProjectStore(tmp_path / "projects")
    with patch("slideforge.server.store", test_store):
        yield TestClient(app)


@pytest.fixture
def client_with_project(client, tmp_path):
    """Client + a pre-saved project."""
    resp = client.post("/api/projects", json={"name": "Test Deck"})
    assert resp.status_code == 201
    project = resp.json()
    return client, project


def test_create_and_list(client):
    """Test creating a project and listing all projects."""
    resp = client.post("/api/projects", json={"name": "My Deck"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Deck"
    assert "id" in data

    resp = client.get("/api/projects")
    assert resp.status_code == 200
    projects = resp.json()
    assert len(projects) == 1
    assert projects[0]["name"] == "My Deck"


def test_get_project(client_with_project):
    """Tests retrieving a project by ID."""
    client, project = client_with_project
    resp = client.get(f"/api/projects/{project['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Deck"


def test_update_project(client_with_project):
    """Updates an existing project with new details."""
    client, project = client_with_project
    project["name"] = "Updated Deck"
    project["slides"] = [
        {"id": "s1", "layout": "SP_Title", "title": "Hello", "body": "", "notes": ""},
    ]
    resp = client.put(f"/api/projects/{project['id']}", json=project)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Deck"
    assert len(resp.json()["slides"]) == 1


def test_delete_project(client_with_project):
    """Deletes a project and verifies its removal."""
    client, project = client_with_project
    resp = client.delete(f"/api/projects/{project['id']}")
    assert resp.status_code == 204
    resp = client.get(f"/api/projects/{project['id']}")
    assert resp.status_code == 404


def test_get_missing_project_404(client):
    """Test that getting a non-existent project returns 404."""
    resp = client.get("/api/projects/nonexistent")
    assert resp.status_code == 404


def test_delete_missing_project_404(client):
    """Test that deleting a non-existent project returns 404."""
    resp = client.delete("/api/projects/nonexistent")
    assert resp.status_code == 404


def test_update_id_mismatch(client_with_project):
    """Tests updating a project with an ID mismatch returns 400."""
    client, project = client_with_project
    project["id"] = "wrong_id"
    resp = client.put("/api/projects/original_id", json=project)
    assert resp.status_code == 400


def test_list_layouts(client):
    """Test the list of layouts endpoint."""
    resp = client.get("/api/layouts")
    assert resp.status_code == 200
    layouts = resp.json()
    assert "SP_Title" in layouts
    assert "SP_Code" in layouts
    assert len(layouts) == 7


@pytest.mark.skipif(not TEMPLATE_DIR.exists(), reason="Template not generated")
def test_export_pptx(client_with_project):
    """Test exporting a project as PPTX."""
    client, project = client_with_project
    # Add a slide first
    project["slides"] = [
        {"id": "s1", "layout": "SP_Content", "title": "Test", "body": "Content", "notes": ""},
    ]
    client.put(f"/api/projects/{project['id']}", json=project)

    resp = client.get(f"/api/projects/{project['id']}/export")
    assert resp.status_code == 200
    assert "openxmlformats" in resp.headers["content-type"]
    assert len(resp.content) > 0


def test_export_missing_project_404(client):
    """Test exporting a non-existent project returns 404."""
    resp = client.get("/api/projects/nonexistent/export")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Approval endpoint tests
# ---------------------------------------------------------------------------


def test_approved_default_false(client_with_project):
    """New project is not approved by default."""
    client, project = client_with_project
    resp = client.get(f"/api/projects/{project['id']}/approved")
    assert resp.status_code == 200
    assert resp.json()["approved"] is False


def test_approve_project(client_with_project):
    """Approve a project and verify it's marked as approved."""
    client, project = client_with_project
    resp = client.post(f"/api/projects/{project['id']}/approve")
    assert resp.status_code == 200
    assert resp.json()["approved"] is True

    resp = client.get(f"/api/projects/{project['id']}/approved")
    assert resp.status_code == 200
    assert resp.json()["approved"] is True


def test_approve_missing_project_404(client):
    """Approving a non-existent project returns 404."""
    resp = client.post("/api/projects/nonexistent/approve")
    assert resp.status_code == 404
