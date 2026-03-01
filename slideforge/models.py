"""Pydantic data models for presentations and slides."""

from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field


class PresentationStyle(str, Enum):
    """Bullet point writing style for slide content."""

    KEYWORDS = "keywords"  # single words / short phrases, no full sentences
    SENTENCES = "sentences"  # one complete sentence per bullet, 8-15 words
    ACADEMIC = "academic"  # full sentences, precise terminology, references where relevant


class Slide(BaseModel):
    """One slide in a presentation."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    layout: str = "SP_Content"
    title: str = ""
    body: str = ""  # newline-separated bullets or prose
    notes: str = ""  # speaker notes (not rendered to slide)
    style: PresentationStyle | None = None  # None = inherit from presentation

    def resolved_style(self, presentation_style: PresentationStyle) -> PresentationStyle:
        """Return slide override if set, otherwise the presentation-level style."""
        return self.style if self.style is not None else presentation_style


class Presentation(BaseModel):
    """A complete presentation (list of slides + metadata)."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = "Untitled"
    slides: list[Slide] = Field(default_factory=list)
    style: PresentationStyle = PresentationStyle.SENTENCES
