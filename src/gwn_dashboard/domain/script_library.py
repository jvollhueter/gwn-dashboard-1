"""Domain models for the internal script library."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class ScriptLibraryItem:
    """One downloadable script or multi-file tool."""

    item_id: str
    title: str
    short_description: str
    long_description: str
    category: str
    tags: tuple[str, ...]
    language: str
    item_type: str
    author: str
    version: str
    updated: date
    source_path: Path
    download_filename: str
    entry_point: str | None = None
    requires_runtime: str | None = None
    dependencies: tuple[str, ...] = ()
    input_formats: tuple[str, ...] = ()
    output_formats: tuple[str, ...] = ()
    readme_path: Path | None = None
    file_count: int = 1

    @property
    def type_label(self) -> str:
        """Return a user-facing label for the publication type."""

        labels = {
            "single_script": "Einzeldatei",
            "notebook": "Jupyter-Notebook",
            "script_package": "Werkzeug-Paket",
        }
        return labels.get(self.item_type, self.item_type)

    @property
    def search_text(self) -> str:
        """Return all searchable metadata as one string."""

        values = (
            self.item_id,
            self.title,
            self.short_description,
            self.long_description,
            self.category,
            self.language,
            self.type_label,
            self.author,
            self.version,
            self.entry_point or "",
            *self.tags,
            *self.dependencies,
            *self.input_formats,
            *self.output_formats,
        )
        return " ".join(values)
