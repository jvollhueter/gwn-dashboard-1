"""Query-parameter based navigation for the platform and its modules."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class ViewerRoute:
    """One route shown by the application shell."""

    key: str
    label: str


START = ViewerRoute("platform", "Start")
GROUNDWATER_DATA = ViewerRoute("groundwater-data", "Grundwasserdaten")
GROUNDWATER_QUANTITY = ViewerRoute(
    "groundwater-quantity",
    "Grundwasserquantität",
)
GROUNDWATER_QUALITY = ViewerRoute(
    "groundwater-quality",
    "Grundwasserqualität",
)
METEOROLOGICAL_DATA = ViewerRoute(
    "meteorological-data",
    "Meteorologische Daten",
)
SCRIPT_LIBRARY = ViewerRoute("script-library", "Script-Bibliothek")

MAPS = ViewerRoute("maps", "Karten")
DIAGRAMS = ViewerRoute("diagrams", "Diagramme")
NOMOGRAMS = ViewerRoute("nomograms", "Nomogramme")
EXPORT = ViewerRoute("export", "Datenexport")
INFORMATION = ViewerRoute("information", "Information")

PLATFORM_ROUTES = (
    START,
    GROUNDWATER_DATA,
    GROUNDWATER_QUANTITY,
    GROUNDWATER_QUALITY,
    METEOROLOGICAL_DATA,
    SCRIPT_LIBRARY,
)
WORKSPACE_ROUTES = (MAPS, DIAGRAMS, NOMOGRAMS, EXPORT, INFORMATION)
GROUNDWATER_QUANTITY_ROUTES = {
    GROUNDWATER_QUANTITY.key,
    *(route.key for route in WORKSPACE_ROUTES),
}
VALID_ROUTE_KEYS = {
    *(route.key for route in PLATFORM_ROUTES),
    *(route.key for route in WORKSPACE_ROUTES),
}


def current_route() -> str:
    """Return the current route from the URL, falling back to the platform."""

    value = st.query_params.get("view", START.key)
    if isinstance(value, list):
        value = value[0] if value else START.key
    value = str(value)
    return value if value in VALID_ROUTE_KEYS else START.key


def current_information_section() -> str:
    """Return an optional anchor-like information section."""

    value = st.query_params.get("section", "overview")
    if isinstance(value, list):
        value = value[0] if value else "overview"
    return str(value)


def reset_session_if_requested() -> None:
    """Clear dashboard selections when the reset route parameter is present."""

    reset = st.query_params.get("reset")
    if reset not in {"1", 1, True, "true"}:
        return

    for key in list(st.session_state):
        if key.startswith("viewer_"):
            del st.session_state[key]

    st.query_params.clear()
    st.query_params["view"] = START.key
    st.rerun()
