"""Application header for the platform and groundwater quantity module."""

from __future__ import annotations

from html import escape

import streamlit as st

from gwn_dashboard.ui.navigation import (
    GROUNDWATER_QUANTITY,
    GROUNDWATER_QUANTITY_ROUTES,
    START,
)


class AppHeader:
    """Render the fixed header with route-specific navigation targets."""

    def render(self, active_route: str) -> None:
        """Render the component or page in Streamlit.
        
        Args:
            active_route: Value of type ``str``.
        """
        if active_route in GROUNDWATER_QUANTITY_ROUTES:
            title = "GWN Viewer"
            subtitle = "Interne Plattform Referat 43"
            brand_route = GROUNDWATER_QUANTITY.key
            brand_class = "viewer-brand"
        else:
            title = "Plattform für Datenaufbereitung und  &#8209;visualisierung"
            subtitle = "Interne Plattform Referat 43"
            brand_route = START.key
            brand_class = "viewer-brand viewer-brand-platform"

        st.html(
            f"""
            <header class="viewer-header">
                <a class="{brand_class}" href="?view={escape(brand_route)}"
                   target="_self" aria-label="Zur Bereichsübersicht">
                    <span class="viewer-brand-title">{escape(title)}</span>
                    <span class="viewer-brand-divider"></span>
                    <span class="viewer-brand-subtitle">{escape(subtitle)}</span>
                </a>
                <nav class="viewer-header-links" aria-label="Servicenavigation">
                    <a href="?view={START.key}" target="_self">Home</a>
                </nav>
            </header>
            """
        )
