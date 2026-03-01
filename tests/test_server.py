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
    """Test creating a project and listing all projects.

    :param client: HTTP client for making requests.
    :type client: object
    :return: None
    :rtype: None
    """
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
    """Tests the retrieval and update of a project.

    :param client_with_project: A tuple containing a client instance and a project dictionary.
    :type client_with_project: tuple[Client, dict]
    :return: None
    :rtype: None
    """
    client, project = client_with_project
    resp = client.get(f"/api/projects/{project['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Deck"


def test_update_project(client_with_project):
    """Updates an existing project with new details.

    :param client_with_project: A tuple containing a client and a project dictionary.
    :type client_with_project: tuple
    :return: None
    :rtype: None
    """
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
    """Deletes a project and verifies its removal.

    :param client_with_project: A tuple containing the client and project to be deleted.
    :type client_with_project: tuple
    :raises AssertionError: If the deletion or verification fails.
    """
    client, project = client_with_project
    resp = client.delete(f"/api/projects/{project['id']}")
    assert resp.status_code == 204
    resp = client.get(f"/api/projects/{project['id']}")
    assert resp.status_code == 404


def test_get_missing_project_404(client):
    """Test that attempting to get a non-existent project returns a 404 status code.

    :param client: The test client for making requests.
    :type client: FlaskClient

    :return: None
    :rtype: None

    :raises AssertionError: If the response status code is not 404.
    """
    resp = client.get("/api/projects/nonexistent")
    assert resp.status_code == 404


def test_delete_missing_project_404(client):
    """Deletes a non-existent project and returns a 404 status code.

    :param client: API client for making requests.
    :type client: object

    :raises AssertionError: If the response status code is not 404.
    """
    resp = client.delete("/api/projects/nonexistent")
    assert resp.status_code == 404


def test_update_id_mismatch(client_with_project):
    """Tests updating a project with an ID mismatch.

    :param client_with_project: A tuple containing the client and project objects.
    :type client_with_project: tuple[Client, dict]
    :raises AssertionError: If the response status code is not 400.
    """
    client, project = client_with_project
    project["id"] = "wrong_id"
    resp = client.put(f"/api/projects/{project['id']}", json=project)
    # ID in URL won't match body
    # Actually the URL has "wrong_id" now — let's use original URL
    resp = client.put("/api/projects/original_id", json=project)
    assert resp.status_code == 400


def test_list_layouts(client):
    """Test the list of layouts endpoint.

    :param client: The API client to use for making requests.
    :type client: object
    :return: None
    :rtype: None
    :raises AssertionError: If the response status code is not 200 or if the expected layouts are missing.
    """
    resp = client.get("/api/layouts")
    assert resp.status_code == 200
    layouts = resp.json()
    assert "SP_Title" in layouts
    assert "SP_Code" in layouts
    assert len(layouts) == 7


@pytest.mark.skipif(not TEMPLATE_DIR.exists(), reason="Template not generated")
def test_export_pptx(client_with_project):
    """Test exporting a PowerPoint file from a project.

    :param client_with_project: A tuple containing the client and project objects.
    :type client_with_project: tuple
    :return: None
    :rtype: None
    :raises AssertionError: If the response status code is not 200 or if the content type does not contain "openxmlformats".
    """
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
    """Test exporting a non-existent project should return a 404 error.

    :param client: The test client to make requests with.
    :type client: FlaskClient
    :return: None
    :rtype: None
    :raises AssertionError: If the response status code is not 404.
    """
    resp = client.get("/api/projects/nonexistent/export")
    assert resp.status_code == 404
