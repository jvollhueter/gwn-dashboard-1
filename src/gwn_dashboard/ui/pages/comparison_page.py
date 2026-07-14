"""Groundwater-body comparison page."""

import streamlit as st

from gwn_dashboard.application import AppContext
from gwn_dashboard.domain.models import DashboardData
from gwn_dashboard.ui.pages.base_page import BasePage


class ComparisonPage(BasePage):
    def __init__(self, context: AppContext, data: DashboardData) -> None:
        self._context = context
        self._data = data

    @property
    def label(self) -> str:
        return "📊 Vergleich"

    def render(self) -> None:
        st.header("Vergleich der ausgewählten Grundwasserkörper")
        st.plotly_chart(
            self._context.chart_factory.create_period_comparison(self._data.comparison),
            use_container_width=True,
        )
        sort_by = st.selectbox(
            "Sortieren nach:",
            ("GWK_ID", "delta_abs", "delta_rel_pct", "mean_ref", "mean_hist"),
        )
        ascending = st.checkbox("Aufsteigend sortieren", value=True)
        table = self._data.comparison.sort_values(sort_by, ascending=ascending)
        st.dataframe(table, use_container_width=True, height=450)
