"""Unit tests for core dashboard services."""

import pandas as pd

from gwn_dashboard.domain.models import Period
from gwn_dashboard.services.aggregation_service import AggregationService
from gwn_dashboard.services.analysis_service import AnalysisService
from gwn_dashboard.services.comparison_service import ComparisonService


def test_groundwater_recharge_is_sum_of_rg1_and_rg2() -> None:
    """Verify groundwater recharge is sum of rg1 and rg2."""
    rg1 = pd.DataFrame({
        "id": [1, 1],
        "year": [2000, 2000],
        "month": [1, 2],
        "value": [10.0, 20.0],
    })
    rg2 = pd.DataFrame({
        "id": [1, 1],
        "year": [2000, 2000],
        "month": [1, 2],
        "value": [1.0, 2.0],
    })

    result = AggregationService().calculate_groundwater_recharge(rg1, rg2)

    assert result.loc[0, "gwn"] == 33.0


def test_period_comparison_calculates_absolute_and_relative_change() -> None:
    """Verify period comparison calculates absolute and relative change."""
    data = pd.DataFrame({
        "GWK_ID": ["A", "A", "A", "A"],
        "year": [1961, 1962, 1991, 1992],
        "gwn_mm_a": [100.0, 100.0, 80.0, 80.0],
    })
    analysis = AnalysisService()
    comparison = ComparisonService(analysis)

    result = comparison.compare_periods(
        data,
        "gwn_mm_a",
        Period("1961–1990", 1961, 1990),
        Period("1991–2020", 1991, 2020),
    )

    assert result.loc[0, "delta_abs"] == -20.0
    assert result.loc[0, "delta_rel_pct"] == -20.0
