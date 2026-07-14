"""Download controls."""

import streamlit as st

from gwn_dashboard.domain.models import DashboardData
from gwn_dashboard.services.export_service import ExportService


class ExportPanel:
    def __init__(self, export_service: ExportService) -> None:
        self._export_service = export_service

    def render(self, data: DashboardData, number_of_groundwater_bodies: int) -> None:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📥 Daten-Export")
        st.sidebar.download_button(
            "Vergleichstabelle (CSV)",
            data=self._export_service.create_csv(data.comparison),
            file_name=f"gwn_vergleich_{number_of_groundwater_bodies}_gwk.csv",
            mime="text/csv",
        )
        st.sidebar.download_button(
            "Trendanalyse (CSV)",
            data=self._export_service.create_csv(data.trends),
            file_name=f"gwn_trend_{number_of_groundwater_bodies}_gwk.csv",
            mime="text/csv",
        )
        st.sidebar.download_button(
            "GWN-Zeitreihen (CSV)",
            data=self._export_service.create_csv(data.groundwater_recharge),
            file_name=f"gwn_zeitreihen_{number_of_groundwater_bodies}_gwk.csv",
            mime="text/csv",
        )
        st.sidebar.download_button(
            "Alle Tabellen (Excel)",
            data=self._export_service.create_excel(data),
            file_name=f"gwn_komplett_{number_of_groundwater_bodies}_gwk.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
