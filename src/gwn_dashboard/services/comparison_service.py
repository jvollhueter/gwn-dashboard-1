"""Period comparison service."""

import numpy as np
import pandas as pd

from gwn_dashboard.domain.models import Period
from gwn_dashboard.services.analysis_service import AnalysisService


class ComparisonService:
    def __init__(self, analysis_service: AnalysisService) -> None:
        self._analysis = analysis_service

    def compare_periods(self, data: pd.DataFrame, value_column: str, reference_period: Period, comparison_period: Period) -> pd.DataFrame:
        reference = self._analysis.period_statistics(data, value_column, reference_period).rename(columns={
            "mean": "mean_ref", "median": "median_ref", "std": "std_ref",
            "min": "min_ref", "max": "max_ref", "n_years": "n_years_ref",
        })
        comparison = self._analysis.period_statistics(data, value_column, comparison_period).rename(columns={
            "mean": "mean_hist", "median": "median_hist", "std": "std_hist",
            "min": "min_hist", "max": "max_hist", "n_years": "n_years_hist",
        })
        result = reference.merge(comparison, on="GWK_ID", how="inner")
        result["delta_abs"] = result["mean_hist"] - result["mean_ref"]
        result["delta_rel_pct"] = np.where(
            result["mean_ref"].abs() > 1e-12,
            result["delta_abs"] / result["mean_ref"] * 100.0,
            np.nan,
        )
        return result
