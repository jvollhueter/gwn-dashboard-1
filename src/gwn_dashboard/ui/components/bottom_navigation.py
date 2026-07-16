"""Fixed viewer-style bottom navigation."""

from __future__ import annotations

from html import escape

import streamlit as st

from gwn_dashboard.ui.navigation import INFORMATION, WORKSPACE_ROUTES


class BottomNavigation:
    """Render the fixed module navigation and highlight the active route."""

    def render(self, active_route: str) -> None:
        """Render the component or page in Streamlit.
        
        Args:
            active_route: Value of type ``str``.
        """
        module_links = []
        for route in WORKSPACE_ROUTES:
            if route is INFORMATION:
                continue
            active = " viewer-nav-active" if route.key == active_route else ""
            module_links.append(
                f'<a class="viewer-bottom-link{active}" href="?view={escape(route.key)}" '
                f'target="_self">{escape(route.label)}</a>'
            )

        information_active = " viewer-nav-active" if active_route == INFORMATION.key else ""
        st.html(
            f"""
            <nav class="viewer-bottom-nav" aria-label="Modulnavigation">
                <div class="viewer-bottom-modules">{''.join(module_links)}</div>
                <a class="viewer-bottom-link viewer-bottom-info{information_active}"
                   href="?view={INFORMATION.key}" target="_self">Information</a>
            </nav>
            """
        )
