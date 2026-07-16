"""Core domain objects used by the dashboard."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class GroundwaterBody:
    """Identifier and descriptive metadata for one groundwater body.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    gwk_id: str
    name: str | None = None


@dataclass(frozen=True)
class Parameter:
    """Metadata describing one model parameter.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    code: str
    label: str
    unit: str
    source_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Period:
    """Inclusive calendar-year interval.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    label: str
    start_year: int
    end_year: int

    def __post_init__(self) -> None:
        if self.start_year > self.end_year:
            raise ValueError("start_year must not be greater than end_year")

    def contains(self, year: int) -> bool:
        """Return whether a year lies inside the inclusive period.
        
        Args:
            year: Value of type ``int``.
        
        Returns:
            bool: Result produced by the operation.
        """
        return self.start_year <= year <= self.end_year


@dataclass(frozen=True)
class DashboardData:
    """Prepared time series, comparisons, and trend tables used by the UI.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    groundwater_recharge: pd.DataFrame
    precipitation: pd.DataFrame
    evapotranspiration: pd.DataFrame
    comparison: pd.DataFrame
    trends: pd.DataFrame


@dataclass(frozen=True)
class SidebarSelection:
    """Immutable representation of the active spatial and temporal selection.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    groundwater_body_ids: tuple[str, ...]
    selected_groundwater_body: str
    reference_period: Period
    comparison_period: Period
    show_precipitation: bool
    show_evapotranspiration: bool
