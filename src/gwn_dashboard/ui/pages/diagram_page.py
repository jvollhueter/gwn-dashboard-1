"""Viewer-style diagrams and statistics module."""

import streamlit as st

from gwn_dashboard.application import AppContext
from gwn_dashboard.config import DashboardConfig
from gwn_dashboard.domain.models import DashboardData, SidebarSelection
from gwn_dashboard.ui.components.viewer_controls import ViewerControls


class DiagramPage:
    """Render time series, period comparison and statistics in viewer layout."""

    def __init__(
        self,
        config: DashboardConfig,
        context: AppContext,
        data: DashboardData,
        selection: SidebarSelection,
    ) -> None:
        self._config = config
        self._context = context
        self._data = data
        self._selection = selection

    def render(self) -> None:
        """Render the component or page in Streamlit.
        """
        selector, spacer = st.columns([0.28, 1.72], gap="small")
        del spacer
        with selector:
            diagram_type = st.selectbox(
                "Diagrammtyp",
                ("Zeitreihen", "Periodenvergleich", "Statistiken"),
                key="viewer_diagram_type",
            )

        if diagram_type == "Zeitreihen":
            self._render_timeseries()
        elif diagram_type == "Periodenvergleich":
            self._render_comparison()
        else:
            self._render_statistics()

    def _render_timeseries(self) -> None:
        groundwater_body = self._selection.selected_groundwater_body
        controls, chart = st.columns([1.0, 2.05], gap="small")
        with controls:
            with st.container(border=True):
                show_precipitation, show_etp = ViewerControls(
                    self._config.reference_period,
                    self._config.comparison_period,
                ).render_diagram_controls(self._selection)
        with chart:
            comparison = self._data.comparison.query(
                "GWK_ID == @groundwater_body"
            )
            trend = self._data.trends.query("GWK_ID == @groundwater_body")
            if not comparison.empty:
                row = comparison.iloc[0]
                col1, col2, col3, col4 = st.columns(4, gap="small")
                col1.metric(
                    self._selection.reference_period.label,
                    f"{row['mean_ref']:.1f} mm/a",
                )
                col2.metric(
                    self._selection.comparison_period.label,
                    f"{row['mean_hist']:.1f} mm/a",
                    delta=f"{row['delta_abs']:+.1f} mm/a",
                )
                col3.metric("Änderung", f"{row['delta_rel_pct']:+.1f} %")
                if not trend.empty:
                    trend_row = trend.iloc[0]
                    col4.metric(
                        "Linearer Trend",
                        f"{trend_row['lr_slope']:+.2f} mm/a je Jahr",
                        delta=f"p={trend_row['lr_pvalue']:.3f}",
                        delta_color="off",
                    )

            figure = self._context.chart_factory.create_timeseries(
                self._data,
                groundwater_body,
                show_precipitation,
                show_etp,
                reference_period=self._selection.reference_period,
                comparison_period=self._selection.comparison_period,
            )
            st.plotly_chart(
                figure,
                use_container_width=True,
                config={"displayModeBar": False},
            )
            if not trend.empty:
                with st.expander("Detaillierte Trendstatistik"):
                    st.dataframe(trend, use_container_width=True)

    def _render_comparison(self) -> None:
        controls, chart = st.columns([1.0, 2.05], gap="small")
        with controls:
            with st.container(border=True):
                st.markdown(
                    '<div class="viewer-panel-heading">Darstellung</div>',
                    unsafe_allow_html=True,
                )
                sort_label = st.selectbox(
                    "Sortieren nach",
                    (
                        "Grundwasserkörper",
                        "Absolute Änderung",
                        "Relative Änderung",
                        f"Mittel {self._selection.reference_period.label}",
                        f"Mittel {self._selection.comparison_period.label}",
                    ),
                    key="viewer_comparison_sort",
                )
                ascending = st.checkbox("Aufsteigend sortieren", value=True)
                only_decrease = st.checkbox("Nur GWK mit Rückgang", value=False)
                mapping = {
                    "Grundwasserkörper": "GWK_ID",
                    "Absolute Änderung": "delta_abs",
                    "Relative Änderung": "delta_rel_pct",
                    f"Mittel {self._selection.reference_period.label}": "mean_ref",
                    f"Mittel {self._selection.comparison_period.label}": "mean_hist",
                }
                table = self._data.comparison.copy()
                if only_decrease:
                    table = table[table["delta_abs"] < 0]
                table = table.sort_values(mapping[sort_label], ascending=ascending)
                st.markdown(
                    '<div class="viewer-panel-separator"></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="viewer-stat-row"><span>Datensätze:</span>'
                    f"<strong>{len(table)}</strong></div>",
                    unsafe_allow_html=True,
                )
        with chart:
            st.plotly_chart(
                self._context.chart_factory.create_period_comparison(
                    table,
                    reference_period=self._selection.reference_period,
                    comparison_period=self._selection.comparison_period,
                ),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            st.dataframe(
                table.rename(
                    columns={
                        "GWK_ID": "Grundwasserkörper",
                        "mean_ref": (
                            f"GWN {self._selection.reference_period.label} [mm/a]"
                        ),
                        "mean_hist": (
                            f"GWN {self._selection.comparison_period.label} [mm/a]"
                        ),
                        "delta_abs": "Änderung [mm/a]",
                        "delta_rel_pct": "Änderung [%]",
                    }
                ),
                use_container_width=True,
                height=290,
            )

    def _render_statistics(self) -> None:
        controls, results = st.columns([1.0, 2.05], gap="small")
        with controls:
            with st.container(border=True):
                st.markdown(
                    '<div class="viewer-panel-heading">Filter</div>',
                    unsafe_allow_html=True,
                )
                significant_only = st.checkbox(
                    "Nur lineare Trends mit p < 0,05",
                    value=False,
                    key="viewer_statistics_significant",
                )
                selected_only = st.checkbox(
                    "Nur Detail-GWK",
                    value=False,
                    key="viewer_statistics_detail",
                )
                st.markdown(
                    '<div class="viewer-panel-separator"></div>',
                    unsafe_allow_html=True,
                )
                ViewerControls.static_field(
                    "Referenz",
                    self._selection.reference_period.label,
                )
                ViewerControls.static_field(
                    "Vergleich",
                    self._selection.comparison_period.label,
                )
        trends = self._data.trends.copy()
        comparison = self._data.comparison.copy()
        if significant_only:
            trends = trends[trends["lr_pvalue"] < 0.05]
        if selected_only:
            groundwater_body = self._selection.selected_groundwater_body
            trends = trends[trends["GWK_ID"] == groundwater_body]
            comparison = comparison[comparison["GWK_ID"] == groundwater_body]
        with results:
            with st.container(border=True):
                st.markdown(
                    '<div class="viewer-panel-heading">Trendanalyse</div>',
                    unsafe_allow_html=True,
                )
                st.dataframe(trends, use_container_width=True, height=310)
                st.markdown(
                    '<div class="viewer-panel-separator"></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="viewer-panel-heading">Periodenvergleich</div>',
                    unsafe_allow_html=True,
                )
                displayed_comparison = comparison.rename(
                    columns={
                        "mean_ref": (
                            f"mean_{self._selection.reference_period.start_year}_"
                            f"{self._selection.reference_period.end_year}"
                        ),
                        "mean_hist": (
                            f"mean_{self._selection.comparison_period.start_year}_"
                            f"{self._selection.comparison_period.end_year}"
                        ),
                    }
                )
                st.dataframe(
                    displayed_comparison,
                    use_container_width=True,
                    height=310,
                )
