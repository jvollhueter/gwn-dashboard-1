"""Focused tests for viewer HTML output and functional UI filters."""

from pathlib import Path

import pandas as pd

from gwn_dashboard.domain.models import DashboardData, SidebarSelection
from gwn_dashboard.ui.pages.export_page import ExportPage
from gwn_dashboard.ui.pages.landing_page import LandingPage


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
    data = _dashboard_data()
    selection = SidebarSelection(
        groundwater_body_ids=("A", "B"),
        selected_groundwater_body="B",
        show_precipitation=True,
        show_evapotranspiration=False,
    )
    page = ExportPage(context=None, data=data, selection=selection)  # type: ignore[arg-type]

    filtered = page._filtered_data(detail_only=True)

    for frame in (
        filtered.groundwater_recharge,
        filtered.precipitation,
        filtered.evapotranspiration,
        filtered.comparison,
        filtered.trends,
    ):
        assert frame["GWK_ID"].tolist() == ["B"]
