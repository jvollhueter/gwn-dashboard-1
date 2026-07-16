"""Statistics page."""

import streamlit as st

from gwn_dashboard.domain.models import DashboardData
from gwn_dashboard.ui.pages.base_page import BasePage


class StatisticsPage(BasePage):
    """Render descriptive and trend-statistics tables and graphics.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    def __init__(self, data: DashboardData) -> None:
        self._data = data

    @property
    def label(self) -> str:
        """Return the human-readable page label.
        
        Returns:
            str: Result produced by the operation.
        """
        return "📋 Statistiken"

    def render(self) -> None:
        """Render the component or page in Streamlit.
        """
        st.header("Vollständige Statistiken")
        significant_only = st.checkbox("Nur lineare Trends mit p < 0,05 anzeigen", value=False)
        trends = self._data.trends
        if significant_only:
            trends = trends[trends["lr_pvalue"] < 0.05]
        st.subheader("Trendanalyse")
        st.dataframe(trends, use_container_width=True, height=400)
        st.subheader("Periodenvergleich")
        st.dataframe(self._data.comparison, use_container_width=True, height=400)
