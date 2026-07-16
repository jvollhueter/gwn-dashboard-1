"""Unit tests for comparisons between analysis periods."""

import numpy as np
import pandas as pd
import pytest

from gwn_dashboard.domain.models import Period
from gwn_dashboard.services.analysis_service import AnalysisService
from gwn_dashboard.services.comparison_service import ComparisonService


def test_period_comparison_calculates_expected_values_for_multiple_gwk() -> None:
    """Verify period comparison calculates expected values for multiple gwk."""
    data = pd.DataFrame(
        {
            "GWK_ID": [
                "A", "A", "A", "A",
                "B", "B", "B", "B",
            ],
            "year": [
                1961, 1962, 1991, 1992,
                1961, 1962, 1991, 1992,
            ],
            "gwn_mm_a": [
                100.0, 100.0, 80.0, 80.0,
                50.0, 70.0, 90.0, 110.0,
            ],
        }
    )

    result = ComparisonService(AnalysisService()).compare_periods(
        data,
        "gwn_mm_a",
        Period("1961–1990", 1961, 1990),
        Period("1991–2020", 1991, 2020),
    )

    row_a = result.loc[result["GWK_ID"] == "A"].iloc[0]
    row_b = result.loc[result["GWK_ID"] == "B"].iloc[0]

    assert row_a["mean_ref"] == 100.0
    assert row_a["mean_hist"] == 80.0
    assert row_a["delta_abs"] == -20.0
    assert row_a["delta_rel_pct"] == -20.0

    assert row_b["mean_ref"] == 60.0
    assert row_b["mean_hist"] == 100.0
    assert row_b["delta_abs"] == 40.0
    assert row_b["delta_rel_pct"] == pytest.approx(66.6666666667)


def test_relative_change_is_nan_when_reference_mean_is_zero() -> None:
    """Verify relative change is nan when reference mean is zero."""
    data = pd.DataFrame(
        {
            "GWK_ID": ["A", "A"],
            "year": [1961, 1991],
            "gwn_mm_a": [0.0, 100.0],
        }
    )

    result = ComparisonService(AnalysisService()).compare_periods(
        data,
        "gwn_mm_a",
        Period("Referenz", 1961, 1961),
        Period("Vergleich", 1991, 1991),
    )

    assert result.loc[0, "delta_abs"] == 100.0
    assert np.isnan(result.loc[0, "delta_rel_pct"])
