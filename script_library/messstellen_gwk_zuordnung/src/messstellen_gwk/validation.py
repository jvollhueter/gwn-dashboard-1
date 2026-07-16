"""Input validation."""

from __future__ import annotations

import geopandas as gpd


def validate_inputs(
    stations: gpd.GeoDataFrame,
    groundwater_bodies: gpd.GeoDataFrame,
    gwk_column: str,
) -> None:
    """Implement validate inputs."""
    if stations.crs is None:
        raise ValueError("Für die Messstellen ist kein Koordinatensystem definiert.")
    if groundwater_bodies.crs is None:
        raise ValueError("Für die Grundwasserkörper ist kein Koordinatensystem definiert.")
    if gwk_column not in groundwater_bodies.columns:
        raise ValueError(f"GWK-Spalte ist nicht vorhanden: {gwk_column}")
    if stations.geometry.is_empty.any() or stations.geometry.isna().any():
        raise ValueError("Mindestens eine Messstelle besitzt keine gültige Geometrie.")
