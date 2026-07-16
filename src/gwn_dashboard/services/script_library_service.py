"""Search, filter and package entries of the script library."""

from __future__ import annotations

import io
import unicodedata
import zipfile
from pathlib import Path

from gwn_dashboard.domain.script_library import ScriptLibraryItem
from gwn_dashboard.repositories.script_library_repository import ScriptLibraryRepository


class ScriptLibraryService:
    """Provide a safe catalogue and download data for the UI."""

    def __init__(self, repository: ScriptLibraryRepository) -> None:
        self._repository = repository

    def load_catalogue(self) -> tuple[ScriptLibraryItem, ...]:
        """Load all valid script-library items.
        
        Returns:
            tuple[ScriptLibraryItem, ...]: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        return self._repository.load_items()

    def find_by_id(
        self,
        catalogue: tuple[ScriptLibraryItem, ...],
        item_id: str,
    ) -> ScriptLibraryItem | None:
        """Find one catalogue item by its stable identifier.
        
        Args:
            catalogue: Value of type ``tuple[ScriptLibraryItem, ...]``.
            item_id: Value of type ``str``.
        
        Returns:
            ScriptLibraryItem | None: Result produced by the operation.
        """
        return next((item for item in catalogue if item.item_id == item_id), None)

    def filter_items(
        self,
        catalogue: tuple[ScriptLibraryItem, ...],
        *,
        query: str = "",
        category: str = "Alle Kategorien",
        language: str = "Alle Sprachen",
        item_type: str = "Alle Typen",
        tags: tuple[str, ...] = (),
    ) -> tuple[ScriptLibraryItem, ...]:
        """Filter catalogue items by text query and structured criteria.
        
        Args:
            catalogue: Value of type ``tuple[ScriptLibraryItem, ...]``.
            query: Value of type ``str``.
            category: Value of type ``str``.
            language: Value of type ``str``.
            item_type: Value of type ``str``.
            tags: Value of type ``tuple[str, ...]``.
        
        Returns:
            tuple[ScriptLibraryItem, ...]: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        terms = [term for term in self._normalise(query).split() if term]
        result: list[ScriptLibraryItem] = []
        for item in catalogue:
            haystack = self._normalise(item.search_text)
            if terms and not all(term in haystack for term in terms):
                continue
            if category != "Alle Kategorien" and item.category != category:
                continue
            if language != "Alle Sprachen" and item.language != language:
                continue
            if item_type != "Alle Typen" and item.type_label != item_type:
                continue
            if tags and not set(tags).issubset(item.tags):
                continue
            result.append(item)
        return tuple(result)

    def build_download(self, item: ScriptLibraryItem) -> tuple[bytes, str, str]:
        """Return bytes, filename and MIME type for a publication."""

        if item.item_type != "script_package":
            return (
                item.source_path.read_bytes(),
                item.download_filename,
                self._mime_type(item.source_path),
            )

        buffer = io.BytesIO()
        root_name = item.source_path.name
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in self._repository.download_files(item):
                if path.is_dir():
                    continue
                relative = Path(root_name) / path.relative_to(item.source_path)
                archive.write(path, relative.as_posix())
        return buffer.getvalue(), item.download_filename, "application/zip"

    @staticmethod
    def read_readme(item: ScriptLibraryItem) -> str | None:
        """Read an optional README associated with a library item.
        
        Args:
            item: Value of type ``ScriptLibraryItem``.
        
        Returns:
            str | None: Result produced by the operation.
        """
        if item.readme_path is None:
            return None
        return item.readme_path.read_text(encoding="utf-8")

    @staticmethod
    def categories(catalogue: tuple[ScriptLibraryItem, ...]) -> tuple[str, ...]:
        """Return sorted unique catalogue categories.
        
        Args:
            catalogue: Value of type ``tuple[ScriptLibraryItem, ...]``.
        
        Returns:
            tuple[str, ...]: Result produced by the operation.
        """
        return tuple(sorted({item.category for item in catalogue}, key=str.casefold))

    @staticmethod
    def languages(catalogue: tuple[ScriptLibraryItem, ...]) -> tuple[str, ...]:
        """Return sorted unique programming languages.
        
        Args:
            catalogue: Value of type ``tuple[ScriptLibraryItem, ...]``.
        
        Returns:
            tuple[str, ...]: Result produced by the operation.
        """
        order = {"Python": 0, "R": 1, "Jupyter": 2}
        return tuple(sorted({item.language for item in catalogue}, key=lambda value: order.get(value, 99)))

    @staticmethod
    def types(catalogue: tuple[ScriptLibraryItem, ...]) -> tuple[str, ...]:
        """Return sorted unique publication types.
        
        Args:
            catalogue: Value of type ``tuple[ScriptLibraryItem, ...]``.
        
        Returns:
            tuple[str, ...]: Result produced by the operation.
        """
        return tuple(sorted({item.type_label for item in catalogue}, key=str.casefold))

    @staticmethod
    def tags(catalogue: tuple[ScriptLibraryItem, ...]) -> tuple[str, ...]:
        """Return sorted unique tags.
        
        Args:
            catalogue: Value of type ``tuple[ScriptLibraryItem, ...]``.
        
        Returns:
            tuple[str, ...]: Result produced by the operation.
        """
        return tuple(sorted({tag for item in catalogue for tag in item.tags}))

    @staticmethod
    def _normalise(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold())
        return "".join(character for character in decomposed if not unicodedata.combining(character))

    @staticmethod
    def _mime_type(path: Path) -> str:
        return {
            ".py": "text/x-python",
            ".r": "text/x-r-source",
            ".ipynb": "application/x-ipynb+json",
        }.get(path.suffix.lower(), "application/octet-stream")
