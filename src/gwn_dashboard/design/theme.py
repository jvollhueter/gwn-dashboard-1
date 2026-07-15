"""Central design tokens for the dashboard.

The interface palette is derived from the supplied GWN Sachsen viewer
screenshot. It reproduces the viewer's color scheme only; it does not copy the
viewer layout and it is not presented as an official LfULG corporate-design
specification.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorPalette:
    """Semantic color roles shared by the user interface and visualizations."""

    # Brand and navigation
    brand_primary: str
    brand_primary_dark: str
    brand_primary_light: str
    text_on_brand: str

    # Neutral interface colors
    background: str
    surface: str
    border: str
    grid: str
    text: str
    text_muted: str

    # Scientific data colors
    groundwater: str
    precipitation: str
    evapotranspiration: str

    # Period comparison
    reference_period: str
    comparison_period: str

    # Semantic result colors
    increase: str
    decrease: str
    neutral: str
    warning: str
    error: str


COLORS = ColorPalette(
    # Core colors sampled from the supplied GWN viewer screenshot.
    brand_primary="#337E33",
    # Darker companion tone for hover, borders and selected outlines.
    brand_primary_dark="#28652A",
    brand_primary_light="#E8F3E8",
    text_on_brand="#FFFFFF",
    background="#F0F0F0",
    surface="#FFFFFF",
    border="#CED4DA",
    grid="#E6E6E6",
    text="#3C3C3C",
    text_muted="#6C757D",
    groundwater="#007BFF",
    # Darker blue companion for an optional second water-related series.
    precipitation="#005BBB",
    evapotranspiration="#F45B5B",
    reference_period="#6C757D",
    comparison_period="#337E33",
    increase="#337E33",
    decrease="#F45B5B",
    neutral="#6C757D",
    warning="#B26A00",
    error="#C62828",
)


GROUNDWATER_SCALE = [
    [0.00, "#EAF4FF"],
    [0.25, "#B9DCFF"],
    [0.50, "#75B8FF"],
    [0.75, "#2C93FF"],
    [1.00, COLORS.groundwater],
]

CHANGE_SCALE = [
    [0.00, COLORS.decrease],
    [0.50, COLORS.surface],
    [1.00, COLORS.increase],
]
