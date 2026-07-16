"""Command-line entry point for spatial station assignment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIRECTORY = PROJECT_ROOT / "src"
if str(SRC_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SRC_DIRECTORY))

from messstellen_gwk.data_reader import read_groundwater_bodies, read_stations
from messstellen_gwk.exporter import write_results
from messstellen_gwk.spatial_assignment import assign_groundwater_bodies
from messstellen_gwk.validation import validate_inputs


def parse_arguments() -> argparse.Namespace:
    """Implement parse arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stations", type=Path)
    parser.add_argument("groundwater_bodies", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--station-crs", default="EPSG:25833")
    parser.add_argument("--gwk-column", default="GWK_ID")
    parser.add_argument("--geopackage", type=Path)
    return parser.parse_args()


def main() -> None:
    """Implement main."""
    args = parse_arguments()
    stations = read_stations(args.stations, args.station_crs)
    groundwater_bodies = read_groundwater_bodies(args.groundwater_bodies)
    validate_inputs(stations, groundwater_bodies, args.gwk_column)
    result = assign_groundwater_bodies(stations, groundwater_bodies, args.gwk_column)
    write_results(result, args.output_csv, args.geopackage)
    print(f"Zuordnung geschrieben: {args.output_csv}")


if __name__ == "__main__":
    main()
