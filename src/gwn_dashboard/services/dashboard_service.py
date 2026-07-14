"""Facade used by the user interface."""

import geopandas as gpd
import pandas as pd

from gwn_dashboard.config import DashboardConfig
from gwn_dashboard.domain.models import DashboardData
from gwn_dashboard.repositories.interfaces import GroundwaterDataRepository
from gwn_dashboard.services.aggregation_service import AggregationService
from gwn_dashboard.services.analysis_service import AnalysisService
from gwn_dashboard.services.comparison_service import ComparisonService


class DashboardService:
    def __init__(self, config: DashboardConfig, repository: GroundwaterDataRepository, aggregation_service: AggregationService, analysis_service: AnalysisService, comparison_service: ComparisonService) -> None:
        self._config = config
        self._repository = repository
        self._aggregation = aggregation_service
        self._analysis = analysis_service
        self._comparison = comparison_service

    def get_available_groundwater_bodies(self) -> list[str]:
        return self._repository.get_available_groundwater_bodies()

    def load_geometries(self) -> gpd.GeoDataFrame:
        return self._repository.load_geometries()

    def load_dashboard_data(self, groundwater_body_ids) -> DashboardData:
        selected = tuple(groundwater_body_ids)
        mapping = self._repository.load_mapping()
        recharge_codes = self._config.groundwater_recharge.source_codes
        if len(recharge_codes) != 2:
            raise ValueError("GWN benötigt genau zwei Quellparameter.")
        recharge_by_id = self._aggregation.calculate_groundwater_recharge(
            self._repository.load_monthly_parameter(recharge_codes[0]),
            self._repository.load_monthly_parameter(recharge_codes[1]),
        )
        recharge = self._prepare(recharge_by_id, mapping, "gwn", selected).rename(columns={"gwn": "gwn_mm_a"})
        precipitation = self._prepare(
            self._aggregation.monthly_to_yearly_sum(self._repository.load_monthly_parameter(self._config.precipitation.code), "value"),
            mapping, "value", selected,
        )
        evapotranspiration = self._prepare(
            self._aggregation.monthly_to_yearly_sum(self._repository.load_monthly_parameter(self._config.potential_evapotranspiration.code), "value"),
            mapping, "value", selected,
        )
        comparison = self._comparison.compare_periods(
            recharge, "gwn_mm_a", self._config.reference_period, self._config.comparison_period
        )
        trends = self._analysis.trend_statistics(recharge, "gwn_mm_a")
        return DashboardData(recharge, precipitation, evapotranspiration, comparison, trends)

    def _prepare(self, data: pd.DataFrame, mapping: pd.DataFrame, value_column: str, selected) -> pd.DataFrame:
        data = self._aggregation.attach_groundwater_body_id(data, mapping)
        data = self._aggregation.aggregate_to_groundwater_body(data, value_column)
        return self._aggregation.filter_groundwater_bodies(data, selected)
