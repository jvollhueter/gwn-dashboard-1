"""Summary metric panel."""

import streamlit as st

from gwn_dashboard.config import DashboardConfig
from gwn_dashboard.domain.models import DashboardData, SidebarSelection


class MetricPanel:
    def __init__(self, config: DashboardConfig) -> None:
        self._config = config

    def render(self, data: DashboardData, selection: SidebarSelection) -> None:
        st.subheader(f"📊 Übersicht: {len(selection.groundwater_body_ids)} ausgewählte GWK")
        col1, col2, col3, col4 = st.columns(4)
        comparison = data.comparison
        col1.metric(
            f"⌀ GWN {self._config.reference_period.label}",
            f"{comparison['mean_ref'].mean():.1f} mm/a",
        )
        col2.metric(
            f"⌀ GWN {self._config.comparison_period.label}",
            f"{comparison['mean_hist'].mean():.1f} mm/a",
        )
        col3.metric("⌀ Änderung", f"{comparison['delta_abs'].mean():+.1f} mm/a")
        decreasing = int((comparison["delta_abs"] < 0).sum())
        col4.metric("GWK mit Rückgang", f"{decreasing} / {len(comparison)}")
        st.markdown("---")
