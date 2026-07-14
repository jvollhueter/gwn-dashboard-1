"""Import smoke tests for the refactored architecture."""

import pytest


@pytest.mark.smoke
def test_application_modules_import() -> None:
    from gwn_dashboard.application import create_app_context  # noqa: F401
    from gwn_dashboard.config import load_config  # noqa: F401
    from gwn_dashboard.repositories.csv_repository import (  # noqa: F401
        CsvGroundwaterDataRepository,
    )
    from gwn_dashboard.services.dashboard_service import DashboardService  # noqa: F401
    from gwn_dashboard.services.export_service import ExportService  # noqa: F401
    from gwn_dashboard.visualization.chart_factory import ChartFactory  # noqa: F401
    from gwn_dashboard.visualization.map_factory import MapFactory  # noqa: F401
