"""Template loader — validates and exposes a .pptx template directory.

A template directory contains:
  slides.pptx   — PowerPoint file with named slide layouts
  config.json   — placeholder index mapping per layout name

Usage::

    loader = load_template(Path("slideforge/templates/default"))
    prs = loader.open_presentation()
    layout = loader.get_layout(prs, "SP_Content")
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pptx import Presentation
from pptx.slide import SlideLayout

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class TemplateError(Exception):
    """Base error for template loading failures."""


class TemplateConfigError(TemplateError):
    """Raised when config.json is missing or malformed."""


class TemplateLayoutError(TemplateError):
    """Raised when a required layout is not found in the .pptx file."""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemplateLayout:
    """Placeholder index mapping for one named layout."""

    name: str  # e.g. "SP_Title"
    title_ph: int  # placeholder idx for heading
    body_ph: int | None  # placeholder idx for body, None if absent


# ---------------------------------------------------------------------------
# TemplateLoader
# ---------------------------------------------------------------------------


class TemplateLoader:
    """Loads and validates a template directory for use by the renderer."""

    REQUIRED_LAYOUTS: frozenset[str] = frozenset({
        "SP_Title",
        "SP_Content",
        "SP_Intro",
        "SP_Closing",
        "SP_Sources",
        "SP_SectionBreak",
        "SP_Code",
    })

    def __init__(self, directory: Path, layouts: dict[str, TemplateLayout]) -> None:
        """Initialize the TemplateLoader with a directory and layout templates.

        :param directory: The path to the directory containing slide files.
        :type directory: Path
        :param layouts: A dictionary of template layouts keyed by layout name.
        :type layouts: dict[str, TemplateLayout]
        """
        self._dir = directory
        self.layouts = layouts

    @property
    def slides_path(self) -> Path:
        """Returns the path to the slides.pptx file."""
        return self._dir / "slides.pptx"

    def open_presentation(self) -> Presentation:
        """Open slides.pptx as a fresh Presentation instance.

        Each call returns a new object — the template file is never mutated.
        """
        if not self.slides_path.exists():
            raise TemplateError(f"Template file not found: {self.slides_path}")
        return Presentation(str(self.slides_path))

    def get_layout(self, prs: Presentation, name: str) -> SlideLayout:
        """Find a slide layout by name in the presentation.

        Raises:
            TemplateLayoutError: If the layout name is not found.
        """
        for layout in prs.slide_layouts:
            if layout.name == name:
                return layout
        raise TemplateLayoutError(
            f"Layout '{name}' not found. Available: {[sl.name for sl in prs.slide_layouts]}"
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def load_template(directory: Path) -> TemplateLoader:
    """Load and validate a template directory.

    Reads config.json and validates its structure. Does NOT open slides.pptx
    (that happens lazily in ``open_presentation()``).

    Args:
        directory: Path to a template directory containing config.json
                   and slides.pptx.

    Raises:
        TemplateConfigError: If config.json is missing or malformed.
    """
    config_path = directory / "config.json"

    if not config_path.exists():
        raise TemplateConfigError(f"Template config not found: {config_path}")

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    _validate_config(raw, config_path)

    layouts: dict[str, TemplateLayout] = {}
    for name, data in raw["layouts"].items():
        layouts[name] = TemplateLayout(
            name=name,
            title_ph=data["title_ph"],
            body_ph=data.get("body_ph"),
        )

    return TemplateLoader(directory, layouts)


def _validate_config(raw: dict, path: Path) -> None:
    """Validate config.json structure."""
    if raw.get("version") != 1:
        raise TemplateConfigError(f"{path}: expected 'version': 1")

    if "layouts" not in raw:
        raise TemplateConfigError(f"{path}: missing 'layouts' key")

    missing = TemplateLoader.REQUIRED_LAYOUTS - set(raw["layouts"].keys())
    if missing:
        raise TemplateConfigError(f"{path}: missing required layouts: {sorted(missing)}")

    for name, data in raw["layouts"].items():
        if "title_ph" not in data:
            raise TemplateConfigError(f"{path}: layout '{name}' missing 'title_ph'")
        if not isinstance(data["title_ph"], int):
            raise TemplateConfigError(f"{path}: layout '{name}' title_ph must be int, got {data['title_ph']!r}")
