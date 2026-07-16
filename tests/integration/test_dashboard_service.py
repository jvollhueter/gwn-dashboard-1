"""Integration tests for the complete service-layer data flow."""

from pathlib import Path

import pandas as pd
import pytest

from gwn_dashboard.config import (
    ApplicationSettings,
    DashboardConfig,
    DataPaths,
)
from gwn_dashboard.domain.models import Parameter, Period
from gwn_dashboard.repositories.interfaces import GroundwaterDataRepository
from gwn_dashboard.services.aggregation_service import AggregationService
from gwn_dashboard.services.analysis_service import AnalysisService
from gwn_dashboard.services.comparison_service import ComparisonService
from gwn_dashboard.services.dashboard_service import DashboardService


class SyntheticGroundwaterDataRepository(GroundwaterDataRepository):
    """Small deterministic repository for an end-to-end service test."""

    def load_mapping(self) -> pd.DataFrame:
        """Verify load mapping."""
        return pd.DataFrame(
            {
                "id": [1, 2],
                "GWK_ID": ["GWK_A", "GWK_B"],
            }
        )

    def get_available_groundwater_bodies(self) -> list[str]:
        """Verify get available groundwater bodies."""
        return ["GWK_A", "GWK_B"]

    def load_monthly_parameter(self, parameter_code: str) -> pd.DataFrame:
        """Verify load monthly parameter."""
        values = {
            "rg1": [40.0, 60.0, 80.0, 100.0],
            "rg2": [4.0, 6.0, 8.0, 10.0],
            "P": [200.0, 300.0, 400.0, 500.0],
            "ETp": [150.0, 200.0, 250.0, 300.0],
        }
        return pd.DataFrame(
            {
                "id": [1, 1, 2, 2],
                "year": [2000, 2010, 2000, 2010],
                "month": [1, 1, 1, 1],
                "value": values[parameter_code],
            }
        )

    def load_geometries(self):
        """Verify load geometries."""
        raise NotImplementedError

    def load_monitoring_stations(self):
        """Verify load monitoring stations."""
        raise NotImplementedError


def create_test_config(project_root: Path) -> DashboardConfig:
    """Verify create config."""
    return DashboardConfig(
        application=ApplicationSettings(
            title="Test dashboard",
            page_title="Test dashboard",
            page_icon="",
            layout="wide",
            initial_sidebar_state="expanded",
        ),
        data=DataPaths(
            base_directory=project_root,
            mapping_file=project_root / "mapping.csv",
            geometry_file=project_root / "geometry.shp",
            station_overview_file=project_root / "stations.csv",
            station_mapping_file=project_root / "station_mapping.csv",
        ),
        reference_period=Period("Referenz", 2000, 2000),
        comparison_period=Period("Vergleich", 2010, 2010),
        groundwater_recharge=Parameter(
            code="gwn",
            label="Grundwasserneubildung",
            unit="mm/a",
            source_codes=("rg1", "rg2"),
        ),
        precipitation=Parameter(
            code="P",
            label="Niederschlag",
            unit="mm/a",
        ),
        potential_evapotranspiration=Parameter(
            code="ETp",
            label="Potenzielle Evapotranspiration",
            unit="mm/a",
        ),
    )


@pytest.mark.integration
def test_dashboard_service_builds_expected_data_for_selected_gwk(
    tmp_path: Path,
) -> None:
    """Verify dashboard service builds expected data for selected gwk."""
    analysis = AnalysisService()
    service = DashboardService(
        config=create_test_config(tmp_path),
        repository=SyntheticGroundwaterDataRepository(),
        aggregation_service=AggregationService(),
        analysis_service=analysis,
        comparison_service=ComparisonService(analysis),
    )

    result = service.load_dashboard_data(("GWK_A",))

    expected_recharge = pd.DataFrame(
        {
            "GWK_ID": ["GWK_A", "GWK_A"],
            "year": [2000, 2010],
            "gwn_mm_a": [44.0, 66.0],
        }
    )
    pd.testing.assert_frame_equal(
        result.groundwater_recharge.reset_index(drop=True),
        expected_recharge,
    )

    assert result.precipitation["value"].tolist() == [200.0, 300.0]
    assert result.evapotranspiration["value"].tolist() == [150.0, 200.0]

    comparison = result.comparison.iloc[0]
    assert comparison["mean_ref"] == 44.0
    assert comparison["mean_hist"] == 66.0
    assert comparison["delta_abs"] == 22.0
    assert comparison["delta_rel_pct"] == 50.0

    trend = result.trends.iloc[0]
    assert trend["lr_slope"] == pytest.approx(2.2)


@pytest.mark.integration
def test_dashboard_service_reports_common_available_year_range(
    tmp_path: Path,
) -> None:
    """Verify dashboard service reports common available year range."""
    analysis = AnalysisService()
    service = DashboardService(
        config=create_test_config(tmp_path),
        repository=SyntheticGroundwaterDataRepository(),
        aggregation_service=AggregationService(),
        analysis_service=analysis,
        comparison_service=ComparisonService(analysis),
    )

    assert service.get_available_year_range() == (2000, 2010)


@pytest.mark.integration
def test_dashboard_service_accepts_individually_selected_periods(
    tmp_path: Path,
) -> None:
    """Verify dashboard service accepts individually selected periods."""
    analysis = AnalysisService()
    service = DashboardService(
        config=create_test_config(tmp_path),
        repository=SyntheticGroundwaterDataRepository(),
        aggregation_service=AggregationService(),
        analysis_service=analysis,
        comparison_service=ComparisonService(analysis),
    )

    result = service.load_dashboard_data(
        ("GWK_A",),
        reference_period=Period("Individuelle Referenz", 2000, 2000),
        comparison_period=Period("Individueller Vergleich", 2010, 2010),
    )

    comparison = result.comparison.iloc[0]
    assert comparison["mean_ref"] == 44.0
    assert comparison["mean_hist"] == 66.0


@pytest.mark.integration
def test_dashboard_service_rejects_overlapping_periods(
    tmp_path: Path,
) -> None:
    """Verify dashboard service rejects overlapping periods."""
    analysis = AnalysisService()
    service = DashboardService(
        config=create_test_config(tmp_path),
        repository=SyntheticGroundwaterDataRepository(),
        aggregation_service=AggregationService(),
        analysis_service=analysis,
        comparison_service=ComparisonService(analysis),
    )

    with pytest.raises(ValueError, match="müssen getrennt sein"):
        service.load_dashboard_data(
            ("GWK_A",),
            reference_period=Period("Referenz", 2000, 2005),
            comparison_period=Period("Vergleich", 2005, 2010),
        )
