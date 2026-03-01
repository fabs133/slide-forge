"""JSON-file storage backend for presentations."""

from __future__ import annotations

import re
from pathlib import Path

from .models import Presentation


class ProjectStore:
    """CRUD operations on presentations stored as JSON files."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize the project store.

        :param base_dir: Directory where presentation JSON files are stored.
        :type base_dir: Path
        """
        self._dir = base_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, project_id: str) -> Path:
        """Return the file path for a project's JSON file.

        :param project_id: The project ID.
        :type project_id: str
        :return: Path to the project's JSON file.
        :rtype: Path
        :raises ValueError: If the project ID contains unsafe characters.
        """
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", project_id):
            raise ValueError(f"Invalid project ID: {project_id}")
        return self._dir / f"{project_id}.json"

    def list_projects(self) -> list[Presentation]:
        """Return all saved presentations."""
        results = []
        for p in sorted(self._dir.glob("*.json")):
            try:
                results.append(Presentation.model_validate_json(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        return results

    def get(self, project_id: str) -> Presentation | None:
        """Load a presentation by ID, or None if not found."""
        path = self._path(project_id)
        if not path.exists():
            return None
        return Presentation.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, presentation: Presentation) -> None:
        """Write (or overwrite) the presentation to disk."""
        path = self._path(presentation.id)
        path.write_text(presentation.model_dump_json(indent=2), encoding="utf-8")

    def delete(self, project_id: str) -> bool:
        """Delete a presentation. Returns True if it existed."""
        path = self._path(project_id)
        if not path.exists():
            return False
        path.unlink()
        return True
