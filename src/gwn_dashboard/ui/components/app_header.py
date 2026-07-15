"""Viewer-style application header."""

from __future__ import annotations

import streamlit as st


class AppHeader:
    """Render the dark-green header shared by landing and workspace pages."""

    def render(self) -> None:
        st.html(
            """
            <header class="viewer-header">
                <a class="viewer-brand" href="?view=start" target="_self" aria-label="Zur Startseite">
                    <span class="viewer-brand-title">GWN Viewer</span>
                    <span class="viewer-brand-divider"></span>
                    <span class="viewer-brand-subtitle">Interne Plattform Referat 43</span>
                </a>
                <nav class="viewer-header-links" aria-label="Servicenavigation">
                    <a href="?view=start" target="_self">Home</a>
                </nav>
            </header>
            """
        )
