"""CSV and shapefile implementation of the data repository."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from gwn_dashboard.config import DataPaths
from gwn_dashboard.repositories.interfaces import GroundwaterDataRepository


class CsvGroundwaterDataRepository(GroundwaterDataRepository):
    REQUIRED_MONTHLY_COLUMNS = {"id", "year", "month", "value"}

    def __init__(self, paths: DataPaths) -> None:
        self._paths = paths

    def load_mapping(self) -> pd.DataFrame:
        mapping = pd.read_csv(self._paths.mapping_file, sep=",", on_bad_lines="skip")
        missing = {"id", "desc"} - set(mapping.columns)
        if missing:
            raise ValueError(f"Mapping CSV: fehlende Spalten {sorted(missing)}")
        mapping = mapping[["id", "desc"]].copy()
        mapping["id"] = mapping["id"].astype(int)
        mapping["GWK_ID"] = mapping["desc"].astype(str).str.strip()
        return mapping[["id", "GWK_ID"]]

    def get_available_groundwater_bodies(self) -> list[str]:
        mapping = self.load_mapping()
        return sorted(mapping["GWK_ID"].dropna().unique().tolist())

    def load_monthly_parameter(self, parameter_code: str) -> pd.DataFrame:
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
        geometries = gpd.read_file(self._paths.geometry_file)
        if geometries.crs is not None and geometries.crs.to_epsg() != 4326:
            geometries = geometries.to_crs(epsg=4326)
        if "desc" not in geometries.columns:
            raise ValueError("Geometriedatei benötigt die Spalte 'desc'.")
        geometries = geometries.copy()
        geometries["GWK_ID"] = geometries["desc"].astype(str).str.strip()
        return geometries

    def _find_parameter_file(self, parameter_code: str) -> Path:
        folders = sorted(self._paths.base_directory.glob(f"{parameter_code}_*_all_month"))
        if not folders:
            raise FileNotFoundError(f"Kein Datenordner für '{parameter_code}' gefunden.")
        csv_path = folders[0] / f"{folders[0].name}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Parameterdatei nicht gefunden: {csv_path}")
        return csv_path
