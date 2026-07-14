"""CSV and Excel export service."""

from io import BytesIO

import pandas as pd

from gwn_dashboard.domain.models import DashboardData


class ExportService:
    def create_csv(self, data: pd.DataFrame) -> str:
        return data.to_csv(index=False, sep=";", decimal=",")

    def create_excel(self, data: DashboardData) -> bytes:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            data.comparison.to_excel(writer, sheet_name="Vergleich", index=False)
            data.trends.to_excel(writer, sheet_name="Trend", index=False)
            data.groundwater_recharge.to_excel(writer, sheet_name="GWN_Zeitreihen", index=False)
            data.precipitation.to_excel(writer, sheet_name="Niederschlag", index=False)
            data.evapotranspiration.to_excel(writer, sheet_name="ETp", index=False)
        return output.getvalue()
