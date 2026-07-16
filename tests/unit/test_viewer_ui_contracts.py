"""Focused tests for viewer HTML output and functional UI filters."""

from pathlib import Path

import pandas as pd

from gwn_dashboard.domain.models import DashboardData, Period, SidebarSelection
from gwn_dashboard.ui.pages.export_page import ExportPage
from gwn_dashboard.ui.components.app_header import AppHeader
from gwn_dashboard.ui.pages.landing_page import (
    GroundwaterDataLandingPage,
    LandingPage,
    PlaceholderLandingPage,
    PlatformLandingPage,
)


def _dashboard_data() -> DashboardData:
    comparison = pd.DataFrame(
        {
            "GWK_ID": ["A", "B"],
            "mean_ref": [100.0, 200.0],
            "mean_hist": [90.0, 180.0],
            "delta_abs": [-10.0, -20.0],
            "delta_rel_pct": [-10.0, -10.0],
        }
    )
    trends = pd.DataFrame(
        {
            "GWK_ID": ["A", "B"],
            "lr_slope": [-1.0, -2.0],
        }
    )
    recharge = pd.DataFrame(
        {
            "GWK_ID": ["A", "B"],
            "year": [2000, 2000],
            "gwn_mm_a": [100.0, 200.0],
        }
    )
    precipitation = pd.DataFrame(
        {
            "GWK_ID": ["A", "B"],
            "year": [2000, 2000],
            "value": [500.0, 600.0],
        }
    )
    evapotranspiration = pd.DataFrame(
        {
            "GWK_ID": ["A", "B"],
            "year": [2000, 2000],
            "value": [400.0, 450.0],
        }
    )
    return DashboardData(
        groundwater_recharge=recharge,
        precipitation=precipitation,
        evapotranspiration=evapotranspiration,
        comparison=comparison,
        trends=trends,
    )


def test_landing_page_emits_four_complete_cards_without_escaped_source(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify landing page emits four complete cards without escaped source."""
    background = tmp_path / "background.jpg"
    background.write_bytes(b"test-image")
    icon_directory = tmp_path / "icons"
    icon_directory.mkdir()
    for filename in (
        "karte.png",
        "liniendiagramm.png",
        "korrelation.png",
        "import-export.png",
    ):
        (icon_directory / filename).write_bytes(b"test-icon")
    captured: list[str] = []

    monkeypatch.setattr(
        "gwn_dashboard.ui.pages.landing_page.st.html",
        captured.append,
    )

    LandingPage(background).render()

    assert len(captured) == 1
    html = captured[0]
    assert html.count('<a class="viewer-landing-card"') == 4
    assert html.count('</a>') == 5  # four cards plus the arrow link
    assert "&lt;a class=" not in html
    assert html.count('src="data:image/png;base64,') == 4
    assert "<svg" not in html


def test_export_detail_filter_applies_to_every_exported_table() -> None:
    """Verify export detail filter applies to every exported table."""
    data = _dashboard_data()
    selection = SidebarSelection(
        groundwater_body_ids=("A", "B"),
        selected_groundwater_body="B",
        reference_period=Period("1961–1990", 1961, 1990),
        comparison_period=Period("1991–2020", 1991, 2020),
        show_precipitation=True,
        show_evapotranspiration=False,
    )
    page = ExportPage(
        context=None,
        data=data,
        selection=selection,
        minimum_year=1961,
        maximum_year=2020,
    )  # type: ignore[arg-type]

    filtered = page._filtered_data(detail_only=True)

    for frame in (
        filtered.groundwater_recharge,
        filtered.precipitation,
        filtered.evapotranspiration,
        filtered.comparison,
        filtered.trends,
    ):
        assert frame["GWK_ID"].tolist() == ["B"]


def _landing_assets(tmp_path: Path) -> Path:
    background = tmp_path / "background.jpg"
    background.write_bytes(b"test-image")
    icon_directory = tmp_path / "icons"
    icon_directory.mkdir()
    for filename in (
        "grundwasser.png",
        "wetter.png",
        "bibliothek.png",
        "messbecher.png",
        "labor-ausstattung.png",
        "karte.png",
        "liniendiagramm.png",
        "korrelation.png",
        "import-export.png",
    ):
        (icon_directory / filename).write_bytes(b"test-icon")
    return background


def test_platform_landing_page_emits_three_linked_subject_cards(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify platform landing page emits three linked subject cards."""
    background = _landing_assets(tmp_path)
    captured: list[str] = []
    monkeypatch.setattr(
        "gwn_dashboard.ui.pages.landing_page.st.html",
        captured.append,
    )

    PlatformLandingPage(background).render()

    html = captured[0]
    assert html.count('<a class="viewer-landing-card"') == 3
    assert '?view=groundwater-data' in html
    assert '?view=meteorological-data' in html
    assert '?view=script-library' in html
    assert 'Plattform für Datenaufbereitung und  &#8209;visualisierung' in html
    assert html.count('src="data:image/png;base64,') == 3


def test_groundwater_data_landing_page_links_quantity_and_quality(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify groundwater data landing page links quantity and quality."""
    background = _landing_assets(tmp_path)
    captured: list[str] = []
    monkeypatch.setattr(
        "gwn_dashboard.ui.pages.landing_page.st.html",
        captured.append,
    )

    GroundwaterDataLandingPage(background).render()

    html = captured[0]
    assert html.count('<a class="viewer-landing-card"') == 2
    assert '?view=groundwater-quantity' in html
    assert '?view=groundwater-quality' in html
    assert 'Grundwasserquantität' in html
    assert 'Grundwasserqualität' in html


def test_placeholder_page_contains_status_message(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify placeholder page contains status message."""
    background = _landing_assets(tmp_path)
    captured: list[str] = []
    monkeypatch.setattr(
        "gwn_dashboard.ui.pages.landing_page.st.html",
        captured.append,
    )

    PlaceholderLandingPage(
        background,
        title="Meteorologische Daten",
        subtitle="Datenvisualisierung und Aufbereitung meteorologischer Daten",
        icon_filename="wetter.png",
    ).render()

    html = captured[0]
    assert 'Meteorologische Daten' in html
    assert 'Für diesen Bereich sind derzeit noch keine Inhalte hinterlegt.' in html
    assert html.count('src="data:image/png;base64,') == 1


def test_header_links_quantity_brand_to_quantity_landing_and_home_to_platform(
    monkeypatch,
) -> None:
    """Verify header links quantity brand to quantity landing and home to platform."""
    captured: list[str] = []
    monkeypatch.setattr(
        "gwn_dashboard.ui.components.app_header.st.html",
        captured.append,
    )

    AppHeader().render("maps")

    html = captured[0]
    assert 'GWN Viewer' in html
    assert '?view=groundwater-quantity' in html
    assert '?view=platform' in html
    assert html.count('>Home</a>') == 1


def test_platform_header_uses_platform_title_and_home_target(monkeypatch) -> None:
    """Verify platform header uses platform title and home target."""
    captured: list[str] = []
    monkeypatch.setattr(
        "gwn_dashboard.ui.components.app_header.st.html",
        captured.append,
    )

    AppHeader().render("groundwater-data")

    html = captured[0]
    assert 'Plattform für Datenaufbereitung und  &#8209;visualisierung' in html
    assert '?view=platform' in html
    assert 'GWN Viewer' not in html
