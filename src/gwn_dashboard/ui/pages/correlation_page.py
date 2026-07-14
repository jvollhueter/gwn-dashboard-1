"""Correlation page."""

import streamlit as st

from gwn_dashboard.application import AppContext
from gwn_dashboard.domain.models import DashboardData, SidebarSelection
from gwn_dashboard.ui.pages.base_page import BasePage


class CorrelationPage(BasePage):
    def __init__(self, context: AppContext, data: DashboardData, selection: SidebarSelection) -> None:
        self._context = context
        self._data = data
        self._selection = selection

    @property
    def label(self) -> str:
        return "🔄 Korrelation"

    def render(self) -> None:
        groundwater_body = self._selection.selected_groundwater_body
        st.header(f"Korrelationsanalyse: {groundwater_body}")
        figure = self._context.chart_factory.create_correlation(self._data, groundwater_body)
        if figure is None:
            st.warning("Keine ausreichenden Daten für die Korrelationsanalyse vorhanden.")
            return
        st.plotly_chart(figure, use_container_width=True)
        st.info("Die Darstellung zeigt einen explorativen linearen Zusammenhang. R² beschreibt die Stärke des linearen Zusammenhangs; eine Korrelation ist kein Kausalitätsnachweis.")
