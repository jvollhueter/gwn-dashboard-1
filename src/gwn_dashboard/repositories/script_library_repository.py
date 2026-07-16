"""Read script-library metadata without importing or executing scripts."""

from __future__ import annotations

import json
import re
import tomllib
from datetime import date
from pathlib import Path
from typing import Any

from gwn_dashboard.domain.script_library import ScriptLibraryItem


_COMMENT_BLOCK = re.compile(
    r"(?ms)^# /// (?:script|ref43-script)\s*$\n"
    r"(?P<body>.*?)"
    r"^# ///\s*$"
)
_IGNORED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
_IGNORED_SUFFIXES = {".pyc", ".pyo"}


class ScriptLibraryRepository:
    """Discover validated publications in a configured library directory."""

    def __init__(self, library_root: Path) -> None:
        self._library_root = library_root.resolve()

    @property
    def library_root(self) -> Path:
        """Return the root directory containing publishable library items.
        
        Returns:
            Path: Result produced by the operation.
        """
        return self._library_root

    def load_items(self) -> tuple[ScriptLibraryItem, ...]:
        """Return all valid top-level publications sorted by title."""

        if not self._library_root.exists():
            return ()

        items: list[ScriptLibraryItem] = []
        item_ids: set[str] = set()
        for path in sorted(self._library_root.iterdir(), key=lambda item: item.name.lower()):
            if path.name.startswith(".") or path.name == "README.md":
                continue
            item = self._read_item(path)
            if item is None:
                continue
            if item.item_id in item_ids:
                raise ValueError(f"Doppelte Script-ID: {item.item_id}")
            item_ids.add(item.item_id)
            items.append(item)

        return tuple(sorted(items, key=lambda item: item.title.casefold()))

    def _read_item(self, path: Path) -> ScriptLibraryItem | None:
        if path.is_dir():
            metadata_path = path / "metadata.toml"
            if not metadata_path.is_file():
                return None
            metadata = tomllib.loads(metadata_path.read_text(encoding="utf-8"))
            return self._build_item(
                metadata.get("library", metadata),
                source_path=path,
                item_type="script_package",
                default_language=str(metadata.get("library", metadata).get("language", "")),
                readme_path=(path / "README.md") if (path / "README.md").is_file() else None,
                file_count=sum(1 for file in self._iter_download_files(path) if file.is_file()),
            )

        suffix = path.suffix.lower()
        if suffix in {".py", ".r"}:
            metadata = self._read_comment_metadata(path)
            default_language = "Python" if suffix == ".py" else "R"
            return self._build_item(
                metadata,
                source_path=path,
                item_type="single_script",
                default_language=default_language,
            )

        if suffix == ".ipynb":
            notebook = json.loads(path.read_text(encoding="utf-8"))
            metadata = notebook.get("metadata", {}).get("ref43_library")
            if not isinstance(metadata, dict):
                raise ValueError(f"Notebook-Metadaten fehlen: {path.name}")
            return self._build_item(
                metadata,
                source_path=path,
                item_type="notebook",
                default_language="Jupyter",
            )

        return None

    @staticmethod
    def _read_comment_metadata(path: Path) -> dict[str, Any]:
        source = path.read_text(encoding="utf-8")
        match = _COMMENT_BLOCK.search(source)
        if match is None:
            raise ValueError(f"Metadatenblock fehlt: {path.name}")

        lines: list[str] = []
        for line in match.group("body").splitlines():
            if line.startswith("# "):
                lines.append(line[2:])
            elif line == "#":
                lines.append("")
            elif line.startswith("#"):
                lines.append(line[1:])
            else:
                raise ValueError(f"Ungültige Metadatenzeile in {path.name}")
        parsed = tomllib.loads("\n".join(lines))
        library = parsed.get("tool", {}).get("ref43_library")
        if not isinstance(library, dict):
            library = parsed.get("ref43_library")
        if not isinstance(library, dict):
            raise ValueError(f"Bibliotheksmetadaten fehlen: {path.name}")
        library = dict(library)
        if "requires_runtime" not in library:
            runtime = parsed.get("requires-python") or parsed.get("requires-r")
            if runtime:
                library["requires_runtime"] = str(runtime)
        if "dependencies" not in library and isinstance(parsed.get("dependencies"), list):
            library["dependencies"] = parsed["dependencies"]
        return library

    def _build_item(
        self,
        metadata: dict[str, Any],
        *,
        source_path: Path,
        item_type: str,
        default_language: str,
        readme_path: Path | None = None,
        file_count: int = 1,
    ) -> ScriptLibraryItem:
        required = (
            "id",
            "title",
            "short_description",
            "long_description",
            "category",
            "tags",
            "author",
            "version",
            "updated",
        )
        missing = [field for field in required if not metadata.get(field)]
        if missing:
            raise ValueError(
                f"Pflichtfelder fehlen in {source_path.name}: {', '.join(missing)}"
            )

        item_id = str(metadata["id"]).strip()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item_id):
            raise ValueError(f"Ungültige Script-ID: {item_id}")

        updated = date.fromisoformat(str(metadata["updated"]))
        tags = self._normalise_list(metadata["tags"], lower=True)
        language = str(metadata.get("language") or default_language).strip()
        if language not in {"Python", "R", "Jupyter"}:
            raise ValueError(f"Nicht unterstützte Sprache: {language}")

        entry_point = metadata.get("entry_point")
        if item_type == "script_package":
            if not entry_point:
                raise ValueError(f"Einstiegspunkt fehlt: {source_path.name}")
            entry_path = (source_path / str(entry_point)).resolve()
            if not entry_path.is_relative_to(source_path.resolve()) or not entry_path.exists():
                raise ValueError(f"Einstiegspunkt ist nicht vorhanden: {entry_point}")

        extension = source_path.suffix if source_path.is_file() else ".zip"
        download_filename = str(
            metadata.get("download_filename")
            or f"{item_id}-{metadata['version']}{extension}"
        )

        return ScriptLibraryItem(
            item_id=item_id,
            title=str(metadata["title"]).strip(),
            short_description=str(metadata["short_description"]).strip(),
            long_description=str(metadata["long_description"]).strip(),
            category=str(metadata["category"]).strip(),
            tags=tags,
            language=language,
            item_type=item_type,
            author=str(metadata["author"]).strip(),
            version=str(metadata["version"]).strip(),
            updated=updated,
            source_path=source_path.resolve(),
            download_filename=download_filename,
            entry_point=str(entry_point) if entry_point else None,
            requires_runtime=(
                str(metadata["requires_runtime"]).strip()
                if metadata.get("requires_runtime")
                else None
            ),
            dependencies=self._normalise_list(metadata.get("dependencies", [])),
            input_formats=self._normalise_list(metadata.get("input_formats", [])),
            output_formats=self._normalise_list(metadata.get("output_formats", [])),
            readme_path=readme_path.resolve() if readme_path else None,
            file_count=file_count,
        )

    @staticmethod
    def _normalise_list(value: Any, *, lower: bool = False) -> tuple[str, ...]:
        if not isinstance(value, list):
            raise ValueError("Metadatenliste erwartet")
        result: list[str] = []
        for entry in value:
            text = str(entry).strip()
            if not text:
                continue
            if lower:
                text = text.casefold().replace(" ", "-")
            if text not in result:
                result.append(text)
        return tuple(result)

    @classmethod
    def _iter_download_files(cls, directory: Path):
        for path in directory.rglob("*"):
            relative = path.relative_to(directory)
            if any(part in _IGNORED_PARTS for part in relative.parts):
                continue
            if path.suffix.lower() in _IGNORED_SUFFIXES:
                continue
            if path.name in {".env", "credentials.json"}:
                continue
            yield path

    def download_files(self, item: ScriptLibraryItem):
        """Yield files that belong to a package download."""

        if item.item_type != "script_package":
            raise ValueError("Dateiliste ist nur für Werkzeug-Pakete verfügbar")
        yield from self._iter_download_files(item.source_path)
