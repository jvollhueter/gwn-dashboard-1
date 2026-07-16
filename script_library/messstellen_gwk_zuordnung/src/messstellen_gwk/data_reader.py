"""Input readers."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


def read_stations(path: Path, crs: str) -> gpd.GeoDataFrame:
    """Implement read stations."""
    data = pd.read_csv(path, dtype={"station_id": "string"})
    required = {"station_id", "easting", "northing"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Fehlende Messstellenspalten: {', '.join(sorted(missing))}")
    geometry = gpd.points_from_xy(data["easting"], data["northing"])
    return gpd.GeoDataFrame(data, geometry=geometry, crs=crs)


def read_groundwater_bodies(path: Path) -> gpd.GeoDataFrame:
    """Implement read groundwater bodies."""
    return gpd.read_file(path)
