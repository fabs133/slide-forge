"""Tests for slideforge.template_loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from slideforge.template_loader import (
    TemplateConfigError,
    TemplateLayoutError,
    load_template,
)

TEMPLATE_DIR = Path(__file__).parent.parent / "slideforge" / "templates" / "default"


@pytest.fixture
def valid_config(tmp_path):
    """Create a minimal valid config.json for testing."""
    layouts = {
        name: {"title_ph": 0, "body_ph": 1 if name != "SP_SectionBreak" else None}
        for name in ["SP_Title", "SP_Content", "SP_Intro", "SP_Closing", "SP_Sources", "SP_SectionBreak", "SP_Code"]
    }
    config = {"version": 1, "layouts": layouts}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return tmp_path


def test_load_template_valid(valid_config):
    """Test loading a valid template configuration."""
    loader = load_template(valid_config)
    assert "SP_Title" in loader.layouts
    assert "SP_Code" in loader.layouts
    assert loader.layouts["SP_SectionBreak"].body_ph is None
    assert loader.layouts["SP_Content"].body_ph == 1


def test_missing_config_raises(tmp_path):
    """Test that a TemplateConfigError is raised when the configuration file is missing."""
    with pytest.raises(TemplateConfigError, match="not found"):
        load_template(tmp_path)


def test_wrong_version_raises(tmp_path):
    """Tests that an unsupported config version raises TemplateConfigError."""
    config = {"version": 99, "layouts": {}}
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(TemplateConfigError, match="version"):
        load_template(tmp_path)


def test_missing_layout_raises(tmp_path):
    """Tests that a missing required layout raises TemplateConfigError."""
    layouts = {"SP_Title": {"title_ph": 0, "body_ph": 1}}
    config = {"version": 1, "layouts": layouts}
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(TemplateConfigError, match="missing required"):
        load_template(tmp_path)


@pytest.mark.skipif(not TEMPLATE_DIR.exists(), reason="Template not generated")
def test_generated_template_has_all_layouts():
    """Tests that the generated template contains all required slide layouts."""
    loader = load_template(TEMPLATE_DIR)
    prs = loader.open_presentation()
    layout_names = {sl.name for sl in prs.slide_layouts if sl.name.startswith("SP_")}
    assert layout_names == {
        "SP_Title",
        "SP_Content",
        "SP_Intro",
        "SP_Closing",
        "SP_Sources",
        "SP_SectionBreak",
        "SP_Code",
    }


@pytest.mark.skipif(not TEMPLATE_DIR.exists(), reason="Template not generated")
def test_get_layout_by_name():
    """Tests retrieving a layout by name."""
    loader = load_template(TEMPLATE_DIR)
    prs = loader.open_presentation()
    layout = loader.get_layout(prs, "SP_Content")
    assert layout.name == "SP_Content"


@pytest.mark.skipif(not TEMPLATE_DIR.exists(), reason="Template not generated")
def test_get_layout_unknown_raises():
    """Test that calling get_layout with an unknown layout raises a TemplateLayoutError."""
    loader = load_template(TEMPLATE_DIR)
    prs = loader.open_presentation()
    with pytest.raises(TemplateLayoutError, match="not found"):
        loader.get_layout(prs, "SP_Nonexistent")
