"""Smoke tests for the landing page and viewer modules."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_FILE = PROJECT_ROOT / "app.py"


@pytest.mark.smoke
def test_landing_page_starts_without_exception() -> None:
    app = AppTest.from_file(APP_FILE, default_timeout=30)
    app.run()

    assert not app.exception
    landing_source = (
        PROJECT_ROOT
        / "src"
        / "gwn_dashboard"
        / "ui"
        / "pages"
        / "landing_page.py"
    ).read_text(encoding="utf-8")
    assert 'st.html(' in landing_source
    assert '("maps", "Karten")' in landing_source
    assert '("diagrams", "Diagramme")' in landing_source
    assert '("nomograms", "Nomogramme")' in landing_source
    assert '("export", "Export")' in landing_source


@pytest.mark.smoke
@pytest.mark.parametrize(
    "route",
    ["maps", "diagrams", "nomograms", "export", "information"],
)
def test_viewer_module_starts_without_exception(route: str) -> None:
    app = AppTest.from_file(APP_FILE, default_timeout=60)
    app.query_params["view"] = route
    app.run()

    assert not app.exception
    assert not app.error


@pytest.mark.smoke
def test_previous_functionality_is_available_in_viewer_routes() -> None:
    diagrams = AppTest.from_file(APP_FILE, default_timeout=60)
    diagrams.query_params["view"] = "diagrams"
    diagrams.run()
    assert len(diagrams.metric) == 4
    assert len(diagrams.checkbox) >= 2
    assert len(diagrams.get("plotly_chart")) >= 1

    maps = AppTest.from_file(APP_FILE, default_timeout=60)
    maps.query_params["view"] = "maps"
    maps.run()
    assert len(maps.get("plotly_chart")) >= 3
    assert len(maps.radio) >= 1

    nomograms = AppTest.from_file(APP_FILE, default_timeout=60)
    nomograms.query_params["view"] = "nomograms"
    nomograms.run()
    assert len(nomograms.get("plotly_chart")) == 1

    export = AppTest.from_file(APP_FILE, default_timeout=60)
    export.query_params["view"] = "export"
    export.run()
    # One configurable package plus the four downloads from the previous UI.
    assert len(export.get("download_button")) == 5
