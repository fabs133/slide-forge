"""Tests for slideforge.models."""
from __future__ import annotations

from slideforge.models import Presentation, Slide


def test_slide_default_id():
    """Test Slide class default ID generation.

    :param id: ID of the slide.
    :type id: str
    :return: None
    :rtype: None

    Test Slide class with all fields set.

    :param id: ID of the slide.
    :type id: str
    :param layout: Layout of the slide.
    :type layout: str
    :param title: Title of the slide.
    :type title: str
    :param body: Body content of the slide.
    :type body: str
    :param notes: Notes for the slide.
    :type notes: str
    :return: None
    :rtype: None
    """
    s = Slide()
    assert len(s.id) == 8


def test_slide_all_fields():
    """Test that all fields of a Slide object are set correctly.

    :param layout: The layout of the slide.
    :type layout: str
    :param title: The title of the slide.
    :type title: str
    :param body: The body text of the slide.
    :type body: str
    :param notes: The notes for the slide.
    :type notes: str
    """
    s = Slide(id="abc", layout="SP_Title", title="Hi", body="Body", notes="Notes")
    assert s.layout == "SP_Title"
    assert s.title == "Hi"
    assert s.body == "Body"
    assert s.notes == "Notes"


def test_presentation_default_id():
    """Test a presentation with default ID.

    :param sample_presentation: A sample presentation instance.
    :type sample_presentation: Presentation
    :return: None
    :rtype: None
    :raises ExceptionType: Not applicable.
    """
    p = Presentation()
    assert len(p.id) == 12
    assert p.name == "Untitled"
    assert p.slides == []


def test_json_round_trip(sample_presentation):
    """Test JSON round trip for a presentation model.

    :param sample_presentation: The presentation object to serialize and deserialize.
    :type sample_presentation: Presentation
    :raises AssertionError: If the deserialized presentation does not match the original.
    """
    json_str = sample_presentation.model_dump_json()
    restored = Presentation.model_validate_json(json_str)
    assert restored.id == sample_presentation.id
    assert restored.name == sample_presentation.name
    assert len(restored.slides) == 3
    assert restored.slides[0].layout == "SP_Title"
    assert restored.slides[1].body == "Bullet 1\nBullet 2\nBullet 3"


def test_empty_presentation():
    """Test an empty presentation.

    :param name: Name of the presentation.
    :type name: str
    :return: None
    :rtype: None
    """
    p = Presentation(name="Empty")
    assert p.slides == []
    json_str = p.model_dump_json()
    restored = Presentation.model_validate_json(json_str)
    assert restored.slides == []
