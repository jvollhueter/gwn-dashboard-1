"""Integration tests for the monitoring-station layer."""

from pathlib import Path

from gwn_dashboard.config import load_config
from gwn_dashboard.repositories.csv_repository import CsvGroundwaterDataRepository


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_project_monitoring_stations_are_loaded_in_wgs84() -> None:
    """Verify project monitoring stations are loaded in wgs84."""
    repository = CsvGroundwaterDataRepository(load_config(PROJECT_ROOT).data)

    stations = repository.load_monitoring_stations()

    assert len(stations) == 3131
    assert stations["station_id"].is_unique
    assert stations.geometry.notna().all()
    assert stations.crs is not None
    assert stations.crs.to_epsg() == 4326
    assert {
        "station_id",
        "station_name",
        "station_label",
        "first_measurement",
        "last_measurement",
        "GWK_ID",
        "easting",
        "northing",
        "geometry",
    } <= set(stations.columns)
    assert stations.geometry.x.between(11.5, 15.5).all()
    assert stations.geometry.y.between(50.0, 52.0).all()
