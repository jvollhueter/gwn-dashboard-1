"""Unit tests for the shared dashboard design system."""

from dataclasses import fields
from pathlib import Path
import re

import pandas as pd
import plotly.graph_objects as go

from gwn_dashboard.config import (
    ApplicationSettings,
    DashboardConfig,
    DataPaths,
)
from gwn_dashboard.design.plotly_theme import apply_dashboard_layout
from gwn_dashboard.design.theme import COLORS
from gwn_dashboard.domain.models import DashboardData, Parameter, Period
from gwn_dashboard.visualization.chart_factory import ChartFactory


HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _test_config() -> DashboardConfig:
    return DashboardConfig(
        application=ApplicationSettings(
            title="Test",
            page_title="Test",
            page_icon="💧",
            layout="wide",
            initial_sidebar_state="expanded",
        ),
        data=DataPaths(
            base_directory=Path("data"),
            mapping_file=Path("mapping.csv"),
            geometry_file=Path("geometry.shp"),
            station_overview_file=Path("stations.csv"),
            station_mapping_file=Path("station_mapping.csv"),
        ),
        reference_period=Period("2000–2001", 2000, 2001),
        comparison_period=Period("2002–2003", 2002, 2003),
        groundwater_recharge=Parameter(
            code="gwn",
            label="Grundwasserneubildung",
            unit="mm/a",
            source_codes=("rg1", "rg2"),
        ),
        precipitation=Parameter(
            code="P",
            label="Niederschlag",
            unit="mm/a",
        ),
        potential_evapotranspiration=Parameter(
            code="ETp",
            label="Potenzielle Evapotranspiration",
            unit="mm/a",
        ),
    )


def _test_dashboard_data() -> DashboardData:
    recharge = pd.DataFrame(
        {
            "GWK_ID": ["GWK_A"] * 4,
            "year": [2000, 2001, 2002, 2003],
            "gwn_mm_a": [100.0, 110.0, 90.0, 95.0],
        }
    )
    precipitation = pd.DataFrame(
        {
            "GWK_ID": ["GWK_A"] * 4,
            "year": [2000, 2001, 2002, 2003],
            "value": [500.0, 510.0, 490.0, 505.0],
        }
    )
    evapotranspiration = pd.DataFrame(
        {
            "GWK_ID": ["GWK_A"] * 4,
            "year": [2000, 2001, 2002, 2003],
            "value": [400.0, 405.0, 410.0, 415.0],
        }
    )
    return DashboardData(
        groundwater_recharge=recharge,
        precipitation=precipitation,
        evapotranspiration=evapotranspiration,
        comparison=pd.DataFrame(),
        trends=pd.DataFrame(),
    )


def test_all_theme_colors_are_valid_hex_values() -> None:
    """Verify all theme colors are valid hex values."""
    for color_field in fields(COLORS):
        value = getattr(COLORS, color_field.name)
        assert HEX_COLOR.fullmatch(value), f"Invalid color for {color_field.name}: {value}"


def test_required_semantic_color_roles_are_defined() -> None:
    """Verify required semantic color roles are defined."""
    required_roles = {
        "brand_primary",
        "background",
        "surface",
        "text",
        "groundwater",
        "precipitation",
        "evapotranspiration",
        "increase",
        "decrease",
    }
    available_roles = {color_field.name for color_field in fields(COLORS)}

    assert required_roles <= available_roles


def test_plotly_theme_applies_shared_surface_and_text_colors() -> None:
    """Verify plotly theme applies shared surface and text colors."""
    figure = apply_dashboard_layout(go.Figure(), title="Test", height=300)

    assert figure.layout.paper_bgcolor == COLORS.surface
    assert figure.layout.plot_bgcolor == COLORS.surface
    assert figure.layout.font.color == COLORS.text
    assert figure.layout.height == 300


def test_timeseries_uses_groundwater_theme_color() -> None:
    """Verify timeseries uses groundwater theme color."""
    figure = ChartFactory(_test_config()).create_timeseries(
        _test_dashboard_data(),
        groundwater_body="GWK_A",
        show_precipitation=False,
        show_evapotranspiration=False,
    )

    groundwater_trace = figure.data[0]
    assert groundwater_trace.line.color == COLORS.groundwater
    assert groundwater_trace.marker.color == COLORS.groundwater


def test_timeseries_uses_distinct_etp_theme_color() -> None:
    """Verify timeseries uses distinct etp theme color."""
    figure = ChartFactory(_test_config()).create_timeseries(
        _test_dashboard_data(),
        groundwater_body="GWK_A",
        show_precipitation=True,
        show_evapotranspiration=True,
    )

    traces = {trace.name: trace for trace in figure.data}
    etp_trace = traces["Potenzielle Evapotranspiration"]
    precipitation_trace = traces["Niederschlag"]
    groundwater_trace = traces["Grundwasserneubildung"]

    assert etp_trace.line.color == COLORS.evapotranspiration
    assert etp_trace.marker.color == COLORS.evapotranspiration
    assert etp_trace.line.color != precipitation_trace.line.color
    assert etp_trace.line.color != groundwater_trace.line.color


def test_streamlit_theme_stays_synchronized_with_python_palette() -> None:
    """Verify streamlit theme stays synchronized with python palette."""
    import tomllib

    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / ".streamlit" / "config.toml"
    with config_path.open("rb") as stream:
        streamlit_config = tomllib.load(stream)

    theme = streamlit_config["theme"]
    assert theme["primaryColor"] == COLORS.brand_primary
    assert theme["backgroundColor"] == COLORS.background
    assert theme["textColor"] == COLORS.text


def test_core_palette_matches_supplied_gwn_viewer_reference() -> None:
    """Verify core palette matches supplied gwn viewer reference."""
    assert COLORS.brand_primary == "#337E33"
    assert COLORS.background == "#F0F0F0"
    assert COLORS.surface == "#FFFFFF"
    assert COLORS.border == "#CED4DA"
    assert COLORS.groundwater == "#007BFF"
    assert COLORS.precipitation == "#F45B5B"
    assert COLORS.evapotranspiration == "#7B2CBF"
    assert COLORS.evapotranspiration != COLORS.groundwater
    assert COLORS.evapotranspiration != COLORS.precipitation


def test_viewer_layout_css_contains_landing_header_and_footer_navigation() -> None:
    """Verify viewer layout css contains landing header and footer navigation."""
    project_root = Path(__file__).resolve().parents[2]
    styles = (
        project_root / "src" / "gwn_dashboard" / "design" / "styles.css"
    ).read_text(encoding="utf-8")

    assert ".viewer-header" in styles
    assert ".viewer-landing" in styles
    assert ".viewer-landing-card" in styles
    assert ".viewer-bottom-nav" in styles
    assert "position: fixed" in styles
    assert "background: var(--viewer-green)" in styles


def test_application_routes_landing_and_all_viewer_modules() -> None:
    """Verify application routes landing and all viewer modules."""
    project_root = Path(__file__).resolve().parents[2]
    application = (
        project_root / "src" / "gwn_dashboard" / "ui" / "application.py"
    ).read_text(encoding="utf-8")

    landing_position = application.index("if route == START.key")
    context_position = application.index("self._context = _create_cached_context")

    assert landing_position < context_position
    assert "LandingPage(" in application
    assert "MapPage(" in application
    assert "DiagramPage(" in application
    assert "NomogramPage(" in application
    assert "ExportPage(" in application
    assert "InformationPage().render()" in application


def test_landing_background_asset_is_included() -> None:
    """Verify landing background asset is included."""
    project_root = Path(__file__).resolve().parents[2]
    background = (
        project_root
        / "src"
        / "gwn_dashboard"
        / "ui"
        / "assets"
        / "landing_background.jpg"
    )

    assert background.exists()
    assert background.stat().st_size > 10_000



def test_header_contains_only_home_service_link_and_internal_platform_title() -> None:
    """Verify header contains only home service link and internal platform title."""
    project_root = Path(__file__).resolve().parents[2]
    header = (
        project_root
        / "src"
        / "gwn_dashboard"
        / "ui"
        / "components"
        / "app_header.py"
    ).read_text(encoding="utf-8")

    assert "Interne Plattform Referat 43" in header
    assert "viewer-brand-mark" not in header
    assert 'Plattform für Datenaufbereitung und  &#8209;visualisierung' in header
    assert 'title = "GWN Viewer"' in header
    assert 'brand_route = GROUNDWATER_QUANTITY.key' in header
    assert 'href="?view={START.key}"' in header
    assert "Kontakt" not in header
    assert "Impressum" not in header
    assert "Datenschutzerklärung" not in header
    assert "Sitzung beenden" not in header


def test_decorative_pseudo_menus_are_not_present() -> None:
    """Verify decorative pseudo menus are not present."""
    project_root = Path(__file__).resolve().parents[2]
    ui_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (project_root / "src" / "gwn_dashboard" / "ui").rglob("*.py")
    )
    styles = (
        project_root / "src" / "gwn_dashboard" / "design" / "styles.css"
    ).read_text(encoding="utf-8")

    assert "viewer-map-toolbar" not in ui_source
    assert "viewer-toolbar-arrow" not in ui_source
    assert "viewer-module-selector" not in ui_source
    assert "viewer-brand-mark" not in styles


def test_timeseries_preserves_both_optional_meteorological_series() -> None:
    """Verify timeseries preserves both optional meteorological series."""
    figure = ChartFactory(_test_config()).create_timeseries(
        _test_dashboard_data(),
        groundwater_body="GWK_A",
        show_precipitation=True,
        show_evapotranspiration=True,
    )
    names = {trace.name for trace in figure.data}

    assert "Grundwasserneubildung" in names
    assert "Niederschlag" in names
    assert "Potenzielle Evapotranspiration" in names
    assert any("2000–2001" in name for name in names)
    assert any("2002–2003" in name for name in names)


def test_map_page_preserves_period_boxplot_and_uses_real_plotly_toolbar() -> None:
    """Verify map page preserves period boxplot and uses real plotly toolbar."""
    project_root = Path(__file__).resolve().parents[2]
    map_page = (
        project_root
        / "src"
        / "gwn_dashboard"
        / "ui"
        / "pages"
        / "map_page.py"
    ).read_text(encoding="utf-8")

    assert "create_period_boxplot" in map_page
    assert '"displayModeBar": True' in map_page
    assert "viewer-map-toolbar" not in map_page


def test_landing_page_icon_assets_are_included() -> None:
    """Verify landing page icon assets are included."""
    project_root = Path(__file__).resolve().parents[2]
    icon_directory = (
        project_root
        / "src"
        / "gwn_dashboard"
        / "ui"
        / "assets"
        / "icons"
    )

    expected_icons = {
        "karte.png",
        "liniendiagramm.png",
        "korrelation.png",
        "import-export.png",
        "grundwasser.png",
        "wetter.png",
        "bibliothek.png",
        "messbecher.png",
        "labor-ausstattung.png",
    }

    assert {path.name for path in icon_directory.glob("*.png")} == expected_icons
    for icon_path in icon_directory.glob("*.png"):
        assert icon_path.stat().st_size > 1_000


def test_timeseries_uses_individually_selected_period_labels() -> None:
    """Verify timeseries uses individually selected period labels."""
    reference = Period("2000", 2000, 2000)
    comparison = Period("2003", 2003, 2003)

    figure = ChartFactory(_test_config()).create_timeseries(
        _test_dashboard_data(),
        groundwater_body="GWK_A",
        show_precipitation=False,
        show_evapotranspiration=False,
        reference_period=reference,
        comparison_period=comparison,
    )
    names = {trace.name for trace in figure.data}

    assert any("GWN Ø 2000" in name for name in names)
    assert any("GWN Ø 2003" in name for name in names)
