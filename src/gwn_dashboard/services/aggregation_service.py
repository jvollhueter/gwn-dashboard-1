"""Temporal and spatial aggregation services."""

from collections.abc import Collection

import pandas as pd


class AggregationService:
    """Aggregate monthly model results and derive groundwater recharge.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    def monthly_to_yearly_sum(self, monthly_data: pd.DataFrame, value_name: str) -> pd.DataFrame:
        """Aggregate monthly parameter values to annual sums.
        
        Args:
            monthly_data: Value of type ``pd.DataFrame``.
            value_name: Value of type ``str``.
        
        Returns:
            pd.DataFrame: Result produced by the operation.
        """
        return monthly_data.groupby(["id", "year"], as_index=False)["value"].sum().rename(columns={"value": value_name})

    def calculate_groundwater_recharge(self, rg1_monthly: pd.DataFrame, rg2_monthly: pd.DataFrame) -> pd.DataFrame:
        """Calculate annual groundwater recharge as the sum of rg1 and rg2.
        
        Args:
            rg1_monthly: Value of type ``pd.DataFrame``.
            rg2_monthly: Value of type ``pd.DataFrame``.
        
        Returns:
            pd.DataFrame: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        rg1 = self.monthly_to_yearly_sum(rg1_monthly, "rg1")
        rg2 = self.monthly_to_yearly_sum(rg2_monthly, "rg2")
        merged = rg1.merge(rg2, on=["id", "year"], how="inner")
        merged["gwn"] = merged["rg1"] + merged["rg2"]
        return merged[["id", "year", "gwn"]]

    def attach_groundwater_body_id(self, data: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
        """Join the technical spatial identifier to the fachlich GWK identifier.
        
        Args:
            data: Value of type ``pd.DataFrame``.
            mapping: Value of type ``pd.DataFrame``.
        
        Returns:
            pd.DataFrame: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        return data.merge(mapping, on="id", how="left")

    def aggregate_to_groundwater_body(self, data: pd.DataFrame, value_column: str) -> pd.DataFrame:
        """Aggregate annual values to groundwater-body level.
        
        Args:
            data: Value of type ``pd.DataFrame``.
            value_column: Value of type ``str``.
        
        Returns:
            pd.DataFrame: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        return data.dropna(subset=["GWK_ID"]).groupby(["GWK_ID", "year"], as_index=False)[value_column].mean()

    def filter_groundwater_bodies(
        self,
        data: pd.DataFrame,
        groundwater_body_ids: Collection[str],
    ) -> pd.DataFrame:
        """Restrict a table to selected groundwater bodies.
        
        Args:
            data: Value of type ``pd.DataFrame``.
            groundwater_body_ids: Input value used by the operation.
        
        Returns:
            pd.DataFrame: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        return data[data["GWK_ID"].isin(groundwater_body_ids)].copy()
