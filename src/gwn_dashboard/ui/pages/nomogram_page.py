"""Nomogram-like relationship page based on the existing correlation analysis."""

import streamlit as st
from scipy.stats import linregress

from gwn_dashboard.application import AppContext
from gwn_dashboard.domain.models import DashboardData, SidebarSelection
from gwn_dashboard.ui.components.viewer_controls import ViewerControls


class NomogramPage:
    """Present the original GWN/precipitation correlation in viewer layout."""

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
        controls, chart = st.columns([1.0, 2.05], gap="small")
        with controls:
            with st.container(border=True):
                st.markdown('<div class="viewer-panel-heading">Basisnomogramm</div>', unsafe_allow_html=True)
                ViewerControls.static_field("Modell", ViewerControls.MODEL_LABEL)
                ViewerControls.static_field("Raum", self._selection.selected_groundwater_body)
                ViewerControls.static_field("Parameter", "Grundwasserneubildung GWN")
                ViewerControls.static_field("Bezugsgröße", "Niederschlag P")

                merged = self._merged_values()
                if len(merged) >= 2:
                    regression = linregress(merged["value"], merged["gwn_mm_a"])
                    st.markdown('<div class="viewer-panel-separator"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="viewer-panel-heading">Regression</div>', unsafe_allow_html=True)
                    st.markdown(
                        f"""
                        <div class="viewer-stat-row"><span>Steigung:</span><strong>{regression.slope:.4f}</strong></div>
                        <div class="viewer-stat-row"><span>R²:</span><strong>{regression.rvalue ** 2:.3f}</strong></div>
                        <div class="viewer-stat-row"><span>p-Wert:</span><strong>{regression.pvalue:.4f}</strong></div>
                        <div class="viewer-stat-row"><span>n:</span><strong>{len(merged)}</strong></div>
                        """,
                        unsafe_allow_html=True,
                    )
        with chart:
            figure = self._context.chart_factory.create_correlation(
                self._data,
                self._selection.selected_groundwater_body,
            )
            if figure is None:
                st.warning("Keine ausreichenden Daten für die Analyse vorhanden.")
            else:
                st.plotly_chart(
                    figure,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                st.info(
                    "R² beschreibt die Stärke des linearen Zusammenhangs. "
                    "Eine Korrelation ist kein Kausalitätsnachweis."
                )

    def _merged_values(self):
        groundwater_body = self._selection.selected_groundwater_body
        recharge = self._data.groundwater_recharge.query(
            "GWK_ID == @groundwater_body"
        )[["year", "gwn_mm_a"]]
        precipitation = self._data.precipitation.query(
            "GWK_ID == @groundwater_body"
        )[["year", "value"]]
        return recharge.merge(precipitation, on="year").dropna()
