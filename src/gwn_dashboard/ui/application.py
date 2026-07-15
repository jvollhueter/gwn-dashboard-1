"""Object-oriented Streamlit application with a viewer-style navigation shell."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from gwn_dashboard.application import AppContext, create_app_context
from gwn_dashboard.config import DashboardConfig, load_config
from gwn_dashboard.design.style_loader import load_global_styles
from gwn_dashboard.domain.models import DashboardData
from gwn_dashboard.ui.components.app_header import AppHeader
from gwn_dashboard.ui.components.bottom_navigation import BottomNavigation
from gwn_dashboard.ui.components.viewer_controls import ViewerControls
from gwn_dashboard.ui.navigation import (
    DIAGRAMS,
    EXPORT,
    INFORMATION,
    MAPS,
    NOMOGRAMS,
    START,
    current_route,
    reset_session_if_requested,
)
from gwn_dashboard.ui.pages.diagram_page import DiagramPage
from gwn_dashboard.ui.pages.export_page import ExportPage
from gwn_dashboard.ui.pages.information_page import InformationPage
from gwn_dashboard.ui.pages.landing_page import LandingPage
from gwn_dashboard.ui.pages.map_page import MapPage
from gwn_dashboard.ui.pages.nomogram_page import NomogramPage


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
    """Configure the application and route between landing and viewer modules."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._config: DashboardConfig = load_config(project_root)
        self._context: AppContext | None = None

    def run(self) -> None:
        self._configure_page()
        reset_session_if_requested()
        route = current_route()
        AppHeader().render()

        if route == START.key:
            LandingPage(
                self._project_root
                / "src"
                / "gwn_dashboard"
                / "ui"
                / "assets"
                / "landing_background.jpg"
            ).render()
            return

        if route == INFORMATION.key:
            InformationPage().render()
            BottomNavigation().render(route)
            return

        self._context = _create_cached_context(str(self._project_root))
        try:
            available = self._context.dashboard_service.get_available_groundwater_bodies()
        except Exception as error:
            self._show_fatal_error("GWK-Mapping konnte nicht geladen werden", error)
            return

        controls = ViewerControls()
        if route == EXPORT.key:
            selection = controls.current_selection(available)
        else:
            selection = controls.render_toolbar(available)

        try:
            with st.spinner("Daten werden geladen und verarbeitet …"):
                data = _load_cached_data(
                    str(self._project_root),
                    selection.groundwater_body_ids,
                )
        except Exception as error:
            self._show_fatal_error("Daten konnten nicht geladen werden", error)
            return

        if route == MAPS.key:
            MapPage(
                self._config,
                self._context,
                data,
                selection,
                geometry_loader=lambda: _load_cached_geometries(
                    str(self._project_root)
                ),
            ).render()
        elif route == DIAGRAMS.key:
            DiagramPage(self._config, self._context, data, selection).render()
        elif route == NOMOGRAMS.key:
            NomogramPage(self._context, data, selection).render()
        elif route == EXPORT.key:
            ExportPage(self._context, data, selection).render()
        else:
            InformationPage().render()

        BottomNavigation().render(route)

    def _configure_page(self) -> None:
        app = self._config.application
        st.set_page_config(
            page_title=app.page_title,
            page_icon=app.page_icon,
            layout="wide",
            initial_sidebar_state="collapsed",
        )
        load_global_styles()

    @staticmethod
    def _show_fatal_error(message: str, error: Exception) -> None:
        st.error(f"{message}:\n\n{error}")
        with st.expander("Technische Details"):
            st.code(repr(error))
        st.stop()
