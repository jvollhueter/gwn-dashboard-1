"""Facade used by the user interface."""

from __future__ import annotations

from collections.abc import Collection

import geopandas as gpd
import pandas as pd

from gwn_dashboard.config import DashboardConfig
from gwn_dashboard.domain.models import DashboardData, Period
from gwn_dashboard.repositories.interfaces import GroundwaterDataRepository
from gwn_dashboard.services.aggregation_service import AggregationService
from gwn_dashboard.services.analysis_service import AnalysisService
from gwn_dashboard.services.comparison_service import ComparisonService


class DashboardService:
    """Coordinate repository access and all groundwater data preparation.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    def __init__(
        self,
        config: DashboardConfig,
        repository: GroundwaterDataRepository,
        aggregation_service: AggregationService,
        analysis_service: AnalysisService,
        comparison_service: ComparisonService,
    ) -> None:
        self._config = config
        self._repository = repository
        self._aggregation = aggregation_service
        self._analysis = analysis_service
        self._comparison = comparison_service

    def get_available_groundwater_bodies(self) -> list[str]:
        """Return all groundwater-body identifiers available to the application.
        
        Returns:
            list[str]: Result produced by the operation.
        """
        return self._repository.get_available_groundwater_bodies()

    def get_available_year_range(self) -> tuple[int, int]:
        """Return the common year range available for all displayed parameters."""

        parameter_codes = tuple(
            dict.fromkeys(
                (
                    *self._config.groundwater_recharge.source_codes,
                    self._config.precipitation.code,
                    self._config.potential_evapotranspiration.code,
                )
            )
        )
        if not parameter_codes:
            raise ValueError("Keine Parameter für die Ermittlung des Zeitraums konfiguriert.")

        lower_bounds: list[int] = []
        upper_bounds: list[int] = []
        for parameter_code in parameter_codes:
            data = self._repository.load_monthly_parameter(parameter_code)
            years = pd.to_numeric(data["year"], errors="coerce").dropna()
            if years.empty:
                raise ValueError(
                    f"Für den Parameter '{parameter_code}' sind keine gültigen Jahre vorhanden."
                )
            lower_bounds.append(int(years.min()))
            upper_bounds.append(int(years.max()))

        minimum_year = max(lower_bounds)
        maximum_year = min(upper_bounds)
        if minimum_year > maximum_year:
            raise ValueError("Die konfigurierten Parameter besitzen keinen gemeinsamen Zeitraum.")
        return minimum_year, maximum_year

    def load_geometries(self) -> gpd.GeoDataFrame:
        """Load and prepare groundwater-body geometries.
        
        Returns:
            gpd.GeoDataFrame: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        return self._repository.load_geometries()

    def load_monitoring_stations(self) -> gpd.GeoDataFrame:
        """Load monitoring-station metadata and point geometries.
        
        Returns:
            gpd.GeoDataFrame: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        return self._repository.load_monitoring_stations()

    def load_dashboard_data(
        self,
        groundwater_body_ids: Collection[str],
        reference_period: Period | None = None,
        comparison_period: Period | None = None,
    ) -> DashboardData:
        """Load, aggregate, compare, and analyse all dashboard data.
        
        Args:
            groundwater_body_ids: Input value used by the operation.
            reference_period: Value of type ``Period | None``.
            comparison_period: Value of type ``Period | None``.
        
        Returns:
            DashboardData: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        selected = tuple(groundwater_body_ids)
        reference = reference_period or self._config.reference_period
        comparison_period_resolved = comparison_period or self._config.comparison_period
        self._validate_periods(reference, comparison_period_resolved)

        mapping = self._repository.load_mapping()
        recharge_codes = self._config.groundwater_recharge.source_codes
        if len(recharge_codes) != 2:
            raise ValueError("GWN benötigt genau zwei Quellparameter.")
        recharge_by_id = self._aggregation.calculate_groundwater_recharge(
            self._repository.load_monthly_parameter(recharge_codes[0]),
            self._repository.load_monthly_parameter(recharge_codes[1]),
        )
        recharge = self._prepare(
            recharge_by_id,
            mapping,
            "gwn",
            selected,
        ).rename(columns={"gwn": "gwn_mm_a"})
        precipitation = self._prepare(
            self._aggregation.monthly_to_yearly_sum(
                self._repository.load_monthly_parameter(
                    self._config.precipitation.code
                ),
                "value",
            ),
            mapping,
            "value",
            selected,
        )
        evapotranspiration = self._prepare(
            self._aggregation.monthly_to_yearly_sum(
                self._repository.load_monthly_parameter(
                    self._config.potential_evapotranspiration.code
                ),
                "value",
            ),
            mapping,
            "value",
            selected,
        )
        comparison = self._comparison.compare_periods(
            recharge,
            "gwn_mm_a",
            reference,
            comparison_period_resolved,
        )
        trends = self._analysis.trend_statistics(recharge, "gwn_mm_a")
        return DashboardData(
            recharge,
            precipitation,
            evapotranspiration,
            comparison,
            trends,
        )

    def _prepare(
        self,
        data: pd.DataFrame,
        mapping: pd.DataFrame,
        value_column: str,
        selected,
    ) -> pd.DataFrame:
        data = self._aggregation.attach_groundwater_body_id(data, mapping)
        data = self._aggregation.aggregate_to_groundwater_body(data, value_column)
        return self._aggregation.filter_groundwater_bodies(data, selected)

    @staticmethod
    def _validate_periods(reference_period: Period, comparison_period: Period) -> None:
        if reference_period.end_year >= comparison_period.start_year:
            raise ValueError(
                "Referenz- und Vergleichszeitraum müssen getrennt sein; "
                "der Referenzzeitraum muss vor dem Vergleichszeitraum liegen."
            )
