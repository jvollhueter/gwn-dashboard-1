"""Viewer-style spatial analysis page."""

from collections.abc import Callable, Sequence

import geopandas as gpd
import pandas as pd
import streamlit as st

from gwn_dashboard.application import AppContext
from gwn_dashboard.config import DashboardConfig
from gwn_dashboard.domain.models import DashboardData, SidebarSelection


class MapPage:
    """Render map controls, interactive map and summary charts."""

    STATION_MODES = (
        "Keine",
        "Alle",
        "Einzelne Auswahl",
        "Messstellen eines GWK",
    )

    def __init__(
        self,
        config: DashboardConfig,
        context: AppContext,
        data: DashboardData,
        selection: SidebarSelection,
        geometry_loader: Callable[[], gpd.GeoDataFrame],
        station_loader: Callable[[], gpd.GeoDataFrame],
        available_groundwater_bodies: Sequence[str],
    ) -> None:
        self._config = config
        self._context = context
        self._data = data
        self._selection = selection
        self._geometry_loader = geometry_loader
        self._station_loader = station_loader
        self._available_groundwater_bodies = tuple(
            str(value) for value in available_groundwater_bodies
        )

    def render(self) -> None:
        """Render the component or page in Streamlit.
        """
        parameters = self._parameters()
        left, center, right = st.columns([1.28, 5.5, 1.45], gap="small")
        with left:
            with st.container(border=True):
                st.markdown(
                    '<div class="viewer-tree-heading">Wasserhaushalt</div>',
                    unsafe_allow_html=True,
                )
                parameter_label = st.radio(
                    "Parameter",
                    options=tuple(parameters),
                    index=0,
                    key="viewer_map_parameter",
                    label_visibility="collapsed",
                )
                st.markdown(
                    '<div class="viewer-side-note">Ausgewählter Grundwasserkörper</div>',
                    unsafe_allow_html=True,
                )
                st.code(
                    self._selection.selected_groundwater_body,
                    language=None,
                )
                monitoring_stations, station_marker_size = (
                    self._render_monitoring_station_controls()
                )

        value_column, title = parameters[parameter_label]
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
                reference_period=self._selection.reference_period,
                comparison_period=self._selection.comparison_period,
                monitoring_stations=monitoring_stations,
                station_marker_size=station_marker_size,
            )
            if figure is None:
                st.warning("Keine Geometrien verfügbar.")
            else:
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
                st.markdown(
                    '<div class="viewer-panel-heading">Auswahlstatistik</div>',
                    unsafe_allow_html=True,
                )
                values = self._data.comparison[value_column].dropna()
                self._stat_row(
                    "Mittelwert",
                    values.mean(),
                    self._unit(value_column),
                )
                self._stat_row(
                    "Median",
                    values.median(),
                    self._unit(value_column),
                )
                self._stat_row(
                    "Minimum",
                    values.min(),
                    self._unit(value_column),
                )
                self._stat_row(
                    "Maximum",
                    values.max(),
                    self._unit(value_column),
                )
                self._stat_row(
                    "St.abw.",
                    values.std(),
                    self._unit(value_column),
                )
                st.markdown(
                    '<div class="viewer-panel-separator"></div>',
                    unsafe_allow_html=True,
                )
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
                        self._data.comparison,
                        reference_period=self._selection.reference_period,
                        comparison_period=self._selection.comparison_period,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

    def _render_monitoring_station_controls(
        self,
    ) -> tuple[gpd.GeoDataFrame | None, int]:
        st.markdown(
            '<div class="viewer-panel-separator"></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="viewer-tree-heading">Messstellen</div>',
            unsafe_allow_html=True,
        )
        station_mode = st.radio(
            "Messstellen anzeigen",
            options=self.STATION_MODES,
            index=self._station_mode_index(),
            key="viewer_station_mode",
        )
        if station_mode == "Keine":
            return None, 5

        try:
            stations = self._station_loader()
        except Exception as error:
            st.warning(f"Messstellen konnten nicht geladen werden: {error}")
            return None, 5

        if station_mode == "Alle":
            st.caption(self._station_count_text(len(stations)))
            return stations, 5

        if station_mode == "Messstellen eines GWK":
            selected_gwk = self._render_station_gwk_selector()
            selected = stations[
                stations["GWK_ID"].astype("string").str.strip() == selected_gwk
            ].copy()
            if selected.empty:
                st.caption("Keine Messstellen sind diesem GWK zugeordnet.")
            else:
                st.caption(self._station_count_text(len(selected)))
            return selected, 5

        station_ids = stations["station_id"].astype(str).tolist()
        labels = dict(
            zip(
                stations["station_id"].astype(str),
                stations["station_label"].astype(str),
                strict=True,
            )
        )
        previous = [
            station_id
            for station_id in st.session_state.get(
                "viewer_selected_station_ids",
                [],
            )
            if station_id in labels
        ]
        selected_ids = st.multiselect(
            "Messstellen auswählen",
            options=station_ids,
            default=previous,
            format_func=lambda station_id: labels.get(station_id, station_id),
            key="viewer_selected_station_ids",
            placeholder="Messstellenname oder MKZ eingeben …",
        )
        selected = stations[
            stations["station_id"].astype(str).isin(selected_ids)
        ].copy()
        if selected.empty:
            st.caption("Keine einzelne Messstelle ausgewählt.")
        else:
            st.caption(self._station_count_text(len(selected)))
        return selected, 8

    def _render_station_gwk_selector(self) -> str:
        available = list(self._available_groundwater_bodies)
        if not available:
            st.error("Keine Grundwasserkörper für die Messstellenauswahl verfügbar.")
            st.stop()

        current = st.session_state.get("viewer_station_gwk")
        if current not in available:
            current = self._selection.selected_groundwater_body
        if current not in available:
            current = available[0]
        st.session_state["viewer_station_gwk"] = current

        return st.selectbox(
            "GWK auswählen",
            options=available,
            index=available.index(current),
            key="viewer_station_gwk",
        )

    @staticmethod
    def _station_count_text(count: int) -> str:
        formatted = f"{count:,}".replace(",", ".")
        noun = "Messstelle" if count == 1 else "Messstellen"
        verb = "wird" if count == 1 else "werden"
        return f"{formatted} {noun} {verb} angezeigt."

    @classmethod
    def _station_mode_index(cls) -> int:
        current = st.session_state.get("viewer_station_mode", "Keine")
        return cls.STATION_MODES.index(current) if current in cls.STATION_MODES else 0

    def _parameters(self) -> dict[str, tuple[str, str]]:
        reference = self._selection.reference_period.label
        comparison = self._selection.comparison_period.label
        return {
            "Änderung GWN [mm/a]": (
                "delta_abs",
                f"Änderung der GWN {reference} zu {comparison} [mm/a]",
            ),
            "Änderung GWN [%]": (
                "delta_rel_pct",
                f"Änderung der GWN {reference} zu {comparison} [%]",
            ),
            f"GWN {comparison}": (
                "mean_hist",
                f"Mittlere GWN {comparison} [mm/a]",
            ),
            f"GWN {reference}": (
                "mean_ref",
                f"Mittlere GWN {reference} [mm/a]",
            ),
        }

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
            f'<div class="viewer-stat-row"><span>{label}:</span>'
            f"<strong>{formatted}</strong></div>",
            unsafe_allow_html=True,
        )
