"""Spatial join logic."""

from __future__ import annotations

import geopandas as gpd


def assign_groundwater_bodies(
    stations: gpd.GeoDataFrame,
    groundwater_bodies: gpd.GeoDataFrame,
    gwk_column: str,
) -> gpd.GeoDataFrame:
    """Implement assign groundwater bodies."""
    polygons = groundwater_bodies[[gwk_column, "geometry"]].copy()
    points = stations.to_crs(polygons.crs)
    joined = gpd.sjoin(points, polygons, how="left", predicate="within")
    joined = joined.rename(columns={gwk_column: "GWK_ID"})
    counts = joined.groupby("station_id")["GWK_ID"].transform("count")
    joined["zuordnungsstatus"] = "zugeordnet"
    joined.loc[joined["GWK_ID"].isna(), "zuordnungsstatus"] = "nicht zugeordnet"
    joined.loc[counts > 1, "zuordnungsstatus"] = "mehrfach zugeordnet"
    return joined.drop(columns=["index_right"], errors="ignore")
