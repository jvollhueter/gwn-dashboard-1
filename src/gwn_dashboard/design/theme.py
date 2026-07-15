"""Central design tokens derived from the supplied GWN Viewer references.

The palette and layout roles reproduce the visual language of the supplied
screenshots: dark-green navigation, light-gray application background, white
work surfaces, restrained gray borders, blue primary data series and a
salmon-red secondary series. The implementation adapts the existing dashboard
content and does not copy GWN Viewer functionality.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorPalette:
    """Semantic color roles shared by the interface and visualizations."""

    # Brand and navigation
    brand_primary: str
    brand_primary_dark: str
    brand_primary_light: str
    text_on_brand: str

    # Neutral interface colors
    background: str
    surface: str
    surface_muted: str
    border: str
    divider: str
    grid: str
    text: str
    text_strong: str
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
    # Exact dominant green sampled from the supplied GWN Viewer screenshots.
    brand_primary="#337E33",
    brand_primary_dark="#28652A",
    brand_primary_light="#E8F3E8",
    text_on_brand="#FFFFFF",
    # Neutral interface colors visible in the viewer.
    background="#F0F0F0",
    surface="#FFFFFF",
    surface_muted="#F9F9F9",
    border="#CED4DA",
    divider="#E6E6E6",
    grid="#E6E6E6",
    text="#56626E",
    text_strong="#3C3C3C",
    text_muted="#8B8B8B",
    # Exact dominant chart colors sampled from the diagram screenshot.
    groundwater="#007BFF",
    precipitation="#F45B5B",
    evapotranspiration="#F45B5B",
    # Period and semantic colors.
    reference_period="#8B8B8B",
    comparison_period="#337E33",
    increase="#337E33",
    decrease="#F45B5B",
    neutral="#8B8B8B",
    warning="#B26A00",
    error="#C62828",
)


GROUNDWATER_SCALE = [
    [0.00, "#ff1a0a"],
    [0.13, "#ff6a00"],
    [0.27, "#ffae00"],
    [0.42, "#fff200"],
    [0.56, "#42e51b"],
    [0.70, "#16a01d"],
    [0.82, "#45c7e8"],
    [0.91, "#174dff"],
    [1.00, "#7c08eb"],
]

CHANGE_SCALE = [
    [0.00, COLORS.decrease],
    [0.50, COLORS.surface],
    [1.00, COLORS.increase],
]
