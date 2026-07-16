"""CSV, ZIP and Excel export service."""

from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from gwn_dashboard.domain.models import DashboardData


class ExportService:
    """Create downloadable representations without Streamlit dependencies."""

    def create_csv(self, data: pd.DataFrame) -> str:
        """Serialize a data frame as UTF-8 CSV text.
        
        Args:
            data: Value of type ``pd.DataFrame``.
        
        Returns:
            str: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        return data.to_csv(index=False, sep=";", decimal=",")

    def create_excel(self, data: DashboardData) -> bytes:
        """Create a complete Excel workbook from dashboard data.
        
        Args:
            data: Value of type ``DashboardData``.
        
        Returns:
            bytes: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        return self.create_selected_excel(self.dashboard_tables(data))

    def create_selected_excel(self, tables: dict[str, pd.DataFrame]) -> bytes:
        """Create an Excel workbook from explicitly selected tables.
        
        Args:
            tables: Value of type ``dict[str, pd.DataFrame]``.
        
        Returns:
            bytes: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            for sheet_name, table in tables.items():
                table.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        return output.getvalue()

    def create_csv_zip(self, tables: dict[str, pd.DataFrame]) -> bytes:
        """Create an in-memory ZIP archive containing CSV tables.
        
        Args:
            tables: Value of type ``dict[str, pd.DataFrame]``.
        
        Returns:
            bytes: Result produced by the operation.
        
        Raises:
            ValueError: If required input data or metadata are invalid.
        """
        output = BytesIO()
        with ZipFile(output, mode="w", compression=ZIP_DEFLATED) as archive:
            for name, table in tables.items():
                archive.writestr(
                    f"{name}.csv",
                    table.to_csv(index=False, sep=";", decimal=",", encoding="utf-8"),
                )
        return output.getvalue()

    @staticmethod
    def dashboard_tables(data: DashboardData) -> dict[str, pd.DataFrame]:
        """Return the canonical export-table mapping for dashboard data.
        
        Args:
            data: Value of type ``DashboardData``.
        
        Returns:
            dict[str, pd.DataFrame]: Result produced by the operation.
        """
        return {
            "Vergleich": data.comparison,
            "Trend": data.trends,
            "GWN_Zeitreihen": data.groundwater_recharge,
            "Niederschlag": data.precipitation,
            "ETp": data.evapotranspiration,
        }
