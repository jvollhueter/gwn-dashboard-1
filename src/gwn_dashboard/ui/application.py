"""Object-oriented Streamlit application."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from gwn_dashboard.application import AppContext, create_app_context
from gwn_dashboard.config import DashboardConfig, load_config
from gwn_dashboard.domain.models import DashboardData
from gwn_dashboard.ui.components.export_panel import ExportPanel
from gwn_dashboard.ui.components.metric_panel import MetricPanel
from gwn_dashboard.ui.pages.comparison_page import ComparisonPage
from gwn_dashboard.ui.pages.correlation_page import CorrelationPage
from gwn_dashboard.ui.pages.map_page import MapPage
from gwn_dashboard.ui.pages.statistics_page import StatisticsPage
from gwn_dashboard.ui.pages.timeseries_page import TimeSeriesPage
from gwn_dashboard.ui.sidebar import Sidebar


@st.cache_resource
def _create_cached_context(project_root: str) -> AppContext:
    root = Path(project_root)
    return create_app_context(load_config(root))


@st.cache_data
def _load_cached_data(project_root: str, selected_ids: tuple[str, ...]) -> DashboardData:
    return _create_cached_context(project_root).dashboard_service.load_dashboard_data(selected_ids)


@st.cache_data
def _load_cached_geometries(project_root: str):
    return _create_cached_context(project_root).dashboard_service.load_geometries()


class StreamlitApplication:
    """Configure the GUI and compose independent page objects."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._config: DashboardConfig = load_config(project_root)
        self._context: AppContext | None = None

    def run(self) -> None:
        self._configure_page()
        self._context = _create_cached_context(str(self._project_root))
        st.title(f"💧 {self._config.application.title}")
        st.markdown("---")

        try:
            available = self._context.dashboard_service.get_available_groundwater_bodies()
        except Exception as error:
            self._show_fatal_error("GWK-Mapping konnte nicht geladen werden", error)
            return

        selection = Sidebar().render(available)
        try:
            with st.spinner("Daten werden geladen und verarbeitet …"):
                data = _load_cached_data(str(self._project_root), selection.groundwater_body_ids)
        except Exception as error:
            self._show_fatal_error("Daten konnten nicht geladen werden", error)
            return

        MetricPanel(self._config).render(data, selection)
        pages = [
            TimeSeriesPage(self._config, self._context, data, selection),
            CorrelationPage(self._context, data, selection),
            ComparisonPage(self._context, data),
            StatisticsPage(data),
            MapPage(
                self._context,
                data,
                selection,
                geometry_loader=lambda: _load_cached_geometries(str(self._project_root)),
            ),
        ]
        tabs = st.tabs([page.label for page in pages])
        for tab, page in zip(tabs, pages):
            with tab:
                page.render()

        ExportPanel(self._context.export_service).render(data, len(selection.groundwater_body_ids))

    def _configure_page(self) -> None:
        app = self._config.application
        st.set_page_config(
            page_title=app.page_title,
            page_icon=app.page_icon,
            layout=app.layout,
            initial_sidebar_state=app.initial_sidebar_state,
        )
        st.markdown(
            """
            <style>
            .main { padding: 0rem 1rem; }
            .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def _show_fatal_error(message: str, error: Exception) -> None:
        st.error(f"❌ {message}:\n\n{error}")
        with st.expander("Technische Details"):
            st.code(repr(error))
        st.stop()
