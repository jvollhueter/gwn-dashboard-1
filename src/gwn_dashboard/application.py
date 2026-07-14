"""Dependency construction for the dashboard."""

from dataclasses import dataclass

from gwn_dashboard.config import DashboardConfig
from gwn_dashboard.repositories.csv_repository import CsvGroundwaterDataRepository
from gwn_dashboard.services.aggregation_service import AggregationService
from gwn_dashboard.services.analysis_service import AnalysisService
from gwn_dashboard.services.comparison_service import ComparisonService
from gwn_dashboard.services.dashboard_service import DashboardService
from gwn_dashboard.services.export_service import ExportService
from gwn_dashboard.visualization.chart_factory import ChartFactory
from gwn_dashboard.visualization.map_factory import MapFactory


@dataclass(frozen=True)
class AppContext:
    dashboard_service: DashboardService
    export_service: ExportService
    chart_factory: ChartFactory
    map_factory: MapFactory


def create_app_context(config: DashboardConfig) -> AppContext:
    repository = CsvGroundwaterDataRepository(config.data)
    aggregation = AggregationService()
    analysis = AnalysisService()
    comparison = ComparisonService(analysis)
    return AppContext(
        dashboard_service=DashboardService(config, repository, aggregation, analysis, comparison),
        export_service=ExportService(),
        chart_factory=ChartFactory(config),
        map_factory=MapFactory(),
    )
