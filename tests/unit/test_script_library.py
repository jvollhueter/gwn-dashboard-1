"""Tests for script-library discovery, search and downloads."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from gwn_dashboard.repositories.script_library_repository import ScriptLibraryRepository
from gwn_dashboard.services.script_library_service import ScriptLibraryService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LIBRARY_ROOT = PROJECT_ROOT / "script_library"


def _service() -> ScriptLibraryService:
    return ScriptLibraryService(ScriptLibraryRepository(LIBRARY_ROOT))


def test_catalogue_contains_all_supported_publication_forms() -> None:
    """Verify catalogue contains all supported publication forms."""
    catalogue = _service().load_catalogue()

    assert len(catalogue) == 6
    assert {item.language for item in catalogue} == {"Python", "R", "Jupyter"}
    assert {item.item_type for item in catalogue} == {
        "single_script",
        "notebook",
        "script_package",
    }
    assert len({item.item_id for item in catalogue}) == len(catalogue)


def test_full_text_search_and_metadata_filters_are_combined() -> None:
    """Verify full text search and metadata filters are combined."""
    service = _service()
    catalogue = service.load_catalogue()

    result = service.filter_items(
        catalogue,
        query="messstellen geodaten",
        category="Grundwasserquantität",
        language="Python",
        item_type="Werkzeug-Paket",
        tags=("gwk",),
    )

    assert [item.item_id for item in result] == ["messstellen-gwk-zuordnung"]


def test_search_is_case_and_diacritic_insensitive() -> None:
    """Verify search is case and diacritic insensitive."""
    service = _service()
    result = service.filter_items(service.load_catalogue(), query="DATENPRUFUNG")

    assert "csv-datenpruefung" in {item.item_id for item in result}


def test_single_file_download_preserves_the_source_file() -> None:
    """Verify single file download preserves the source file."""
    service = _service()
    item = service.find_by_id(service.load_catalogue(), "niederschlag-aggregieren")

    assert item is not None
    data, filename, mime_type = service.build_download(item)

    assert data == item.source_path.read_bytes()
    assert filename.endswith(".py")
    assert mime_type == "text/x-python"


def test_package_download_contains_project_files_and_excludes_cache_files() -> None:
    """Verify package download contains project files and excludes cache files."""
    service = _service()
    item = service.find_by_id(service.load_catalogue(), "messstellen-gwk-zuordnung")

    assert item is not None
    data, filename, mime_type = service.build_download(item)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = set(archive.namelist())

    assert filename.endswith(".zip")
    assert mime_type == "application/zip"
    assert "messstellen_gwk_zuordnung/main.py" in names
    assert "messstellen_gwk_zuordnung/metadata.toml" in names
    assert "messstellen_gwk_zuordnung/examples/messstellen.csv" in names
    assert not any("__pycache__" in name or name.endswith(".pyc") for name in names)
