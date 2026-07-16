"""Map visualization factory."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from gwn_dashboard.design.plotly_theme import apply_map_layout
from gwn_dashboard.design.theme import CHANGE_SCALE, COLORS, GROUNDWATER_SCALE
from gwn_dashboard.domain.models import Period


class MapFactory:
    """Create interactive maps without Streamlit dependencies."""

    def create_choropleth(
        self,
        geometries: gpd.GeoDataFrame,
        comparison: pd.DataFrame,
        selected_groundwater_body: str | None = None,
        *,
        value_column: str = "delta_abs",
        title: str = "Änderung der Grundwasserneubildung",
        reference_period: Period | None = None,
        comparison_period: Period | None = None,
        monitoring_stations: gpd.GeoDataFrame | None = None,
        station_marker_size: int = 5,
    ) -> go.Figure | None:
        """Create a groundwater-body choropleth with optional monitoring stations.
        
        Args:
            geometries: Value of type ``gpd.GeoDataFrame``.
            comparison: Value of type ``pd.DataFrame``.
            selected_groundwater_body: Value of type ``str | None``.
            value_column: Value of type ``str``.
            title: Value of type ``str``.
            reference_period: Value of type ``Period | None``.
            comparison_period: Value of type ``Period | None``.
            monitoring_stations: Value of type ``gpd.GeoDataFrame | None``.
            station_marker_size: Value of type ``int``.
        
        Returns:
            go.Figure | None: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        if geometries is None or geometries.empty:
            return None
        if value_column not in comparison.columns:
            raise ValueError(f"Unbekannte Kartenspalte: {value_column}")

        merged = geometries.merge(comparison, on="GWK_ID", how="left").reset_index(
            drop=True
        )
        centroid = merged.geometry.unary_union.centroid
        is_change = value_column in {"delta_abs", "delta_rel_pct"}
        values = merged[value_column].dropna()
        if is_change:
            maximum = float(values.abs().quantile(0.98)) if not values.empty else 1.0
            maximum = maximum if maximum > 0 else 1.0
            scale = CHANGE_SCALE
            range_color = (-maximum, maximum)
            midpoint = 0
        else:
            scale = GROUNDWATER_SCALE
            range_color = None
            midpoint = None

        reference_label = (
            reference_period.label if reference_period is not None else "Referenz"
        )
        comparison_label = (
            comparison_period.label if comparison_period is not None else "Vergleich"
        )
        labels = {
            value_column: title,
            "mean_ref": f"GWN {reference_label} [mm/a]",
            "mean_hist": f"GWN {comparison_label} [mm/a]",
            "delta_abs": "Änderung [mm/a]",
            "delta_rel_pct": "Änderung [%]",
        }

        figure = px.choropleth_mapbox(
            merged,
            geojson=merged.geometry.__geo_interface__,
            locations=merged.index,
            color=value_column,
            hover_name="GWK_ID",
            hover_data={
                "mean_ref": ":.1f",
                "mean_hist": ":.1f",
                "delta_abs": ":+.1f",
                "delta_rel_pct": ":+.1f",
            },
            color_continuous_scale=scale,
            color_continuous_midpoint=midpoint,
            range_color=range_color,
            mapbox_style="carto-positron",
            zoom=7,
            center={"lat": centroid.y, "lon": centroid.x},
            opacity=0.82,
            labels=labels,
        )

        if selected_groundwater_body:
            selected = merged[merged["GWK_ID"] == selected_groundwater_body]
            if not selected.empty:
                outline = px.choropleth_mapbox(
                    selected,
                    geojson=selected.geometry.__geo_interface__,
                    locations=selected.index,
                    mapbox_style="carto-positron",
                    opacity=0,
                )
                trace = outline.data[0]
                trace.marker.line.width = 4
                trace.marker.line.color = COLORS.brand_primary_dark
                trace.showscale = False
                figure.add_trace(trace)

        self._add_monitoring_station_trace(
            figure,
            monitoring_stations,
            marker_size=station_marker_size,
        )

        return apply_map_layout(
            figure,
            title=title,
            height=720,
        )

    @staticmethod
    def _add_monitoring_station_trace(
        figure: go.Figure,
        monitoring_stations: gpd.GeoDataFrame | None,
        *,
        marker_size: int,
    ) -> None:
        if monitoring_stations is None or monitoring_stations.empty:
            return

        required = {
            "station_id",
            "station_name",
            "first_measurement",
            "last_measurement",
            "GWK_ID",
            "geometry",
        }
        missing = required - set(monitoring_stations.columns)
        if missing:
            raise ValueError(
                "Messstellendaten: fehlende Spalten "
                f"{sorted(missing)}"
            )

        stations = monitoring_stations.dropna(subset=["geometry"]).copy()
        if stations.empty:
            return
        if stations.crs is not None and stations.crs.to_epsg() != 4326:
            stations = stations.to_crs(epsg=4326)

        custom_data = stations[
            [
                "station_id",
                "station_name",
                "first_measurement",
                "last_measurement",
                "GWK_ID",
            ]
        ].astype(str).to_numpy()
        figure.add_trace(
            go.Scattermapbox(
                lon=stations.geometry.x,
                lat=stations.geometry.y,
                mode="markers",
                marker={
                    "size": marker_size,
                    "color": "#000000",
                    "opacity": 0.72,
                },
                customdata=custom_data,
                hovertemplate=(
                    "<b>%{customdata[1]}</b><br>"
                    "MKZ: %{customdata[0]}<br>"
                    "Messzeitraum: %{customdata[2]}–%{customdata[3]}<br>"
                    "GWK 2025: %{customdata[4]}"
                    "<extra></extra>"
                ),
                name="Grundwassermessstellen",
                showlegend=False,
            )
        )

