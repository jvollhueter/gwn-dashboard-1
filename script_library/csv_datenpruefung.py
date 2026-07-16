# /// script
# requires-python = ">=3.10"
# dependencies = []
#
# [tool.ref43_library]
# id = "csv-datenpruefung"
# title = "CSV-Datenprüfung"
# short_description = "Prüft CSV-Dateien auf fehlende Werte, Duplikate und uneinheitliche Spalteninhalte."
# long_description = """
# Das Werkzeug liest eine CSV-Datei ein und erstellt einen strukturierten Prüfbericht.
# Erfasst werden Zeilen- und Spaltenzahl, fehlende Werte je Spalte, vollständig doppelte
# Datensätze sowie beispielhafte Werte. Der Bericht wird als CSV-Datei ausgegeben und
# kann ohne zusätzliche Python-Pakete erzeugt werden.
# """
# category = "Allgemeine Datenaufbereitung"
# tags = ["csv", "datenprüfung", "fehlendewerte", "duplikate", "export"]
# author = "Referat 43"
# version = "1.0.0"
# updated = "2026-07-16"
# language = "Python"
# input_formats = ["CSV"]
# output_formats = ["CSV"]
# ///

"""Create a compact quality report for a CSV file."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def inspect_csv(input_path: Path, delimiter: str = ",") -> list[dict[str, str | int]]:
    """Return one quality-summary record per column."""

    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("Die CSV-Datei besitzt keine Kopfzeile.")
        rows = list(reader)

    duplicates = sum(count - 1 for count in Counter(tuple(row.items()) for row in rows).values() if count > 1)
    report: list[dict[str, str | int]] = []
    for column in reader.fieldnames:
        values = [str(row.get(column, "")).strip() for row in rows]
        non_empty = [value for value in values if value]
        report.append(
            {
                "spalte": column,
                "zeilen": len(rows),
                "fehlende_werte": len(values) - len(non_empty),
                "unterschiedliche_werte": len(set(non_empty)),
                "beispielwert": non_empty[0] if non_empty else "",
                "doppelte_zeilen_gesamt": duplicates,
            }
        )
    return report


def write_report(records: list[dict[str, str | int]], output_path: Path) -> None:
    """Write the inspection result to a CSV file."""

    if not records:
        raise ValueError("Der Prüfbericht enthält keine Datensätze.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def parse_arguments() -> argparse.Namespace:
    """Implement parse arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Eingabedatei im CSV-Format")
    parser.add_argument("output", type=Path, help="Ausgabedatei für den Prüfbericht")
    parser.add_argument("--delimiter", default=",", help="Feldtrennzeichen der Eingabedatei")
    return parser.parse_args()


def main() -> None:
    """Implement main."""
    args = parse_arguments()
    write_report(inspect_csv(args.input, args.delimiter), args.output)
    print(f"Prüfbericht geschrieben: {args.output}")


if __name__ == "__main__":
    main()
