"""Shared Plotly layout helpers."""

from __future__ import annotations

import plotly.graph_objects as go

from gwn_dashboard.design.theme import COLORS


def apply_dashboard_layout(
    figure: go.Figure,
    *,
    title: str | None = None,
    height: int | None = None,
    hovermode: str | None = None,
) -> go.Figure:
    """Apply the common dashboard style to a Cartesian Plotly figure."""

    layout: dict[str, object] = {
        "template": "plotly_white",
        "paper_bgcolor": COLORS.surface,
        "plot_bgcolor": COLORS.surface,
        "font": {
            "color": COLORS.text,
            "family": "Arial, sans-serif",
            "size": 13,
        },
        "title_font": {
            "color": COLORS.text,
            "size": 18,
        },
        "legend": {
            "title": None,
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        "margin": {
            "l": 60,
            "r": 30,
            "t": 90,
            "b": 60,
        },
        "hoverlabel": {
            "bgcolor": COLORS.surface,
            "font_color": COLORS.text,
            "bordercolor": COLORS.border,
        },
    }
    if title is not None:
        layout["title"] = title
    if height is not None:
        layout["height"] = height
    if hovermode is not None:
        layout["hovermode"] = hovermode

    figure.update_layout(**layout)
    figure.update_xaxes(
        gridcolor=COLORS.grid,
        linecolor=COLORS.border,
        zerolinecolor=COLORS.border,
    )
    figure.update_yaxes(
        gridcolor=COLORS.grid,
        linecolor=COLORS.border,
        zerolinecolor=COLORS.border,
    )
    return figure


def apply_map_layout(
    figure: go.Figure,
    *,
    title: str,
    height: int = 650,
) -> go.Figure:
    """Apply the common dashboard style to a map figure."""

    figure.update_layout(
        title=title,
        height=height,
        paper_bgcolor=COLORS.surface,
        font={
            "color": COLORS.text,
            "family": "Arial, sans-serif",
            "size": 13,
        },
        title_font={
            "color": COLORS.text,
            "size": 18,
        },
        hoverlabel={
            "bgcolor": COLORS.surface,
            "font_color": COLORS.text,
            "bordercolor": COLORS.border,
        },
        margin={"r": 0, "t": 60, "l": 0, "b": 0},
    )
    return figure
