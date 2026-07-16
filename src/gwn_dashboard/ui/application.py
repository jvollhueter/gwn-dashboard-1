"""Object-oriented Streamlit application with a viewer-style navigation shell."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from gwn_dashboard.application import AppContext, create_app_context
from gwn_dashboard.config import DashboardConfig, load_config
from gwn_dashboard.design.style_loader import load_global_styles
from gwn_dashboard.domain.models import DashboardData, Period
from gwn_dashboard.repositories.script_library_repository import (
    ScriptLibraryRepository,
)
from gwn_dashboard.services.script_library_service import ScriptLibraryService
from gwn_dashboard.ui.components.app_header import AppHeader
from gwn_dashboard.ui.components.bottom_navigation import BottomNavigation
from gwn_dashboard.ui.components.viewer_controls import ViewerControls
from gwn_dashboard.ui.navigation import (
    DIAGRAMS,
    EXPORT,
    GROUNDWATER_DATA,
    GROUNDWATER_QUALITY,
    GROUNDWATER_QUANTITY,
    INFORMATION,
    MAPS,
    METEOROLOGICAL_DATA,
    NOMOGRAMS,
    SCRIPT_LIBRARY,
    START,
    current_route,
    reset_session_if_requested,
)
from gwn_dashboard.ui.pages.diagram_page import DiagramPage
from gwn_dashboard.ui.pages.export_page import ExportPage
from gwn_dashboard.ui.pages.information_page import InformationPage
from gwn_dashboard.ui.pages.landing_page import (
    GroundwaterDataLandingPage,
    LandingPage,
    PlaceholderLandingPage,
    PlatformLandingPage,
)
from gwn_dashboard.ui.pages.map_page import MapPage
from gwn_dashboard.ui.pages.nomogram_page import NomogramPage
from gwn_dashboard.ui.pages.script_library_page import ScriptLibraryPage


@st.cache_resource
def _create_cached_context(project_root: str) -> AppContext:
    root = Path(project_root)
    return create_app_context(load_config(root))


@st.cache_resource
def _create_script_library_service(project_root: str) -> ScriptLibraryService:
    library_root = Path(project_root) / "script_library"
    return ScriptLibraryService(ScriptLibraryRepository(library_root))


@st.cache_data
def _load_cached_year_range(project_root: str) -> tuple[int, int]:
    return _create_cached_context(
        project_root
    ).dashboard_service.get_available_year_range()


@st.cache_data
def _load_cached_data(
    project_root: str,
    selected_ids: tuple[str, ...],
    reference_start: int,
    reference_end: int,
    comparison_start: int,
    comparison_end: int,
) -> DashboardData:
    reference_period = Period(
        f"{reference_start}–{reference_end}",
        reference_start,
        reference_end,
    )
    comparison_period = Period(
        f"{comparison_start}–{comparison_end}",
        comparison_start,
        comparison_end,
    )
    return _create_cached_context(project_root).dashboard_service.load_dashboard_data(
        selected_ids,
        reference_period=reference_period,
        comparison_period=comparison_period,
    )


@st.cache_data
def _load_cached_geometries(project_root: str):
    return _create_cached_context(project_root).dashboard_service.load_geometries()


@st.cache_data
def _load_cached_monitoring_stations(project_root: str):
    return (
        _create_cached_context(project_root)
        .dashboard_service.load_monitoring_stations()
    )


class StreamlitApplication:
    """Configure the application and route between landing and viewer modules."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._config: DashboardConfig = load_config(project_root)
        self._context: AppContext | None = None

    def run(self) -> None:
        """Render the complete application for the current request.
        """
        self._configure_page()
        reset_session_if_requested()
        route = current_route()
        AppHeader().render(route)
        background_path = (
            self._project_root
            / "src"
            / "gwn_dashboard"
            / "ui"
            / "assets"
            / "landing_background.jpg"
        )

        if route == START.key:
            PlatformLandingPage(background_path).render()
            return

        if route == GROUNDWATER_DATA.key:
            GroundwaterDataLandingPage(background_path).render()
            return

        if route == GROUNDWATER_QUANTITY.key:
            LandingPage(background_path).render()
            return

        if route == GROUNDWATER_QUALITY.key:
            PlaceholderLandingPage(
                background_path,
                title="Grundwasserqualität",
                subtitle="Datenvisualisierung und Aufbereitung zur Grundwasserqualität",
                icon_filename="labor-ausstattung.png",
            ).render()
            return

        if route == METEOROLOGICAL_DATA.key:
            PlaceholderLandingPage(
                background_path,
                title="Meteorologische Daten",
                subtitle="Datenvisualisierung und Aufbereitung meteorologischer Daten",
                icon_filename="wetter.png",
            ).render()
            return

        if route == SCRIPT_LIBRARY.key:
            ScriptLibraryPage(
                _create_script_library_service(str(self._project_root))
            ).render()
            return

        if route == INFORMATION.key:
            InformationPage().render()
            BottomNavigation().render(route)
            return

        self._context = _create_cached_context(str(self._project_root))
        try:
            available = (
                self._context.dashboard_service.get_available_groundwater_bodies()
            )
            minimum_year, maximum_year = _load_cached_year_range(
                str(self._project_root)
            )
        except Exception as error:
            self._show_fatal_error(
                "Datenbasis konnte nicht initialisiert werden",
                error,
            )
            return

        controls = ViewerControls(
            self._config.reference_period,
            self._config.comparison_period,
        )
        if route == EXPORT.key:
            selection = controls.current_selection(
                available,
                minimum_year,
                maximum_year,
            )
        else:
            selection = controls.render_toolbar(
                available,
                minimum_year,
                maximum_year,
            )

        try:
            with st.spinner("Daten werden geladen und verarbeitet …"):
                data = _load_cached_data(
                    str(self._project_root),
                    selection.groundwater_body_ids,
                    selection.reference_period.start_year,
                    selection.reference_period.end_year,
                    selection.comparison_period.start_year,
                    selection.comparison_period.end_year,
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
                station_loader=lambda: _load_cached_monitoring_stations(
                    str(self._project_root)
                ),
                available_groundwater_bodies=available,
            ).render()
        elif route == DIAGRAMS.key:
            DiagramPage(self._config, self._context, data, selection).render()
        elif route == NOMOGRAMS.key:
            NomogramPage(self._context, data, selection).render()
        elif route == EXPORT.key:
            ExportPage(
                self._context,
                data,
                selection,
                minimum_year,
                maximum_year,
            ).render()
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
