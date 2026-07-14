"""Application configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from gwn_dashboard.domain.models import Parameter, Period


@dataclass(frozen=True)
class ApplicationSettings:
    title: str
    page_title: str
    page_icon: str
    layout: str
    initial_sidebar_state: str


@dataclass(frozen=True)
class DataPaths:
    base_directory: Path
    mapping_file: Path
    geometry_file: Path


@dataclass(frozen=True)
class DashboardConfig:
    application: ApplicationSettings
    data: DataPaths
    reference_period: Period
    comparison_period: Period
    groundwater_recharge: Parameter
    precipitation: Parameter
    potential_evapotranspiration: Parameter


def _resolve_path(project_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _parameter(raw: dict[str, Any]) -> Parameter:
    return Parameter(
        code=str(raw["code"]),
        label=str(raw["label"]),
        unit=str(raw["unit"]),
        source_codes=tuple(str(code) for code in raw.get("source_codes", [])),
    )


def load_config(project_root: Path, config_path: Path | None = None) -> DashboardConfig:
    path = config_path or project_root / "config" / "app_config.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {path}")
    with path.open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}
    app = raw["application"]
    data = raw["data"]
    periods = raw["periods"]
    parameters = raw["parameters"]
    return DashboardConfig(
        application=ApplicationSettings(
            title=str(app["title"]), page_title=str(app["page_title"]),
            page_icon=str(app["page_icon"]), layout=str(app.get("layout", "wide")),
            initial_sidebar_state=str(app.get("initial_sidebar_state", "expanded")),
        ),
        data=DataPaths(
            base_directory=_resolve_path(project_root, str(data["base_directory"])),
            mapping_file=_resolve_path(project_root, str(data["mapping_file"])),
            geometry_file=_resolve_path(project_root, str(data["geometry_file"])),
        ),
        reference_period=Period(**periods["reference"]),
        comparison_period=Period(**periods["comparison"]),
        groundwater_recharge=_parameter(parameters["groundwater_recharge"]),
        precipitation=_parameter(parameters["precipitation"]),
        potential_evapotranspiration=_parameter(parameters["potential_evapotranspiration"]),
    )
