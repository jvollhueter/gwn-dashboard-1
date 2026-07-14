"""Map visualization factory."""

import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class MapFactory:
    """Create interactive maps without Streamlit dependencies."""

    def create_choropleth(
        self,
        geometries: gpd.GeoDataFrame,
        comparison: pd.DataFrame,
        selected_groundwater_body: str | None = None,
    ) -> go.Figure | None:
        if geometries is None or geometries.empty:
            return None

        merged = geometries.merge(comparison, on="GWK_ID", how="left").reset_index(drop=True)
        centroid = merged.geometry.unary_union.centroid
        figure = px.choropleth_mapbox(
            merged,
            geojson=merged.geometry.__geo_interface__,
            locations=merged.index,
            color="delta_abs",
            hover_name="GWK_ID",
            hover_data={
                "mean_ref": ":.1f",
                "mean_hist": ":.1f",
                "delta_abs": ":+.1f",
                "delta_rel_pct": ":+.1f",
            },
            color_continuous_scale="RdYlGn",
            range_color=(-50, 50),
            mapbox_style="open-street-map",
            zoom=7,
            center={"lat": centroid.y, "lon": centroid.x},
            opacity=0.7,
            labels={"delta_abs": "Änderung [mm/a]"},
        )

        if selected_groundwater_body:
            selected = merged[merged["GWK_ID"] == selected_groundwater_body]
            if not selected.empty:
                outline = px.choropleth_mapbox(
                    selected,
                    geojson=selected.geometry.__geo_interface__,
                    locations=selected.index,
                    mapbox_style="open-street-map",
                    opacity=0,
                )
                trace = outline.data[0]
                trace.marker.line.width = 4
                trace.marker.line.color = "yellow"
                trace.showscale = False
                figure.add_trace(trace)

        figure.update_layout(
            title="<b>GWK-Karte: Änderung der Grundwasserneubildung</b>",
            height=650,
            margin={"r": 0, "t": 50, "l": 0, "b": 0},
        )
        return figure
