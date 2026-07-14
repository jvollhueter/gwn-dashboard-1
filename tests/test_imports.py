"""Import smoke tests for the refactored architecture."""


def test_application_modules_import() -> None:
    from gwn_dashboard.application import create_app_context  # noqa: F401
    from gwn_dashboard.repositories.csv_repository import CsvGroundwaterDataRepository  # noqa: F401
    from gwn_dashboard.services.dashboard_service import DashboardService  # noqa: F401
    from gwn_dashboard.visualization.chart_factory import ChartFactory  # noqa: F401
    from gwn_dashboard.visualization.map_factory import MapFactory  # noqa: F401
