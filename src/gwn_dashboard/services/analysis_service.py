"""Statistical analysis services."""

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, linregress

from gwn_dashboard.domain.models import Period


class AnalysisService:
    def period_statistics(self, data: pd.DataFrame, value_column: str, period: Period) -> pd.DataFrame:
        subset = data[data["year"].between(period.start_year, period.end_year, inclusive="both")]
        rows = []
        for groundwater_body, group in subset.groupby("GWK_ID"):
            values = group[value_column].dropna().to_numpy()
            if values.size:
                rows.append({
                    "GWK_ID": groundwater_body,
                    "mean": float(np.mean(values)),
                    "median": float(np.median(values)),
                    "std": float(np.std(values, ddof=1)) if values.size > 1 else np.nan,
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "n_years": int(values.size),
                })
        return pd.DataFrame(rows)

    def trend_statistics(self, data: pd.DataFrame, value_column: str) -> pd.DataFrame:
        rows = []
        for groundwater_body, group in data.groupby("GWK_ID"):
            clean = group[["year", value_column]].dropna().sort_values("year")
            if len(clean) < 2:
                continue
            years = clean["year"].to_numpy()
            values = clean[value_column].to_numpy()
            regression = linregress(years, values)
            tau, kendall_p = kendalltau(years, values)
            rows.append({
                "GWK_ID": groundwater_body,
                "n_years": int(len(values)),
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "std": float(np.std(values, ddof=1)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "lr_slope": float(regression.slope),
                "lr_intercept": float(regression.intercept),
                "lr_rvalue": float(regression.rvalue),
                "lr_pvalue": float(regression.pvalue),
                "lr_stderr": float(regression.stderr),
                "kendall_tau": float(tau),
                "kendall_p": float(kendall_p),
            })
        return pd.DataFrame(rows)
