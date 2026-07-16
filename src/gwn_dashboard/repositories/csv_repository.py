"""CSV and shapefile implementation of the data repository."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from gwn_dashboard.config import DataPaths
from gwn_dashboard.repositories.interfaces import GroundwaterDataRepository


class CsvGroundwaterDataRepository(GroundwaterDataRepository):
    """Load groundwater data and spatial metadata from local files.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    REQUIRED_MONTHLY_COLUMNS = {"id", "year", "month", "value"}

    def __init__(self, paths: DataPaths) -> None:
        self._paths = paths

    def load_mapping(self) -> pd.DataFrame:
        """Load the numerical-to-GWK identifier mapping.
        
        Returns:
            pd.DataFrame: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        mapping = pd.read_csv(self._paths.mapping_file, sep=",", on_bad_lines="skip")
        missing = {"id", "desc"} - set(mapping.columns)
        if missing:
            raise ValueError(f"Mapping CSV: fehlende Spalten {sorted(missing)}")
        mapping = mapping[["id", "desc"]].copy()
        mapping["id"] = mapping["id"].astype(int)
        mapping["GWK_ID"] = mapping["desc"].astype(str).str.strip()
        return mapping[["id", "GWK_ID"]]

    def get_available_groundwater_bodies(self) -> list[str]:
        """Return all groundwater-body identifiers available to the application.
        
        Returns:
            list[str]: Result produced by the operation.
        """
        mapping = self.load_mapping()
        return sorted(mapping["GWK_ID"].dropna().unique().tolist())

    def load_monthly_parameter(self, parameter_code: str) -> pd.DataFrame:
        """Load validated monthly values for one configured parameter.
        
        Args:
            parameter_code: Value of type ``str``.
        
        Returns:
            pd.DataFrame: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        csv_path = self._find_parameter_file(parameter_code)
        data = pd.read_csv(csv_path)
        missing = self.REQUIRED_MONTHLY_COLUMNS - set(data.columns)
        if missing:
            raise ValueError(f"{csv_path}: fehlende Spalten {sorted(missing)}")
        data = data[["id", "year", "month", "value"]].copy()
        data["id"] = data["id"].astype(int)
        data["year"] = data["year"].astype(int)
        data["month"] = data["month"].astype(int)
        data["value"] = pd.to_numeric(data["value"], errors="coerce")
        return data

    def load_geometries(self) -> gpd.GeoDataFrame:
        """Load and prepare groundwater-body geometries.
        
        Returns:
            gpd.GeoDataFrame: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        geometries = gpd.read_file(self._paths.geometry_file)
        if geometries.crs is not None and geometries.crs.to_epsg() != 4326:
            geometries = geometries.to_crs(epsg=4326)
        if "desc" not in geometries.columns:
            raise ValueError("Geometriedatei benötigt die Spalte 'desc'.")
        geometries = geometries.copy()
        geometries["GWK_ID"] = geometries["desc"].astype(str).str.strip()
        return geometries


    def load_monitoring_stations(self) -> gpd.GeoDataFrame:
        """Load monitoring-station metadata and transform coordinates to WGS 84."""

        stations = pd.read_csv(
            self._paths.station_overview_file,
            sep=";",
            dtype={"MKZ": "string"},
            on_bad_lines="skip",
        )
        required = {
            "MKZ",
            "MESSSTELLE_NAME",
            "RW_ETRS89",
            "HW_ETRS89",
            "Erstes_Messdatum",
            "Letztes_Messdatum",
        }
        missing = required - set(stations.columns)
        if missing:
            raise ValueError(
                "Messstellenübersicht: fehlende Spalten "
                f"{sorted(missing)}"
            )

        stations = stations.copy()
        stations["station_id"] = stations["MKZ"].astype("string").str.strip()
        stations["station_name"] = (
            stations["MESSSTELLE_NAME"]
            .astype("string")
            .fillna("Unbenannte Messstelle")
            .str.strip()
        )
        stations["easting"] = pd.to_numeric(
            stations["RW_ETRS89"], errors="coerce"
        )
        stations["northing"] = pd.to_numeric(
            stations["HW_ETRS89"], errors="coerce"
        )
        stations = stations.dropna(
            subset=["station_id", "easting", "northing"]
        )
        stations = stations.drop_duplicates(subset="station_id", keep="first")

        station_mapping = pd.read_csv(
            self._paths.station_mapping_file,
            sep=";",
            dtype={"MKZ": "string", "GWK25": "string"},
            on_bad_lines="skip",
        )
        mapping_missing = {"MKZ", "GWK25"} - set(station_mapping.columns)
        if mapping_missing:
            raise ValueError(
                "Messstellen-GWK-Zuordnung: fehlende Spalten "
                f"{sorted(mapping_missing)}"
            )
        station_mapping = station_mapping[["MKZ", "GWK25"]].copy()
        station_mapping["station_id"] = (
            station_mapping["MKZ"].astype("string").str.strip()
        )
        station_mapping["GWK_ID"] = (
            station_mapping["GWK25"].astype("string").str.strip()
        )
        station_mapping = station_mapping.drop_duplicates(
            subset="station_id", keep="first"
        )
        stations = stations.merge(
            station_mapping[["station_id", "GWK_ID"]],
            on="station_id",
            how="left",
        )
        stations["GWK_ID"] = stations["GWK_ID"].fillna("nicht zugeordnet")
        stations["first_measurement"] = self._format_station_date(
            stations["Erstes_Messdatum"]
        )
        stations["last_measurement"] = self._format_station_date(
            stations["Letztes_Messdatum"]
        )
        stations["station_label"] = (
            stations["station_name"] + " — " + stations["station_id"]
        )

        result = gpd.GeoDataFrame(
            stations[
                [
                    "station_id",
                    "station_name",
                    "station_label",
                    "first_measurement",
                    "last_measurement",
                    "GWK_ID",
                    "easting",
                    "northing",
                ]
            ].copy(),
            geometry=gpd.points_from_xy(
                stations["easting"],
                stations["northing"],
            ),
            crs="EPSG:25833",
        )
        return result.to_crs(epsg=4326).sort_values(
            ["station_name", "station_id"]
        ).reset_index(drop=True)

    @staticmethod
    def _format_station_date(values: pd.Series) -> pd.Series:
        parsed = pd.to_datetime(values, errors="coerce")
        formatted = parsed.dt.strftime("%d.%m.%Y")
        return formatted.fillna("nicht angegeben")

    def _find_parameter_file(self, parameter_code: str) -> Path:
        folders = sorted(self._paths.base_directory.glob(f"{parameter_code}_*_all_month"))
        if not folders:
            raise FileNotFoundError(f"Kein Datenordner für '{parameter_code}' gefunden.")
        csv_path = folders[0] / f"{folders[0].name}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Parameterdatei nicht gefunden: {csv_path}")
        return csv_path
