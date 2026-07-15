"""Common controls placed in the viewer-style toolbar and side panels."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st

from gwn_dashboard.domain.models import SidebarSelection


class ViewerControls:
    """Maintain the spatial selection shared by all workspace modules."""

    MODEL_LABEL = "KliWES 3.0 - Simulation - kalib_beo_ERA5"

    def render_toolbar(self, available_groundwater_bodies: Sequence[str]) -> SidebarSelection:
        """Render only controls that have an actual effect on the application."""

        available = self._validated_available(available_groundwater_bodies)
        mode_default = st.session_state.get("viewer_selection_mode", "Alle Grundwasserkörper")

        col_room, col_model, col_detail = st.columns([1.15, 1.65, 1.65], gap="small")
        with col_room:
            mode = st.selectbox(
                "Raumauswahl",
                options=("Alle Grundwasserkörper", "Eigene Auswahl"),
                index=0 if mode_default == "Alle Grundwasserkörper" else 1,
                key="viewer_selection_mode",
            )
        with col_model:
            self.static_field("Modell", self.MODEL_LABEL)

        if mode == "Eigene Auswahl":
            current = st.session_state.get("viewer_selected_ids", available[:3])
            selected_ids = st.multiselect(
                "Grundwasserkörper auswählen",
                options=available,
                default=[value for value in current if value in available],
                key="viewer_selected_ids",
            )
            if not selected_ids:
                st.warning("Bitte mindestens einen Grundwasserkörper auswählen.")
                st.stop()
        else:
            selected_ids = available

        previous_detail = st.session_state.get("viewer_detail_gwk")
        default_index = selected_ids.index(previous_detail) if previous_detail in selected_ids else 0
        with col_detail:
            detail = st.selectbox(
                "Detail-GWK",
                options=selected_ids,
                index=default_index,
                key="viewer_detail_gwk",
            )

        return self._selection(selected_ids, detail)

    def current_selection(
        self,
        available_groundwater_bodies: Sequence[str],
    ) -> SidebarSelection:
        """Return a selection without rendering the toolbar."""

        available = self._validated_available(available_groundwater_bodies)
        mode = st.session_state.get("viewer_selection_mode", "Alle Grundwasserkörper")
        if mode == "Eigene Auswahl":
            selected = [
                value
                for value in st.session_state.get("viewer_selected_ids", available[:3])
                if value in available
            ]
            selected_ids = selected or available[:1]
        else:
            selected_ids = available
        detail = st.session_state.get("viewer_detail_gwk")
        if detail not in selected_ids:
            detail = selected_ids[0]
        return self._selection(selected_ids, detail)

    def render_diagram_controls(self, selection: SidebarSelection) -> tuple[bool, bool]:
        """Render the original time-series options without decorative pseudo-controls."""

        st.markdown('<div class="viewer-panel-heading">Grundwasserneubildung</div>', unsafe_allow_html=True)
        self.static_field("Modell", self.MODEL_LABEL)
        self.static_field("Parameter", "Grundwasserneubildung GWN")
        self.static_field("Raum", selection.selected_groundwater_body)

        st.markdown('<div class="viewer-panel-separator"></div>', unsafe_allow_html=True)
        st.markdown('<div class="viewer-panel-heading">Meteorologische Vergleichsgrößen</div>', unsafe_allow_html=True)
        show_precipitation = st.checkbox(
            "Niederschlag P anzeigen",
            value=bool(st.session_state.get("viewer_show_precipitation", True)),
            key="viewer_show_precipitation",
        )
        show_etp = st.checkbox(
            "Potenzielle Evapotranspiration ETp anzeigen",
            value=bool(st.session_state.get("viewer_show_etp", False)),
            key="viewer_show_etp",
        )

        st.markdown('<div class="viewer-panel-separator"></div>', unsafe_allow_html=True)
        st.markdown('<div class="viewer-panel-heading">Zeitraum</div>', unsafe_allow_html=True)
        self.static_field("Zeitraum", "1961–2020")
        self.static_field("Zeitschritt", "Jahr")
        return show_precipitation, show_etp

    @staticmethod
    def static_field(label: str, value: str) -> None:
        """Render a clearly read-only value instead of a one-option menu."""

        st.html(
            f'<div class="viewer-static-field"><span>{escape(label)}</span>'
            f'<strong>{escape(str(value))}</strong></div>'
        )

    @staticmethod
    def _validated_available(values: Sequence[str]) -> list[str]:
        available = list(values)
        if not available:
            raise ValueError("Keine Grundwasserkörper verfügbar.")
        return available

    @staticmethod
    def _selection(selected_ids: Sequence[str], detail: str) -> SidebarSelection:
        return SidebarSelection(
            groundwater_body_ids=tuple(selected_ids),
            selected_groundwater_body=str(detail),
            show_precipitation=bool(st.session_state.get("viewer_show_precipitation", True)),
            show_evapotranspiration=bool(st.session_state.get("viewer_show_etp", False)),
        )
