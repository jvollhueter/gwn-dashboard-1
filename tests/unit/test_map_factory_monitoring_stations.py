"""Tests for the monitoring-station overlay on the GWK map."""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon

from gwn_dashboard.visualization.map_factory import MapFactory


def _geometries() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"GWK_ID": ["GWK_A"]},
        geometry=[
            Polygon(
                [
                    (13.0, 51.0),
                    (13.5, 51.0),
                    (13.5, 51.5),
                    (13.0, 51.5),
                ]
            )
        ],
        crs="EPSG:4326",
    )


def _comparison() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "GWK_ID": ["GWK_A"],
            "mean_ref": [100.0],
            "mean_hist": [90.0],
            "delta_abs": [-10.0],
            "delta_rel_pct": [-10.0],
        }
    )


def _stations() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "station_id": ["12345678"],
            "station_name": ["Testmessstelle"],
            "first_measurement": ["01.01.2000"],
            "last_measurement": ["31.12.2020"],
            "GWK_ID": ["GWK_A"],
        },
        geometry=[Point(13.25, 51.25)],
        crs="EPSG:4326",
    )


def test_map_contains_black_monitoring_station_layer() -> None:
    """Verify map contains black monitoring station layer."""
    figure = MapFactory().create_choropleth(
        _geometries(),
        _comparison(),
        monitoring_stations=_stations(),
        station_marker_size=8,
    )

    assert figure is not None
    station_traces = [
        trace for trace in figure.data if trace.name == "Grundwassermessstellen"
    ]
    assert len(station_traces) == 1
    station_trace = station_traces[0]
    assert station_trace.type == "scattermapbox"
    assert station_trace.marker.color == "#000000"
    assert station_trace.marker.size == 8
    assert station_trace.lon[0] == 13.25
    assert station_trace.lat[0] == 51.25
    assert "MKZ" in station_trace.hovertemplate


def test_map_omits_station_layer_when_no_stations_are_selected() -> None:
    """Verify map omits station layer when no stations are selected."""
    figure = MapFactory().create_choropleth(
        _geometries(),
        _comparison(),
        monitoring_stations=None,
    )

    assert figure is not None
    assert all(trace.name != "Grundwassermessstellen" for trace in figure.data)
