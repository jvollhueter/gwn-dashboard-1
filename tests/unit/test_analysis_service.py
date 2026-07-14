"""Unit tests for period and trend statistics."""

import numpy as np
import pandas as pd
import pytest

from gwn_dashboard.domain.models import Period
from gwn_dashboard.services.analysis_service import AnalysisService


def test_period_statistics_use_inclusive_period_boundaries() -> None:
    data = pd.DataFrame(
        {
            "GWK_ID": ["A", "A", "A", "A"],
            "year": [1960, 1961, 1990, 1991],
            "gwn_mm_a": [999.0, 100.0, 200.0, 999.0],
        }
    )

    result = AnalysisService().period_statistics(
        data,
        "gwn_mm_a",
        Period("1961–1990", 1961, 1990),
    )

    row = result.iloc[0]
    assert row["mean"] == 150.0
    assert row["median"] == 150.0
    assert row["min"] == 100.0
    assert row["max"] == 200.0
    assert row["n_years"] == 2


def test_period_statistics_ignore_missing_values() -> None:
    data = pd.DataFrame(
        {
            "GWK_ID": ["A", "A", "A"],
            "year": [2000, 2001, 2002],
            "gwn_mm_a": [100.0, np.nan, 200.0],
        }
    )

    result = AnalysisService().period_statistics(
        data,
        "gwn_mm_a",
        Period("2000–2002", 2000, 2002),
    )

    row = result.iloc[0]
    assert row["mean"] == 150.0
    assert row["n_years"] == 2


def test_trend_statistics_detect_perfect_linear_increase() -> None:
    data = pd.DataFrame(
        {
            "GWK_ID": ["A", "A", "A", "A"],
            "year": [2000, 2001, 2002, 2003],
            "gwn_mm_a": [10.0, 12.0, 14.0, 16.0],
        }
    )

    result = AnalysisService().trend_statistics(
        data,
        "gwn_mm_a",
    )

    row = result.iloc[0]
    assert row["lr_slope"] == pytest.approx(2.0)
    assert row["lr_rvalue"] == pytest.approx(1.0)
    assert row["kendall_tau"] == pytest.approx(1.0)
    assert row["n_years"] == 4


def test_trend_statistics_skip_groundwater_body_with_one_value() -> None:
    data = pd.DataFrame(
        {
            "GWK_ID": ["A"],
            "year": [2000],
            "gwn_mm_a": [100.0],
        }
    )

    result = AnalysisService().trend_statistics(
        data,
        "gwn_mm_a",
    )

    assert result.empty
