"""Shared test fixtures for slide-forge."""
from __future__ import annotations

import pytest

from slideforge.models import Presentation, Slide
from slideforge.storage import ProjectStore


@pytest.fixture
def sample_presentation() -> Presentation:
    """Returns a new `Presentation` object with predefined slides.

    :param id: The unique identifier for the presentation.
    :type id: str
    :param name: The name of the presentation.
    :type name: str
    :return: A new `Presentation` object initialized with specific slides.
    :rtype: Presentation
    """
    return Presentation(
        id="test123",
        name="Test Deck",
        slides=[
            Slide(id="s1", layout="SP_Title", title="Welcome", body="Subtitle here"),
            Slide(id="s2", layout="SP_Content", title="Main Point", body="Bullet 1\nBullet 2\nBullet 3"),
            Slide(id="s3", layout="SP_Sources", title="Sources", body="Source A\nSource B"),
        ],
    )


@pytest.fixture
def store(tmp_path) -> ProjectStore:
    """Stores projects in a specified directory.

    :param tmp_path: Temporary path where projects will be stored.
    :type tmp_path: Path
    :return: ProjectStore instance initialized with the given path.
    :rtype: ProjectStore
    """
    return ProjectStore(tmp_path / "projects")
