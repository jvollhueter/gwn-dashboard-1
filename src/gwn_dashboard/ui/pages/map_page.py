"""Viewer-style spatial analysis page."""

from collections.abc import Callable

import geopandas as gpd
import pandas as pd
import streamlit as st

from gwn_dashboard.application import AppContext
from gwn_dashboard.config import DashboardConfig
from gwn_dashboard.domain.models import DashboardData, SidebarSelection


class MapPage:
    """Render map controls, interactive map and the original summary charts."""

    _PARAMETERS = {
        "Änderung GWN [mm/a]": ("delta_abs", "Änderung der GWN [mm/a]"),
        "Änderung GWN [%]": ("delta_rel_pct", "Änderung der GWN [%]"),
        "GWN Vergleichsperiode": ("mean_hist", "GWN Vergleichsperiode [mm/a]"),
        "GWN Referenzperiode": ("mean_ref", "GWN Referenzperiode [mm/a]"),
    }

    def __init__(
        self,
        config: DashboardConfig,
        context: AppContext,
        data: DashboardData,
        selection: SidebarSelection,
        geometry_loader: Callable[[], gpd.GeoDataFrame],
    ) -> None:
        self._config = config
        self._context = context
        self._data = data
        self._selection = selection
        self._geometry_loader = geometry_loader

    def render(self) -> None:
        left, center, right = st.columns([1.28, 5.5, 1.45], gap="small")
        with left:
            with st.container(border=True):
                st.markdown('<div class="viewer-tree-heading">Wasserhaushalt</div>', unsafe_allow_html=True)
                parameter_label = st.radio(
                    "Parameter",
                    options=tuple(self._PARAMETERS),
                    index=0,
                    key="viewer_map_parameter",
                    label_visibility="collapsed",
                )
                st.markdown('<div class="viewer-side-note">Ausgewählter Grundwasserkörper</div>', unsafe_allow_html=True)
                st.code(self._selection.selected_groundwater_body, language=None)
                st.markdown('<div class="viewer-side-note">Vergleichszeiträume</div>', unsafe_allow_html=True)
                st.caption(f"{self._config.reference_period.label} / {self._config.comparison_period.label}")

        value_column, title = self._PARAMETERS[parameter_label]
        try:
            geometries = self._geometry_loader()
        except Exception as error:
            center.error(f"Geometrien konnten nicht geladen werden: {error}")
            return

        with center:
            figure = self._context.map_factory.create_choropleth(
                geometries,
                self._data.comparison,
                self._selection.selected_groundwater_body,
                value_column=value_column,
                title=title,
            )
            if figure is None:
                st.warning("Keine Geometrien verfügbar.")
            else:
                # The Plotly mode bar is a real, working map toolbar. The previous
                # decorative pseudo-toolbar has deliberately been removed.
                st.plotly_chart(
                    figure,
                    use_container_width=True,
                    config={
                        "displayModeBar": True,
                        "displaylogo": False,
                        "scrollZoom": True,
                        "responsive": True,
                    },
                )

        with right:
            with st.container(border=True):
                st.markdown('<div class="viewer-panel-heading">Auswahlstatistik</div>', unsafe_allow_html=True)
                values = self._data.comparison[value_column].dropna()
                self._stat_row("Mittelwert", values.mean(), self._unit(value_column))
                self._stat_row("Median", values.median(), self._unit(value_column))
                self._stat_row("Minimum", values.min(), self._unit(value_column))
                self._stat_row("Maximum", values.max(), self._unit(value_column))
                self._stat_row("St.abw.", values.std(), self._unit(value_column))
                st.markdown('<div class="viewer-panel-separator"></div>', unsafe_allow_html=True)
                st.plotly_chart(
                    self._context.chart_factory.create_value_histogram(
                        self._data.comparison,
                        value_column,
                        title,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

        with st.expander("Weitere Auswertungen", expanded=False):
            histogram, boxplot = st.columns(2, gap="small")
            with histogram:
                st.plotly_chart(
                    self._context.chart_factory.create_change_histogram(
                        self._data.comparison
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            with boxplot:
                st.plotly_chart(
                    self._context.chart_factory.create_period_boxplot(
                        self._data.comparison
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

    @staticmethod
    def _unit(value_column: str) -> str:
        return "%" if value_column == "delta_rel_pct" else "mm/a"

    @staticmethod
    def _stat_row(label: str, value: float, unit: str) -> None:
        if pd.isna(value):
            formatted = "–"
        else:
            formatted = f"{value:.2f} {unit}"
        st.markdown(
            f'<div class="viewer-stat-row"><span>{label}:</span><strong>{formatted}</strong></div>',
            unsafe_allow_html=True,
        )
