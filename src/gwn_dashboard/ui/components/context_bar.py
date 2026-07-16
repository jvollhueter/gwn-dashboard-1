"""Compact context bar shown above the analysis workspace."""

from html import escape

import streamlit as st

from gwn_dashboard.config import DashboardConfig
from gwn_dashboard.domain.models import SidebarSelection


class ContextBar:
    """Summarize the active spatial and temporal selections."""

    def __init__(self, config: DashboardConfig) -> None:
        self._config = config

    def render(self, selection: SidebarSelection) -> None:
        """Render the component or page in Streamlit.
        
        Args:
            selection: Value of type ``SidebarSelection``.
        """
        selected = len(selection.groundwater_body_ids)
        detail = escape(selection.selected_groundwater_body)
        reference = escape(self._config.reference_period.label)
        comparison = escape(self._config.comparison_period.label)

        st.markdown(
            f"""
            <div class="viewer-context-bar">
                <div class="viewer-context-item">
                    <span class="viewer-context-label">Raumauswahl</span>
                    <span class="viewer-context-value">{selected} Grundwasserkörper</span>
                </div>
                <div class="viewer-context-item">
                    <span class="viewer-context-label">Detailansicht</span>
                    <span class="viewer-context-value">{detail}</span>
                </div>
                <div class="viewer-context-item viewer-context-wide">
                    <span class="viewer-context-label">Vergleichszeiträume</span>
                    <span class="viewer-context-value">{reference} / {comparison}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
