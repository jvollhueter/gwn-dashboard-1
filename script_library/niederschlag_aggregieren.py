# /// script
# requires-python = ">=3.10"
# dependencies = []
#
# [tool.ref43_library]
# id = "niederschlag-aggregieren"
# title = "Niederschlagsdaten aggregieren"
# short_description = "Bildet Monats-, Kalenderjahres- und hydrologische Jahressummen aus Tageswerten."
# long_description = """
# Das Skript verarbeitet tägliche Niederschlagswerte aus einer CSV-Datei. Neben
# monatlichen und kalenderjährlichen Summen werden hydrologische Jahre berechnet,
# die am 1. November beginnen. Die Ergebnisse werden in getrennte CSV-Dateien
# geschrieben. Es werden keine zusätzlichen Python-Pakete benötigt.
# """
# category = "Meteorologische Daten"
# tags = ["niederschlag", "aggregation", "hydrologisches-jahr", "zeitreihe", "csv"]
# author = "Referat 43"
# version = "1.0.0"
# updated = "2026-07-16"
# language = "Python"
# input_formats = ["CSV"]
# output_formats = ["CSV"]
# ///

"""Aggregate daily precipitation values."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import date
from pathlib import Path


def read_daily_values(path: Path) -> list[tuple[date, float]]:
    """Implement read daily values."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"datum", "niederschlag_mm"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Erwartete Spalten: datum, niederschlag_mm")
        values = []
        for row in reader:
            try:
                values.append((date.fromisoformat(row["datum"]), float(row["niederschlag_mm"])))
            except (TypeError, ValueError):
                continue
    return values


def aggregate(values: list[tuple[date, float]]):
    """Implement aggregate."""
    monthly: defaultdict[tuple[int, int], float] = defaultdict(float)
    annual: defaultdict[int, float] = defaultdict(float)
    hydrological: defaultdict[int, float] = defaultdict(float)
    for measurement_date, precipitation in values:
        monthly[(measurement_date.year, measurement_date.month)] += precipitation
        annual[measurement_date.year] += precipitation
        hydro_year = measurement_date.year + 1 if measurement_date.month >= 11 else measurement_date.year
        hydrological[hydro_year] += precipitation
    return monthly, annual, hydrological


def write_table(path: Path, headers: tuple[str, ...], rows) -> None:
    """Implement write table."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def main() -> None:
    """Implement main."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()

    monthly, annual, hydrological = aggregate(read_daily_values(args.input))
    write_table(
        args.output_directory / "monatssummen.csv",
        ("jahr", "monat", "niederschlag_mm"),
        ((year, month, round(value, 3)) for (year, month), value in sorted(monthly.items())),
    )
    write_table(
        args.output_directory / "jahressummen.csv",
        ("jahr", "niederschlag_mm"),
        ((year, round(value, 3)) for year, value in sorted(annual.items())),
    )
    write_table(
        args.output_directory / "hydrologische_jahre.csv",
        ("hydrologisches_jahr", "niederschlag_mm"),
        ((year, round(value, 3)) for year, value in sorted(hydrological.items())),
    )


if __name__ == "__main__":
    main()
