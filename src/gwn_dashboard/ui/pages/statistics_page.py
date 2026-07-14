"""Statistics page."""

import streamlit as st

from gwn_dashboard.domain.models import DashboardData
from gwn_dashboard.ui.pages.base_page import BasePage


class StatisticsPage(BasePage):
    def __init__(self, data: DashboardData) -> None:
        self._data = data

    @property
    def label(self) -> str:
        return "📋 Statistiken"

    def render(self) -> None:
        st.header("Vollständige Statistiken")
        significant_only = st.checkbox("Nur lineare Trends mit p < 0,05 anzeigen", value=False)
        trends = self._data.trends
        if significant_only:
            trends = trends[trends["lr_pvalue"] < 0.05]
        st.subheader("Trendanalyse")
        st.dataframe(trends, use_container_width=True, height=400)
        st.subheader("Periodenvergleich")
        st.dataframe(self._data.comparison, use_container_width=True, height=400)
