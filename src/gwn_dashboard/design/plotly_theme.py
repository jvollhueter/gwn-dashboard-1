"""Shared Plotly layout helpers for the viewer-inspired interface."""

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
    """Apply the common viewer-like style to a Cartesian Plotly figure."""

    layout: dict[str, object] = {
        "template": "plotly_white",
        "paper_bgcolor": COLORS.surface,
        "plot_bgcolor": COLORS.surface,
        "font": {
            "color": COLORS.text,
            "family": "Arial, sans-serif",
            "size": 12,
        },
        "title": {
            "font": {"color": COLORS.text_strong, "size": 16},
            "x": 0.5,
            "xanchor": "center",
        },
        "legend": {
            "title": None,
            "orientation": "h",
            "yanchor": "top",
            "y": -0.16,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 11},
        },
        "margin": {
            "l": 65,
            "r": 25,
            "t": 65,
            "b": 90,
        },
        "hoverlabel": {
            "bgcolor": COLORS.surface,
            "font_color": COLORS.text,
            "bordercolor": COLORS.border,
        },
    }
    if title is not None:
        layout["title"] = {
            "text": title,
            "font": {"color": COLORS.text_strong, "size": 16},
            "x": 0.5,
            "xanchor": "center",
        }
    if height is not None:
        layout["height"] = height
    if hovermode is not None:
        layout["hovermode"] = hovermode

    figure.update_layout(**layout)
    figure.update_xaxes(
        showline=True,
        linewidth=1,
        gridcolor=COLORS.grid,
        linecolor=COLORS.text_muted,
        zerolinecolor=COLORS.border,
        tickfont={"color": COLORS.text},
        title_font={"color": COLORS.text},
    )
    figure.update_yaxes(
        showline=True,
        linewidth=1,
        gridcolor=COLORS.grid,
        linecolor=COLORS.text_muted,
        zerolinecolor=COLORS.border,
        tickfont={"color": COLORS.text},
        title_font={"color": COLORS.text},
    )
    return figure


def apply_map_layout(
    figure: go.Figure,
    *,
    title: str,
    height: int = 650,
) -> go.Figure:
    """Apply the common viewer-like style to a map figure."""

    figure.update_layout(
        title={
            "text": title,
            "font": {"color": COLORS.text_strong, "size": 16},
            "x": 0.5,
            "xanchor": "center",
        },
        height=height,
        paper_bgcolor=COLORS.surface,
        font={
            "color": COLORS.text,
            "family": "Arial, sans-serif",
            "size": 12,
        },
        hoverlabel={
            "bgcolor": COLORS.surface,
            "font_color": COLORS.text,
            "bordercolor": COLORS.border,
        },
        margin={"r": 0, "t": 52, "l": 0, "b": 0},
    )
    return figure
