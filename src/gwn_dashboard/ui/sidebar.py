"""Sidebar controls."""

import streamlit as st

from gwn_dashboard.domain.models import SidebarSelection


class Sidebar:
    """Render dashboard filters and return a typed selection object."""

    def render(self, available_groundwater_bodies: list[str]) -> SidebarSelection:
        st.sidebar.header("⚙️ Konfiguration")
        selection_mode = st.sidebar.radio(
            "Auswahlmodus:",
            ("Eigene Auswahl", "Alle GWK"),
            index=1,
        )

        if selection_mode == "Eigene Auswahl":
            defaults = [
                groundwater_body
                for groundwater_body in ("DESN_EL-2-1", "DESN_NE-3")
                if groundwater_body in available_groundwater_bodies
            ]
            if not defaults:
                defaults = available_groundwater_bodies[:2]
            selected_ids = st.sidebar.multiselect(
                "Grundwasserkörper auswählen:",
                options=available_groundwater_bodies,
                default=defaults,
            )
            if not selected_ids:
                st.sidebar.warning("Bitte mindestens einen Grundwasserkörper auswählen.")
                st.stop()
        else:
            selected_ids = available_groundwater_bodies
            st.sidebar.info(f"{len(selected_ids)} Grundwasserkörper ausgewählt")

        search_term = st.sidebar.text_input("🔍 GWK suchen:", placeholder="z. B. DESN_EL")
        detail_options = [
            groundwater_body
            for groundwater_body in selected_ids
            if search_term.upper() in groundwater_body.upper()
        ] if search_term else list(selected_ids)
        if not detail_options:
            st.sidebar.warning("Kein passender Grundwasserkörper gefunden.")
            detail_options = list(selected_ids)

        selected_groundwater_body = st.sidebar.selectbox(
            "GWK für Detailansicht:",
            options=detail_options,
        )
        show_precipitation = st.sidebar.checkbox("Niederschlag anzeigen", value=True)
        show_evapotranspiration = st.sidebar.checkbox("ETp anzeigen", value=False)

        return SidebarSelection(
            groundwater_body_ids=tuple(selected_ids),
            selected_groundwater_body=selected_groundwater_body,
            show_precipitation=show_precipitation,
            show_evapotranspiration=show_evapotranspiration,
        )
