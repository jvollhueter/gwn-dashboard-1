"""Output writers."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd


def write_results(
    data: gpd.GeoDataFrame,
    csv_path: Path,
    geopackage_path: Path | None = None,
) -> None:
    """Implement write results."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    tabular = data.drop(columns="geometry").copy()
    tabular.to_csv(csv_path, index=False)
    if geopackage_path is not None:
        geopackage_path.parent.mkdir(parents=True, exist_ok=True)
        data.to_file(geopackage_path, layer="messstellen_gwk", driver="GPKG")
