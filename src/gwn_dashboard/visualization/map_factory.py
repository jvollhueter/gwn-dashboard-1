"""Map visualization factory."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from gwn_dashboard.design.plotly_theme import apply_map_layout
from gwn_dashboard.design.theme import CHANGE_SCALE, COLORS, GROUNDWATER_SCALE


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
    ) -> go.Figure | None:
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
            labels={value_column: title},
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

        return apply_map_layout(
            figure,
            title=title,
            height=720,
        )
