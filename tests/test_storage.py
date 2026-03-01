"""Tests for slideforge.storage."""
from __future__ import annotations

from slideforge.models import Presentation
from slideforge.storage import ProjectStore


def test_save_and_get(store, sample_presentation):
    """Saves a presentation to the store and retrieves it to verify correctness.

    :param store: The storage object where presentations are saved.
    :type store: PresentationStore
    :param sample_presentation: The presentation to save and retrieve.
    :type sample_presentation: Presentation
    :return: None
    :rtype: None
    :raises AssertionError: If the retrieved presentation does not match the original.
    """
    store.save(sample_presentation)
    loaded = store.get(sample_presentation.id)
    assert loaded is not None
    assert loaded.id == sample_presentation.id
    assert loaded.name == "Test Deck"
    assert len(loaded.slides) == 3


def test_list_projects(store, sample_presentation):
    """Tests listing projects.

    :param store: The storage instance to interact with.
    :type store: PresentationStore
    :param sample_presentation: A sample presentation to save before testing.
    :type sample_presentation: Presentation

    :raises AssertionError: If the number of projects or their names do not match expectations.
    """

    """
    Tests retrieving a missing project.

    :param store: The storage instance to interact with.
    :type store: PresentationStore

    :return: None
    :rtype: None
    """
    store.save(sample_presentation)
    second = Presentation(id="second", name="Second Deck")
    store.save(second)
    projects = store.list_projects()
    assert len(projects) == 2
    names = {p.name for p in projects}
    assert names == {"Test Deck", "Second Deck"}


def test_get_missing_returns_none(store):
    """Tests for the storage operations.

    :param store: The storage instance to be tested.
    :type store: Storage

    :return: None
    """

    def test_get_missing_returns_none(store):
        """
        Tests retrieving a non-existent item from the store.

        :param store: The storage instance to be tested.
        :type store: Storage

        :return: None
        """

    def test_delete_existing(store, sample_presentation):
        """
        Tests deleting an existing item from the store.

        :param store: The storage instance to be tested.
        :type store: Storage
        :param sample_presentation: A presentation object to save and delete.
        :type sample_presentation: Presentation

        :return: None
        """

    def test_delete_missing_returns_false(store):
        """
        Tests deleting a non-existent item from the store.

        :param store: The storage instance to be tested.
        :type store: Storage

        :return: None
    """
    assert store.get("nonexistent") is None


def test_delete_existing(store, sample_presentation):
    """Test deleting an existing presentation.

    :param store: The storage object to use.
    :type store: Storage
    :param sample_presentation: The presentation to save and then delete.
    :type sample_presentation: Presentation

    :return: True if the deletion was successful, False otherwise.
    :rtype: bool
    """

    """
    Test attempting to delete a non-existent presentation.

    :param store: The storage object to use.
    :type store: Storage

    :return: False since the presentation does not exist.
    :rtype: bool
    """

    """
    Test saving and then deleting a presentation.

    :param store: The storage object to use.
    :type store: Storage
    :param sample_presentation: The presentation to save and then delete.
    :type sample_presentation: Presentation
    """
    store.save(sample_presentation)
    assert store.delete(sample_presentation.id) is True
    assert store.get(sample_presentation.id) is None


def test_delete_missing_returns_false(store):
    """Tests the behavior of a storage system when deleting and saving presentations.

    :param store: The storage instance to test.
    :type store: Storage

    :return: None
    :rtype: None

    :raises ExceptionType: Description of exception if any
    """
    assert store.delete("nonexistent") is False


def test_save_overwrites(store, sample_presentation):
    """Tests that saving a presentation overwrites the existing one in the store.

    :param store: The store instance to use for testing.
    :type store: ProjectStore
    :param sample_presentation: The presentation object to save and update.
    :type sample_presentation: Presentation

    :raises AssertionError: If the loaded presentation name does not match the updated name.
    """

    """
    Tests that a new directory is created when initializing the ProjectStore.

    :param tmp_path: Temporary path for creating directories.
    :type tmp_path: pathlib.Path
    """
    store.save(sample_presentation)
    sample_presentation.name = "Updated Name"
    store.save(sample_presentation)
    loaded = store.get(sample_presentation.id)
    assert loaded.name == "Updated Name"


def test_store_creates_directory(tmp_path):
    """Creates a new directory and initializes a ProjectStore with it.

    :param tmp_path: Temporary path for creating the directory.
    :type tmp_path: Path
    """
    new_dir = tmp_path / "new" / "nested"
    s = ProjectStore(new_dir)
    assert new_dir.exists()
    p = Presentation(id="test", name="Test")
    s.save(p)
    assert s.get("test").name == "Test"
