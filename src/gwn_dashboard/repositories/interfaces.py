"""Repository interfaces."""

from abc import ABC, abstractmethod

import geopandas as gpd
import pandas as pd


class GroundwaterDataRepository(ABC):
    @abstractmethod
    def load_mapping(self) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def get_available_groundwater_bodies(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def load_monthly_parameter(self, parameter_code: str) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def load_geometries(self) -> gpd.GeoDataFrame:
        raise NotImplementedError
