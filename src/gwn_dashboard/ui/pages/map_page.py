"""Spatial overview page."""

from collections.abc import Callable

import geopandas as gpd
import streamlit as st

from gwn_dashboard.application import AppContext
from gwn_dashboard.domain.models import DashboardData, SidebarSelection
from gwn_dashboard.ui.pages.base_page import BasePage


class MapPage(BasePage):
    def __init__(
        self,
        context: AppContext,
        data: DashboardData,
        selection: SidebarSelection,
        geometry_loader: Callable[[], gpd.GeoDataFrame],
    ) -> None:
        self._context = context
        self._data = data
        self._selection = selection
        self._geometry_loader = geometry_loader

    @property
    def label(self) -> str:
        return "🗺️ Übersichtskarte"

    def render(self) -> None:
        st.header("Räumliche Übersicht")
        try:
            geometries = self._geometry_loader()
        except Exception as error:
            st.error(f"Geometrien konnten nicht geladen werden: {error}")
            return
        figure = self._context.map_factory.create_choropleth(
            geometries,
            self._data.comparison,
            self._selection.selected_groundwater_body,
        )
        if figure is None:
            st.warning("Keine Geometrien verfügbar.")
            return
        st.plotly_chart(figure, use_container_width=True)
        st.subheader("Verteilung der Änderungen")
        st.plotly_chart(
            self._context.chart_factory.create_change_histogram(self._data.comparison),
            use_container_width=True,
        )
        st.subheader("Verteilung nach Perioden")
        st.plotly_chart(
            self._context.chart_factory.create_period_boxplot(self._data.comparison),
            use_container_width=True,
        )
