"""Import smoke tests for the refactored architecture."""

import pytest


@pytest.mark.smoke
def test_application_modules_import() -> None:
    from gwn_dashboard.application import create_app_context  # noqa: F401
    from gwn_dashboard.config import load_config  # noqa: F401
    from gwn_dashboard.design.plotly_theme import apply_dashboard_layout  # noqa: F401
    from gwn_dashboard.design.style_loader import load_global_styles  # noqa: F401
    from gwn_dashboard.design.theme import COLORS  # noqa: F401
    from gwn_dashboard.repositories.csv_repository import (  # noqa: F401
        CsvGroundwaterDataRepository,
    )
    from gwn_dashboard.services.dashboard_service import DashboardService  # noqa: F401
    from gwn_dashboard.services.export_service import ExportService  # noqa: F401
    from gwn_dashboard.visualization.chart_factory import ChartFactory  # noqa: F401
    from gwn_dashboard.visualization.map_factory import MapFactory  # noqa: F401
