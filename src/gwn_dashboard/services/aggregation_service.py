"""Temporal and spatial aggregation services."""

import pandas as pd


class AggregationService:
    def monthly_to_yearly_sum(self, monthly_data: pd.DataFrame, value_name: str) -> pd.DataFrame:
        return monthly_data.groupby(["id", "year"], as_index=False)["value"].sum().rename(columns={"value": value_name})

    def calculate_groundwater_recharge(self, rg1_monthly: pd.DataFrame, rg2_monthly: pd.DataFrame) -> pd.DataFrame:
        rg1 = self.monthly_to_yearly_sum(rg1_monthly, "rg1")
        rg2 = self.monthly_to_yearly_sum(rg2_monthly, "rg2")
        merged = rg1.merge(rg2, on=["id", "year"], how="inner")
        merged["gwn"] = merged["rg1"] + merged["rg2"]
        return merged[["id", "year", "gwn"]]

    def attach_groundwater_body_id(self, data: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
        return data.merge(mapping, on="id", how="left")

    def aggregate_to_groundwater_body(self, data: pd.DataFrame, value_column: str) -> pd.DataFrame:
        return data.dropna(subset=["GWK_ID"]).groupby(["GWK_ID", "year"], as_index=False)[value_column].mean()

    def filter_groundwater_bodies(self, data: pd.DataFrame, groundwater_body_ids) -> pd.DataFrame:
        return data[data["GWK_ID"].isin(groundwater_body_ids)].copy()
