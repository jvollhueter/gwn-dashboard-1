"""Core domain objects used by the dashboard."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class GroundwaterBody:
    gwk_id: str
    name: str | None = None


@dataclass(frozen=True)
class Parameter:
    code: str
    label: str
    unit: str
    source_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Period:
    label: str
    start_year: int
    end_year: int

    def __post_init__(self) -> None:
        if self.start_year > self.end_year:
            raise ValueError("start_year must not be greater than end_year")

    def contains(self, year: int) -> bool:
        return self.start_year <= year <= self.end_year


@dataclass(frozen=True)
class DashboardData:
    groundwater_recharge: pd.DataFrame
    precipitation: pd.DataFrame
    evapotranspiration: pd.DataFrame
    comparison: pd.DataFrame
    trends: pd.DataFrame


@dataclass(frozen=True)
class SidebarSelection:
    groundwater_body_ids: tuple[str, ...]
    selected_groundwater_body: str
    show_precipitation: bool
    show_evapotranspiration: bool
