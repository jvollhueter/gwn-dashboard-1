"""Groundwater-body time-series page."""

import streamlit as st

from gwn_dashboard.application import AppContext
from gwn_dashboard.config import DashboardConfig
from gwn_dashboard.domain.models import DashboardData, SidebarSelection
from gwn_dashboard.ui.pages.base_page import BasePage


class TimeSeriesPage(BasePage):
    """Render groundwater and meteorological annual time series.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    def __init__(self, config: DashboardConfig, context: AppContext, data: DashboardData, selection: SidebarSelection) -> None:
        self._config = config
        self._context = context
        self._data = data
        self._selection = selection

    @property
    def label(self) -> str:
        """Return the human-readable page label.
        
        Returns:
            str: Result produced by the operation.
        """
        return "📈 Zeitreihen"

    def render(self) -> None:
        """Render the component or page in Streamlit.
        """
        groundwater_body = self._selection.selected_groundwater_body
        st.header(f"Zeitreihenanalyse: {groundwater_body}")
        comparison = self._data.comparison.query("GWK_ID == @groundwater_body")
        trend = self._data.trends.query("GWK_ID == @groundwater_body")
        if not comparison.empty:
            row = comparison.iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(self._config.reference_period.label, f"{row['mean_ref']:.1f} mm/a")
            col2.metric(self._config.comparison_period.label, f"{row['mean_hist']:.1f} mm/a", delta=f"{row['delta_abs']:+.1f} mm/a")
            col3.metric("Änderung", f"{row['delta_rel_pct']:+.1f} %")
            if not trend.empty:
                trend_row = trend.iloc[0]
                col4.metric("Linearer Trend", f"{trend_row['lr_slope']:+.2f} mm/a je Jahr", delta=f"p={trend_row['lr_pvalue']:.3f}")
        figure = self._context.chart_factory.create_timeseries(
            self._data,
            groundwater_body,
            self._selection.show_precipitation,
            self._selection.show_evapotranspiration,
        )
        st.plotly_chart(figure, use_container_width=True)
        if not trend.empty:
            with st.expander("Detaillierte Trendstatistik"):
                st.dataframe(trend, use_container_width=True)
