"""Plotly chart factory."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import linregress

from gwn_dashboard.config import DashboardConfig
from gwn_dashboard.domain.models import DashboardData


class ChartFactory:
    def __init__(self, config: DashboardConfig) -> None:
        self._config = config

    def create_timeseries(self, data: DashboardData, groundwater_body: str, show_precipitation: bool, show_evapotranspiration: bool) -> go.Figure:
        recharge = data.groundwater_recharge.query("GWK_ID == @groundwater_body").sort_values("year")
        precipitation = data.precipitation.query("GWK_ID == @groundwater_body").sort_values("year")
        etp = data.evapotranspiration.query("GWK_ID == @groundwater_body").sort_values("year")
        figure = make_subplots(specs=[[{"secondary_y": True}]])
        figure.add_trace(go.Scatter(x=recharge["year"], y=recharge["gwn_mm_a"], name="GWN", mode="lines+markers", line={"color": "steelblue", "width": 3}), secondary_y=False)
        for period, color in ((self._config.reference_period, "darkgreen"), (self._config.comparison_period, "darkorange")):
            mean_value = recharge.loc[recharge["year"].between(period.start_year, period.end_year), "gwn_mm_a"].mean()
            figure.add_trace(go.Scatter(x=[period.start_year, period.end_year], y=[mean_value, mean_value], name=f"GWN Ø {period.label} ({mean_value:.1f} mm/a)", mode="lines", line={"color": color, "dash": "dash"}), secondary_y=False)
            figure.add_vrect(x0=period.start_year, x1=period.end_year, fillcolor=color, opacity=0.08, line_width=0)
        if show_precipitation:
            figure.add_trace(go.Scatter(x=precipitation["year"], y=precipitation["value"], name="Niederschlag", mode="lines", line={"color": "darkblue", "dash": "dot"}), secondary_y=True)
        if show_evapotranspiration:
            figure.add_trace(go.Scatter(x=etp["year"], y=etp["value"], name="ETp", mode="lines", line={"color": "orangered", "dash": "dot"}), secondary_y=True)
        figure.update_xaxes(title_text="Jahr")
        figure.update_yaxes(title_text="GWN [mm/a]", secondary_y=False)
        figure.update_yaxes(title_text="Niederschlag / ETp [mm/a]", secondary_y=True)
        figure.update_layout(title=f"<b>Grundwasserneubildung – {groundwater_body}</b>", hovermode="x unified", height=600, template="plotly_white")
        return figure

    def create_correlation(self, data: DashboardData, groundwater_body: str) -> go.Figure | None:
        recharge = data.groundwater_recharge.query("GWK_ID == @groundwater_body")[["year", "gwn_mm_a"]]
        precipitation = data.precipitation.query("GWK_ID == @groundwater_body")[["year", "value"]]
        merged = recharge.merge(precipitation, on="year").dropna()
        if len(merged) < 2:
            return None
        regression = linregress(merged["value"], merged["gwn_mm_a"])
        figure = px.scatter(merged, x="value", y="gwn_mm_a", hover_data=["year"], labels={"value": "Niederschlag [mm/a]", "gwn_mm_a": "GWN [mm/a]"})
        x_fit = np.linspace(merged["value"].min(), merged["value"].max(), 100)
        figure.add_trace(go.Scatter(x=x_fit, y=regression.slope * x_fit + regression.intercept, mode="lines", name=f"Regression (R²={regression.rvalue ** 2:.3f}, p={regression.pvalue:.4f})"))
        figure.update_layout(title=f"<b>Korrelation: GWN vs. Niederschlag – {groundwater_body}</b>", height=500, template="plotly_white")
        return figure

    def create_period_comparison(self, comparison: pd.DataFrame) -> go.Figure:
        figure = go.Figure()
        figure.add_bar(x=comparison["GWK_ID"], y=comparison["mean_ref"], name=self._config.reference_period.label)
        figure.add_bar(x=comparison["GWK_ID"], y=comparison["mean_hist"], name=self._config.comparison_period.label)
        figure.update_layout(barmode="group", height=400, template="plotly_white", yaxis_title="GWN [mm/a]")
        return figure

    def create_change_histogram(self, comparison: pd.DataFrame) -> go.Figure:
        return px.histogram(comparison, x="delta_abs", nbins=20, labels={"delta_abs": "Änderung GWN [mm/a]"})

    def create_period_boxplot(self, comparison: pd.DataFrame) -> go.Figure:
        box_data = pd.concat([
            comparison[["GWK_ID", "mean_ref"]].rename(columns={"mean_ref": "GWN"}).assign(Periode=self._config.reference_period.label),
            comparison[["GWK_ID", "mean_hist"]].rename(columns={"mean_hist": "GWN"}).assign(Periode=self._config.comparison_period.label),
        ], ignore_index=True)
        return px.box(box_data, x="Periode", y="GWN", color="Periode")
