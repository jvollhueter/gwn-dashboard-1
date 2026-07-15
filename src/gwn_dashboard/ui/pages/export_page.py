"""Viewer-style data export page."""

import streamlit as st

from gwn_dashboard.application import AppContext
from gwn_dashboard.domain.models import DashboardData, SidebarSelection
from gwn_dashboard.ui.components.viewer_controls import ViewerControls


class ExportPage:
    """Render selected exports and preserve all downloads from the previous UI."""

    def __init__(
        self,
        context: AppContext,
        data: DashboardData,
        selection: SidebarSelection,
    ) -> None:
        self._context = context
        self._data = data
        self._selection = selection

    def render(self) -> None:
        left, form, right = st.columns([0.55, 2.2, 0.75], gap="small")
        del left, right
        with form:
            with st.container(border=True):
                st.markdown('<div class="viewer-export-heading">Datenbasis</div>', unsafe_allow_html=True)
                ViewerControls.static_field("Modul", "KliWES 3.0 - Simulation")
                ViewerControls.static_field("Szenario", "kalib_beo_ERA5")

                st.markdown('<div class="viewer-export-heading">Raumauswahl</div>', unsafe_allow_html=True)
                spatial_filter = st.radio(
                    "Exportumfang",
                    (
                        f"Aktuelle Auswahl ({len(self._selection.groundwater_body_ids)} GWK)",
                        f"Nur Detail-GWK ({self._selection.selected_groundwater_body})",
                    ),
                    horizontal=True,
                    label_visibility="collapsed",
                    key="viewer_export_space",
                )
                export_data = self._filtered_data(
                    detail_only=spatial_filter.startswith("Nur Detail-GWK")
                )

                st.markdown('<div class="viewer-export-heading">Parameter und Auswertungen</div>', unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    include_gwn = st.checkbox("Grundwasserneubildung GWN (mm/a)", value=True)
                    include_comparison = st.checkbox("Periodenvergleich", value=True)
                with c2:
                    include_p = st.checkbox("Niederschlag P (mm/a)", value=False)
                    include_trends = st.checkbox("Trendanalyse", value=True)
                with c3:
                    include_etp = st.checkbox("Potenzielle Evapotranspiration ETp (mm/a)", value=False)

                st.markdown('<div class="viewer-export-heading">Paketformat</div>', unsafe_allow_html=True)
                export_format = st.radio(
                    "Paketformat",
                    ("Excel-Arbeitsmappe", "CSV-Dateien als ZIP"),
                    horizontal=True,
                    label_visibility="collapsed",
                )

                all_tables = self._context.export_service.dashboard_tables(export_data)
                selected_tables = {}
                if include_gwn:
                    selected_tables["GWN_Zeitreihen"] = all_tables["GWN_Zeitreihen"]
                if include_p:
                    selected_tables["Niederschlag"] = all_tables["Niederschlag"]
                if include_etp:
                    selected_tables["ETp"] = all_tables["ETp"]
                if include_comparison:
                    selected_tables["Vergleich"] = all_tables["Vergleich"]
                if include_trends:
                    selected_tables["Trend"] = all_tables["Trend"]

                if not selected_tables:
                    st.warning("Bitte mindestens einen Datensatz auswählen.")
                elif export_format == "Excel-Arbeitsmappe":
                    st.download_button(
                        "Ausgewähltes Datenpaket erstellen",
                        data=self._context.export_service.create_selected_excel(selected_tables),
                        file_name="gwn_export.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                else:
                    st.download_button(
                        "Ausgewähltes Datenpaket erstellen",
                        data=self._context.export_service.create_csv_zip(selected_tables),
                        file_name="gwn_export_csv.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )

                st.markdown('<div class="viewer-export-heading">Direktexport wie in der vorherigen Version</div>', unsafe_allow_html=True)
                number_of_gwk = export_data.comparison["GWK_ID"].nunique()
                d1, d2 = st.columns(2)
                with d1:
                    st.download_button(
                        "Vergleichstabelle herunterladen (CSV)",
                        data=self._context.export_service.create_csv(export_data.comparison),
                        file_name=f"gwn_vergleich_{number_of_gwk}_gwk.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                    st.download_button(
                        "Trendanalyse herunterladen (CSV)",
                        data=self._context.export_service.create_csv(export_data.trends),
                        file_name=f"gwn_trend_{number_of_gwk}_gwk.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with d2:
                    st.download_button(
                        "GWN-Zeitreihen herunterladen (CSV)",
                        data=self._context.export_service.create_csv(export_data.groundwater_recharge),
                        file_name=f"gwn_zeitreihen_{number_of_gwk}_gwk.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                    st.download_button(
                        "Alle Tabellen herunterladen (Excel)",
                        data=self._context.export_service.create_excel(export_data),
                        file_name=f"gwn_komplett_{number_of_gwk}_gwk.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

    def _filtered_data(self, *, detail_only: bool) -> DashboardData:
        if not detail_only:
            return self._data
        groundwater_body = self._selection.selected_groundwater_body

        def filter_frame(frame):
            if "GWK_ID" not in frame.columns:
                return frame.copy()
            return frame[frame["GWK_ID"] == groundwater_body].copy()

        return DashboardData(
            groundwater_recharge=filter_frame(self._data.groundwater_recharge),
            precipitation=filter_frame(self._data.precipitation),
            evapotranspiration=filter_frame(self._data.evapotranspiration),
            comparison=filter_frame(self._data.comparison),
            trends=filter_frame(self._data.trends),
        )
