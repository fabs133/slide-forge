"""Tests for slideforge.storage."""
from __future__ import annotations

import pytest

from slideforge.models import Presentation
from slideforge.storage import ProjectStore


def test_save_and_get(store, sample_presentation):
    """Saves a presentation to the store and retrieves it to verify correctness."""
    store.save(sample_presentation)
    loaded = store.get(sample_presentation.id)
    assert loaded is not None
    assert loaded.id == sample_presentation.id
    assert loaded.name == "Test Deck"
    assert len(loaded.slides) == 3


def test_list_projects(store, sample_presentation):
    """Tests listing projects."""
    store.save(sample_presentation)
    second = Presentation(id="second", name="Second Deck")
    store.save(second)
    projects = store.list_projects()
    assert len(projects) == 2
    names = {p.name for p in projects}
    assert names == {"Test Deck", "Second Deck"}


def test_get_missing_returns_none(store):
    """Tests retrieving a non-existent item returns None."""
    assert store.get("nonexistent") is None


def test_delete_existing(store, sample_presentation):
    """Test deleting an existing presentation."""
    store.save(sample_presentation)
    assert store.delete(sample_presentation.id) is True
    assert store.get(sample_presentation.id) is None


def test_delete_missing_returns_false(store):
    """Tests that deleting a non-existent item returns False."""
    assert store.delete("nonexistent") is False


def test_save_overwrites(store, sample_presentation):
    """Tests that saving a presentation overwrites the existing one in the store."""
    store.save(sample_presentation)
    sample_presentation.name = "Updated Name"
    store.save(sample_presentation)
    loaded = store.get(sample_presentation.id)
    assert loaded.name == "Updated Name"


def test_store_creates_directory(tmp_path):
    """Creates a new directory and initializes a ProjectStore with it."""
    new_dir = tmp_path / "new" / "nested"
    s = ProjectStore(new_dir)
    assert new_dir.exists()
    p = Presentation(id="test", name="Test")
    s.save(p)
    assert s.get("test").name == "Test"


def test_path_traversal_raises(store):
    """Tests that a path-traversal project ID raises ValueError."""
    with pytest.raises(ValueError, match="Invalid project ID"):
        store.get("../../etc/passwd")

    with pytest.raises(ValueError, match="Invalid project ID"):
        store.get("../secrets")

    with pytest.raises(ValueError, match="Invalid project ID"):
        store.get("foo/bar")
