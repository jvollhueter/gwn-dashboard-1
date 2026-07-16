"""Viewer-style data export page."""

import streamlit as st

from gwn_dashboard.application import AppContext
from gwn_dashboard.domain.models import DashboardData, SidebarSelection
from gwn_dashboard.ui.components.viewer_controls import ViewerControls


class ExportPage:
    """Render configurable data packages and direct data exports."""

    def __init__(
        self,
        context: AppContext,
        data: DashboardData,
        selection: SidebarSelection,
        minimum_year: int,
        maximum_year: int,
    ) -> None:
        self._context = context
        self._data = data
        self._selection = selection
        self._minimum_year = minimum_year
        self._maximum_year = maximum_year

    def render(self) -> None:
        """Render the component or page in Streamlit.
        """
        left, form, right = st.columns([0.55, 2.2, 0.75], gap="small")
        del left, right
        with form:
            with st.container(border=True):
                st.markdown(
                    '<div class="viewer-export-heading">Datenbasis</div>',
                    unsafe_allow_html=True,
                )
                ViewerControls.static_field(
                    "Modul",
                    "KliWES 3.0 - Simulation",
                )
                ViewerControls.static_field("Szenario", "kalib_beo_ERA5")
                st.markdown(
                    '<div class="viewer-export-heading">Zeitraumauswahl</div>',
                    unsafe_allow_html=True,
                )
                self._render_period_controls()

                st.markdown(
                    '<div class="viewer-export-heading">Raumauswahl</div>',
                    unsafe_allow_html=True,
                )
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

                st.markdown(
                    '<div class="viewer-export-heading">Parameter und Auswertungen</div>',
                    unsafe_allow_html=True,
                )
                c1, c2, c3 = st.columns(3)
                with c1:
                    include_gwn = st.checkbox(
                        "Grundwasserneubildung GWN (mm/a)",
                        value=True,
                    )
                    include_comparison = st.checkbox(
                        "Periodenvergleich",
                        value=True,
                    )
                with c2:
                    include_p = st.checkbox("Niederschlag P (mm/a)", value=False)
                    include_trends = st.checkbox("Trendanalyse", value=True)
                with c3:
                    include_etp = st.checkbox(
                        "Potenzielle Evapotranspiration ETp (mm/a)",
                        value=False,
                    )

                st.markdown(
                    '<div class="viewer-export-heading">Paketformat</div>',
                    unsafe_allow_html=True,
                )
                export_format = st.radio(
                    "Paketformat",
                    ("Excel-Arbeitsmappe", "CSV-Dateien als ZIP"),
                    horizontal=True,
                    label_visibility="collapsed",
                )

                all_tables = self._context.export_service.dashboard_tables(
                    export_data
                )
                selected_tables = {}
                if include_gwn:
                    selected_tables["GWN_Zeitreihen"] = all_tables[
                        "GWN_Zeitreihen"
                    ]
                if include_p:
                    selected_tables["Niederschlag"] = all_tables["Niederschlag"]
                if include_etp:
                    selected_tables["ETp"] = all_tables["ETp"]
                if include_comparison:
                    selected_tables["Vergleich"] = all_tables["Vergleich"]
                if include_trends:
                    selected_tables["Trend"] = all_tables["Trend"]

                period_token = self._period_token()
                if not selected_tables:
                    st.warning("Bitte mindestens einen Datensatz auswählen.")
                elif export_format == "Excel-Arbeitsmappe":
                    st.download_button(
                        "Ausgewähltes Datenpaket erstellen",
                        data=self._context.export_service.create_selected_excel(
                            selected_tables
                        ),
                        file_name=f"gwn_export_{period_token}.xlsx",
                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "spreadsheetml.sheet"
                        ),
                        use_container_width=True,
                    )
                else:
                    st.download_button(
                        "Ausgewähltes Datenpaket erstellen",
                        data=self._context.export_service.create_csv_zip(
                            selected_tables
                        ),
                        file_name=f"gwn_export_{period_token}_csv.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )

                st.markdown(
                    '<div class="viewer-export-heading">Direktexport</div>',
                    unsafe_allow_html=True,
                )
                number_of_gwk = export_data.comparison["GWK_ID"].nunique()
                d1, d2 = st.columns(2)
                with d1:
                    st.download_button(
                        "Vergleichstabelle herunterladen (CSV)",
                        data=self._context.export_service.create_csv(
                            export_data.comparison
                        ),
                        file_name=(
                            f"gwn_vergleich_{period_token}_{number_of_gwk}_gwk.csv"
                        ),
                        mime="text/csv",
                        use_container_width=True,
                    )
                    st.download_button(
                        "Trendanalyse herunterladen (CSV)",
                        data=self._context.export_service.create_csv(
                            export_data.trends
                        ),
                        file_name=f"gwn_trend_{number_of_gwk}_gwk.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with d2:
                    st.download_button(
                        "GWN-Zeitreihen herunterladen (CSV)",
                        data=self._context.export_service.create_csv(
                            export_data.groundwater_recharge
                        ),
                        file_name=f"gwn_zeitreihen_{number_of_gwk}_gwk.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                    st.download_button(
                        "Alle Tabellen herunterladen (Excel)",
                        data=self._context.export_service.create_excel(export_data),
                        file_name=(
                            f"gwn_komplett_{period_token}_{number_of_gwk}_gwk.xlsx"
                        ),
                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "spreadsheetml.sheet"
                        ),
                        use_container_width=True,
                    )

    def _render_period_controls(self) -> None:
        """Render export-specific sliders and commit valid ranges immediately."""

        active_reference = (
            self._selection.reference_period.start_year,
            self._selection.reference_period.end_year,
        )
        active_comparison = (
            self._selection.comparison_period.start_year,
            self._selection.comparison_period.end_year,
        )
        active_source = (active_reference, active_comparison)

        if st.session_state.get("viewer_export_period_source") != active_source:
            st.session_state["viewer_export_reference_period"] = active_reference
            st.session_state["viewer_export_comparison_period"] = active_comparison
            st.session_state["viewer_export_period_source"] = active_source
            st.session_state.pop("viewer_export_period_error", None)

        reference_column, comparison_column = st.columns(2, gap="small")
        with reference_column:
            reference_range = st.slider(
                "Referenzzeitraum",
                min_value=self._minimum_year,
                max_value=self._maximum_year,
                step=1,
                key="viewer_export_reference_period",
                on_change=self._commit_export_periods,
            )
            st.caption(
                f"{reference_range[0]}–{reference_range[1]} "
                f"({reference_range[1] - reference_range[0] + 1} Jahre)"
            )
        with comparison_column:
            comparison_range = st.slider(
                "Vergleichszeitraum",
                min_value=self._minimum_year,
                max_value=self._maximum_year,
                step=1,
                key="viewer_export_comparison_period",
                on_change=self._commit_export_periods,
            )
            st.caption(
                f"{comparison_range[0]}–{comparison_range[1]} "
                f"({comparison_range[1] - comparison_range[0] + 1} Jahre)"
            )

        period_error = st.session_state.get("viewer_export_period_error")
        if period_error:
            st.error(
                f"{period_error} Bis zu einer gültigen Auswahl verwenden die "
                f"Exporte weiterhin {self._selection.reference_period.label} / "
                f"{self._selection.comparison_period.label}."
            )

    def _commit_export_periods(self) -> None:
        """Apply valid export period inputs to the shared viewer selection."""

        reference_range = tuple(
            int(value)
            for value in st.session_state["viewer_export_reference_period"]
        )
        comparison_range = tuple(
            int(value)
            for value in st.session_state["viewer_export_comparison_period"]
        )
        reference_period, comparison_period = ViewerControls._periods_from_ranges(
            reference_range,
            comparison_range,
        )
        try:
            ViewerControls._validate_selected_periods(
                reference_period,
                comparison_period,
                stop_on_error=False,
            )
        except ValueError as error:
            st.session_state["viewer_export_period_error"] = str(error)
            return

        st.session_state["viewer_reference_period"] = reference_range
        st.session_state["viewer_comparison_period"] = comparison_range
        st.session_state["viewer_export_period_source"] = (
            reference_range,
            comparison_range,
        )
        st.session_state.pop("viewer_export_period_error", None)

    def _period_token(self) -> str:
        reference = self._selection.reference_period
        comparison = self._selection.comparison_period
        return (
            f"{reference.start_year}-{reference.end_year}_"
            f"{comparison.start_year}-{comparison.end_year}"
        )

    def _filtered_data(self, *, detail_only: bool) -> DashboardData:
        if not detail_only:
            return self._data
        groundwater_body = self._selection.selected_groundwater_body

        def filter_frame(frame):
            """Provide the filter frame operation.
            
            Args:
                frame: Input value used by the operation.
            
            Raises:
                ValueError: If required input data or metadata are invalid.
            """
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
