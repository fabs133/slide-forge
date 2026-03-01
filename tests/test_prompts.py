"""Tests for slideforge.prompts."""

from __future__ import annotations

import pytest

from slideforge.prompts import STYLE_INSTRUCTIONS, get_style_instruction


def test_all_styles_return_non_empty():
    """All defined styles return a non-empty instruction string."""
    for style in ("keywords", "sentences", "academic"):
        result = get_style_instruction(style)
        assert isinstance(result, str)
        assert len(result) > 0


def test_invalid_style_raises_key_error():
    """An invalid style name raises KeyError."""
    with pytest.raises(KeyError):
        get_style_instruction("nonexistent_style")


def test_style_instructions_has_expected_keys():
    """STYLE_INSTRUCTIONS contains exactly the expected keys."""
    assert set(STYLE_INSTRUCTIONS.keys()) == {"keywords", "sentences", "academic"}
