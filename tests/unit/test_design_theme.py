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
    for color_field in fields(COLORS):
        value = getattr(COLORS, color_field.name)
        assert HEX_COLOR.fullmatch(value), f"Invalid color for {color_field.name}: {value}"


def test_required_semantic_color_roles_are_defined() -> None:
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
    figure = apply_dashboard_layout(go.Figure(), title="Test", height=300)

    assert figure.layout.paper_bgcolor == COLORS.surface
    assert figure.layout.plot_bgcolor == COLORS.surface
    assert figure.layout.font.color == COLORS.text
    assert figure.layout.height == 300


def test_timeseries_uses_groundwater_theme_color() -> None:
    figure = ChartFactory(_test_config()).create_timeseries(
        _test_dashboard_data(),
        groundwater_body="GWK_A",
        show_precipitation=False,
        show_evapotranspiration=False,
    )

    groundwater_trace = figure.data[0]
    assert groundwater_trace.line.color == COLORS.groundwater
    assert groundwater_trace.marker.color == COLORS.groundwater


def test_streamlit_theme_stays_synchronized_with_python_palette() -> None:
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
    assert COLORS.brand_primary == "#337E33"
    assert COLORS.background == "#F0F0F0"
    assert COLORS.surface == "#FFFFFF"
    assert COLORS.border == "#CED4DA"
    assert COLORS.groundwater == "#007BFF"
    assert COLORS.evapotranspiration == "#F45B5B"
