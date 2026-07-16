"""Repository interfaces."""

from abc import ABC, abstractmethod

import geopandas as gpd
import pandas as pd


class GroundwaterDataRepository(ABC):
    """Abstract interface for model and spatial data access.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    @abstractmethod
    def load_mapping(self) -> pd.DataFrame:
        """Load the numerical-to-GWK identifier mapping.
        
        Returns:
            pd.DataFrame: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        raise NotImplementedError

    @abstractmethod
    def get_available_groundwater_bodies(self) -> list[str]:
        """Return all groundwater-body identifiers available to the application.
        
        Returns:
            list[str]: Result produced by the operation.
        """
        raise NotImplementedError

    @abstractmethod
    def load_monthly_parameter(self, parameter_code: str) -> pd.DataFrame:
        """Load validated monthly values for one configured parameter.
        
        Args:
            parameter_code: Value of type ``str``.
        
        Returns:
            pd.DataFrame: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        raise NotImplementedError

    @abstractmethod
    def load_geometries(self) -> gpd.GeoDataFrame:
        """Load and prepare groundwater-body geometries.
        
        Returns:
            gpd.GeoDataFrame: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        raise NotImplementedError

    @abstractmethod
    def load_monitoring_stations(self) -> gpd.GeoDataFrame:
        """Load groundwater monitoring stations in WGS 84 coordinates."""

        raise NotImplementedError
