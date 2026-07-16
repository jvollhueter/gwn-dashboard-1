"""Plotly chart factory."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import linregress

from gwn_dashboard.config import DashboardConfig
from gwn_dashboard.design.plotly_theme import apply_dashboard_layout
from gwn_dashboard.design.theme import COLORS
from gwn_dashboard.domain.models import DashboardData, Period


class ChartFactory:
    """Create consistently styled Plotly figures.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    def __init__(self, config: DashboardConfig) -> None:
        self._config = config

    def create_timeseries(
        self,
        data: DashboardData,
        groundwater_body: str,
        show_precipitation: bool,
        show_evapotranspiration: bool,
        reference_period: Period | None = None,
        comparison_period: Period | None = None,
    ) -> go.Figure:
        """Create an annual groundwater-recharge time-series figure.
        
        Args:
            data: Value of type ``DashboardData``.
            groundwater_body: Value of type ``str``.
            show_precipitation: Value of type ``bool``.
            show_evapotranspiration: Value of type ``bool``.
            reference_period: Value of type ``Period | None``.
            comparison_period: Value of type ``Period | None``.
        
        Returns:
            go.Figure: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        reference, comparison = self._resolve_periods(
            reference_period,
            comparison_period,
        )
        recharge = data.groundwater_recharge.query(
            "GWK_ID == @groundwater_body"
        ).sort_values("year")
        precipitation = data.precipitation.query(
            "GWK_ID == @groundwater_body"
        ).sort_values("year")
        etp = data.evapotranspiration.query(
            "GWK_ID == @groundwater_body"
        ).sort_values("year")

        figure = make_subplots(specs=[[{"secondary_y": True}]])
        figure.add_trace(
            go.Scatter(
                x=recharge["year"],
                y=recharge["gwn_mm_a"],
                name="Grundwasserneubildung",
                mode="lines+markers",
                line={"color": COLORS.groundwater, "width": 1.6},
                marker={
                    "color": COLORS.groundwater,
                    "size": 6,
                    "symbol": "circle",
                },
            ),
            secondary_y=False,
        )

        period_styles = (
            (reference, COLORS.reference_period, "dash"),
            (comparison, COLORS.comparison_period, "dot"),
        )
        for period, color, dash in period_styles:
            mean_value = recharge.loc[
                recharge["year"].between(
                    period.start_year,
                    period.end_year,
                    inclusive="both",
                ),
                "gwn_mm_a",
            ].mean()
            figure.add_trace(
                go.Scatter(
                    x=[period.start_year, period.end_year],
                    y=[mean_value, mean_value],
                    name=f"GWN Ø {period.label} ({mean_value:.1f} mm/a)",
                    mode="lines",
                    line={"color": color, "dash": dash, "width": 2},
                ),
                secondary_y=False,
            )
            figure.add_vrect(
                x0=period.start_year,
                x1=period.end_year,
                fillcolor=color,
                opacity=0.07,
                line_width=0,
            )

        if show_precipitation:
            figure.add_trace(
                go.Scatter(
                    x=precipitation["year"],
                    y=precipitation["value"],
                    name="Niederschlag",
                    mode="lines+markers",
                    line={"color": COLORS.precipitation, "width": 1.5},
                    marker={
                        "color": COLORS.precipitation,
                        "size": 5,
                        "symbol": "square",
                    },
                ),
                secondary_y=True,
            )

        if show_evapotranspiration:
            figure.add_trace(
                go.Scatter(
                    x=etp["year"],
                    y=etp["value"],
                    name="Potenzielle Evapotranspiration",
                    mode="lines+markers",
                    line={
                        "color": COLORS.evapotranspiration,
                        "width": 1.5,
                    },
                    marker={
                        "color": COLORS.evapotranspiration,
                        "size": 5,
                        "symbol": "diamond",
                    },
                ),
                secondary_y=True,
            )

        figure.update_xaxes(title_text="Jahr")
        figure.update_yaxes(title_text="GWN [mm/a]", secondary_y=False)
        figure.update_yaxes(
            title_text="Niederschlag / ETp [mm/a]",
            secondary_y=True,
        )
        return apply_dashboard_layout(
            figure,
            title=f"Grundwasserneubildung – {groundwater_body}",
            height=600,
            hovermode="x unified",
        )

    def create_correlation(
        self,
        data: DashboardData,
        groundwater_body: str,
    ) -> go.Figure | None:
        """Create an exploratory recharge–precipitation scatter plot.
        
        Args:
            data: Value of type ``DashboardData``.
            groundwater_body: Value of type ``str``.
        
        Returns:
            go.Figure | None: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        recharge = data.groundwater_recharge.query(
            "GWK_ID == @groundwater_body"
        )[["year", "gwn_mm_a"]]
        precipitation = data.precipitation.query(
            "GWK_ID == @groundwater_body"
        )[["year", "value"]]
        merged = recharge.merge(precipitation, on="year").dropna()
        if len(merged) < 2:
            return None

        regression = linregress(merged["value"], merged["gwn_mm_a"])
        figure = px.scatter(
            merged,
            x="value",
            y="gwn_mm_a",
            hover_data=["year"],
            labels={
                "value": "Niederschlag [mm/a]",
                "gwn_mm_a": "GWN [mm/a]",
            },
            color_discrete_sequence=[COLORS.groundwater],
        )
        figure.update_traces(marker={"color": COLORS.groundwater, "size": 8})

        x_fit = np.linspace(merged["value"].min(), merged["value"].max(), 100)
        figure.add_trace(
            go.Scatter(
                x=x_fit,
                y=regression.slope * x_fit + regression.intercept,
                mode="lines",
                name=(
                    f"Regression (R²={regression.rvalue ** 2:.3f}, "
                    f"p={regression.pvalue:.4f})"
                ),
                line={"color": COLORS.brand_primary, "width": 2},
            )
        )
        return apply_dashboard_layout(
            figure,
            title=f"Korrelation: GWN vs. Niederschlag – {groundwater_body}",
            height=500,
        )

    def create_period_comparison(
        self,
        comparison_data: pd.DataFrame,
        reference_period: Period | None = None,
        comparison_period: Period | None = None,
    ) -> go.Figure:
        """Create a groundwater-body period-comparison figure.
        
        Args:
            comparison_data: Value of type ``pd.DataFrame``.
            reference_period: Value of type ``Period | None``.
            comparison_period: Value of type ``Period | None``.
        
        Returns:
            go.Figure: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        reference, comparison = self._resolve_periods(
            reference_period,
            comparison_period,
        )
        figure = go.Figure()
        figure.add_bar(
            x=comparison_data["GWK_ID"],
            y=comparison_data["mean_ref"],
            name=reference.label,
            marker_color=COLORS.reference_period,
        )
        figure.add_bar(
            x=comparison_data["GWK_ID"],
            y=comparison_data["mean_hist"],
            name=comparison.label,
            marker_color=COLORS.comparison_period,
        )
        figure.update_layout(barmode="group", yaxis_title="GWN [mm/a]")
        return apply_dashboard_layout(
            figure,
            title=(
                "Vergleich der mittleren Grundwasserneubildung "
                f"({reference.label} / {comparison.label})"
            ),
            height=400,
        )

    def create_change_histogram(self, comparison: pd.DataFrame) -> go.Figure:
        """Create a histogram of groundwater-recharge changes.
        
        Args:
            comparison: Value of type ``pd.DataFrame``.
        
        Returns:
            go.Figure: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        figure = px.histogram(
            comparison,
            x="delta_abs",
            nbins=20,
            labels={"delta_abs": "Änderung GWN [mm/a]"},
            color_discrete_sequence=[COLORS.groundwater],
        )
        return apply_dashboard_layout(
            figure,
            title="Verteilung der GWN-Änderungen",
            height=400,
        )

    def create_value_histogram(
        self,
        data: pd.DataFrame,
        value_column: str,
        title: str,
    ) -> go.Figure:
        """Create a compact histogram for the map statistics panel."""

        figure = px.histogram(
            data.dropna(subset=[value_column]),
            x=value_column,
            nbins=8,
            labels={value_column: title},
            color_discrete_sequence=[COLORS.brand_primary],
        )
        figure.update_layout(showlegend=False)
        return apply_dashboard_layout(
            figure,
            title="",
            height=260,
        )

    def create_period_boxplot(
        self,
        comparison_data: pd.DataFrame,
        reference_period: Period | None = None,
        comparison_period: Period | None = None,
    ) -> go.Figure:
        """Create box plots for reference and comparison values.
        
        Args:
            comparison_data: Value of type ``pd.DataFrame``.
            reference_period: Value of type ``Period | None``.
            comparison_period: Value of type ``Period | None``.
        
        Returns:
            go.Figure: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        reference, comparison = self._resolve_periods(
            reference_period,
            comparison_period,
        )
        box_data = pd.concat(
            [
                comparison_data[["GWK_ID", "mean_ref"]]
                .rename(columns={"mean_ref": "GWN"})
                .assign(Periode=reference.label),
                comparison_data[["GWK_ID", "mean_hist"]]
                .rename(columns={"mean_hist": "GWN"})
                .assign(Periode=comparison.label),
            ],
            ignore_index=True,
        )
        figure = px.box(
            box_data,
            x="Periode",
            y="GWN",
            color="Periode",
            color_discrete_map={
                reference.label: COLORS.reference_period,
                comparison.label: COLORS.comparison_period,
            },
        )
        return apply_dashboard_layout(
            figure,
            title="Verteilung der mittleren GWN nach Periode",
            height=400,
        )

    def _resolve_periods(
        self,
        reference_period: Period | None,
        comparison_period: Period | None,
    ) -> tuple[Period, Period]:
        return (
            reference_period or self._config.reference_period,
            comparison_period or self._config.comparison_period,
        )
