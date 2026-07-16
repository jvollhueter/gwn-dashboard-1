"""Smoke tests for the landing page and viewer modules."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_FILE = PROJECT_ROOT / "app.py"


@pytest.mark.smoke
def test_landing_page_starts_without_exception() -> None:
    """Verify landing page starts without exception."""
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
    assert 'Plattform für Datenaufbereitung und  &#8209;visualisierung' in landing_source
    assert '"groundwater-data"' in landing_source
    assert '"meteorological-data"' in landing_source
    assert '"script-library"' in landing_source


@pytest.mark.smoke
@pytest.mark.parametrize(
    "route",
    [
        "groundwater-data",
        "groundwater-quantity",
        "groundwater-quality",
        "meteorological-data",
        "script-library",
    ],
)
def test_platform_subject_pages_start_without_exception(route: str) -> None:
    """Verify platform subject pages start without exception."""
    app = AppTest.from_file(APP_FILE, default_timeout=30)
    app.query_params["view"] = route
    app.run()

    assert not app.exception
    assert not app.error


@pytest.mark.smoke
@pytest.mark.parametrize(
    "route",
    ["maps", "diagrams", "nomograms", "export", "information"],
)
def test_viewer_module_starts_without_exception(route: str) -> None:
    """Verify viewer module starts without exception."""
    app = AppTest.from_file(APP_FILE, default_timeout=60)
    app.query_params["view"] = route
    app.run()

    assert not app.exception
    assert not app.error


@pytest.mark.smoke
def test_core_functionality_is_available_in_viewer_routes() -> None:
    """Verify core functionality is available in viewer routes."""
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
    # One configurable package plus four direct downloads.
    assert len(export.get("download_button")) == 5


@pytest.mark.smoke
def test_period_sliders_update_comparison_metrics() -> None:
    """Verify period sliders update comparison metrics."""
    app = AppTest.from_file(APP_FILE, default_timeout=60)
    app.query_params["view"] = "diagrams"
    app.run()

    assert len(app.slider) == 2
    assert app.slider[0].label == "Referenzzeitraum"
    assert app.slider[1].label == "Vergleichszeitraum"
    original_metrics = [(metric.label, metric.value) for metric in app.metric]

    app.slider[0].set_value((1961, 1970))
    app.slider[1].set_value((2011, 2020))
    app.run()

    updated_metrics = [(metric.label, metric.value) for metric in app.metric]
    assert not app.exception
    assert updated_metrics != original_metrics
    assert updated_metrics[0][0] == "1961–1970"
    assert updated_metrics[1][0] == "2011–2020"

@pytest.mark.smoke
def test_map_station_modes_are_available_and_load_all_stations() -> None:
    """Verify map station modes are available and load all stations."""
    app = AppTest.from_file(APP_FILE, default_timeout=60)
    app.query_params["view"] = "maps"
    app.run()

    station_control = next(
        radio for radio in app.radio if radio.label == "Messstellen anzeigen"
    )
    assert station_control.options == [
        "Keine",
        "Alle",
        "Einzelne Auswahl",
        "Messstellen eines GWK",
    ]
    assert station_control.value == "Keine"

    station_control.set_value("Alle")
    app.run()

    assert not app.exception
    assert not app.error
    assert any(
        "3.131 Messstellen werden angezeigt" in caption.value
        for caption in app.caption
    )


@pytest.mark.smoke
def test_map_allows_searchable_individual_station_selection() -> None:
    """Verify map allows searchable individual station selection."""
    app = AppTest.from_file(APP_FILE, default_timeout=60)
    app.query_params["view"] = "maps"
    app.run()

    station_control = next(
        radio for radio in app.radio if radio.label == "Messstellen anzeigen"
    )
    station_control.set_value("Einzelne Auswahl")
    app.run()

    station_select = next(
        multiselect
        for multiselect in app.multiselect
        if multiselect.label == "Messstellen auswählen"
    )
    assert len(station_select.options) == 3131

    station_select.set_value([station_select.options[0]])
    app.run()

    assert not app.exception
    assert any(
        "1 Messstelle wird angezeigt" in caption.value
        for caption in app.caption
    )



@pytest.mark.smoke
def test_map_filters_monitoring_stations_by_selected_gwk() -> None:
    """Verify map filters monitoring stations by selected gwk."""
    app = AppTest.from_file(APP_FILE, default_timeout=60)
    app.query_params["view"] = "maps"
    app.run()

    detail_gwk = next(
        selectbox for selectbox in app.selectbox if selectbox.label == "Detail-GWK"
    ).value
    station_control = next(
        radio for radio in app.radio if radio.label == "Messstellen anzeigen"
    )
    station_control.set_value("Messstellen eines GWK")
    app.run()

    station_gwk = next(
        selectbox for selectbox in app.selectbox if selectbox.label == "GWK auswählen"
    )
    assert station_gwk.value == detail_gwk
    assert len(station_gwk.options) == 84

    station_gwk.set_value("DESN_EL-2-2-1")
    app.run()

    assert not app.exception
    assert not app.error
    assert any(
        "Messstelle" in caption.value and "angezeigt" in caption.value
        for caption in app.caption
    )

@pytest.mark.smoke
def test_export_period_sliders_update_shared_export_periods() -> None:
    """Verify export period sliders update shared export periods."""
    app = AppTest.from_file(APP_FILE, default_timeout=60)
    app.query_params["view"] = "export"
    app.run()

    assert not app.exception
    assert [slider.label for slider in app.slider] == [
        "Referenzzeitraum",
        "Vergleichszeitraum",
    ]

    app.slider[0].set_value((1961, 1970))
    app.slider[1].set_value((2011, 2020))
    app.run()

    assert not app.exception
    assert not app.error
    assert app.slider[0].value == (1961, 1970)
    assert app.slider[1].value == (2011, 2020)
    assert app.session_state.filtered_state["viewer_reference_period"] == (
        1961,
        1970,
    )
    assert app.session_state.filtered_state["viewer_comparison_period"] == (
        2011,
        2020,
    )
    assert any("1961–1970 (10 Jahre)" in caption.value for caption in app.caption)
    assert any("2011–2020 (10 Jahre)" in caption.value for caption in app.caption)


@pytest.mark.smoke
def test_script_library_exposes_search_filters_and_six_downloads() -> None:
    """Verify script library exposes search filters and six downloads."""
    app = AppTest.from_file(APP_FILE, default_timeout=30)
    app.query_params["view"] = "script-library"
    app.run()

    assert not app.exception
    assert not app.error
    assert [field.label for field in app.text_input] == ["Suche"]
    assert [field.label for field in app.selectbox] == [
        "Kategorie",
        "Sprache",
        "Bereitstellung",
    ]
    assert [field.label for field in app.multiselect] == ["Tags"]
    assert len(app.get("download_button")) == 6


@pytest.mark.smoke
def test_script_library_filters_by_language_and_opens_detail_page() -> None:
    """Verify script library filters by language and opens detail page."""
    catalogue = AppTest.from_file(APP_FILE, default_timeout=30)
    catalogue.query_params["view"] = "script-library"
    catalogue.run()

    language = next(field for field in catalogue.selectbox if field.label == "Sprache")
    language.set_value("Jupyter")
    catalogue.run()
    assert len(catalogue.get("download_button")) == 1

    detail = AppTest.from_file(APP_FILE, default_timeout=30)
    detail.query_params["view"] = "script-library"
    detail.query_params["script"] = "messstellen-gwk-zuordnung"
    detail.run()

    assert not detail.exception
    assert not detail.error
    assert len(detail.get("download_button")) == 1
    assert any("### Beschreibung" in element.value for element in detail.markdown)
    assert any("### Anwendung" in element.value for element in detail.markdown)
