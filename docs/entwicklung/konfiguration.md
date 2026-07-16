# Konfiguration und Dateipfade

## Zentrale Konfiguration

`config/app_config.yaml` enthält die veränderlichen Anwendungseinstellungen. Der Quellcode soll keine alternativen fest codierten Datenpfade einführen.

## Typisierte Konfigurationsobjekte

`gwn_dashboard.config` überführt YAML-Werte in:

- `ApplicationSettings`,
- `DataPaths`,
- `DashboardConfig`.

Dadurch werden fehlende oder falsch strukturierte Einstellungen früh erkannt.

## Pfadauflösung

Relative Pfade werden vom Projektstamm aus aufgelöst. Die Anwendung muss unabhängig vom aktuellen Arbeitsverzeichnis gestartet werden können, sofern der Projektstamm korrekt bestimmt wurde.

## Relevante Pfadgruppen

- Monatsdaten der Modellparameter,
- GWK-Mapping,
- GWK-Geometrien,
- Messstellenübersicht,
- Messstellen-GWK-Zuordnung,
- Script-Bibliothek,
- CSS- und Bildassets.

## Streamlit-Konfiguration

`.streamlit/config.toml` definiert Grundfarben, Hintergrund, Schrift und Telemetrieeinstellungen. Detaillierte Viewer-Stile befinden sich im CSS der Design-Schicht.

## Abhängigkeiten

- `requirements.txt`: Laufzeitabhängigkeiten,
- `requirements-dev.txt`: Test- und Dokumentationswerkzeuge,
- `pyproject.toml`: Projekt- und Testkonfiguration,
- `runtime.txt`: gewünschte Python-Laufzeit für unterstützende Hostingumgebungen.

## Konfigurationsänderungen prüfen

Nach einer Änderung sind mindestens auszuführen:

```powershell
python -m pytest -v
python scripts\build_docs.py
python -m streamlit run app.py
```
