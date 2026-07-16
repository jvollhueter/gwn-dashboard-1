# Referenz der Projektdateien

## Projektwurzel

| Datei | Aufgabe |
|---|---|
| `app.py` | Einstiegspunkt der Streamlit-Anwendung |
| `README.md` | kompakte Projektübersicht und Startanleitung |
| `ARCHITECTURE.md` | zusammenfassende Architekturinformation |
| `mkdocs.yml` | Navigation, Theme und Build-Konfiguration der Dokumentation |
| `pyproject.toml` | Projekt-, pytest- und Werkzeugkonfiguration |
| `requirements.txt` | Laufzeitabhängigkeiten |
| `requirements-dev.txt` | Entwicklungs-, Test- und Dokumentationsabhängigkeiten |
| `runtime.txt` | Python-Laufzeitangabe |

## Konfiguration

| Pfad | Aufgabe |
|---|---|
| `config/app_config.yaml` | Datenpfade, Perioden und Anwendungseinstellungen |
| `.streamlit/config.toml` | Streamlit-Theme und Laufzeiteinstellungen |

## Quellcodepaket

### `domain`

Fachliche Datenobjekte für Perioden, Auswahlsituation, Dashboardtabellen und Script-Metadaten.

### `repositories`

Dateisystemzugriff und Parser für Grundwasser- und Bibliotheksdaten.

### `services`

Fachliche Berechnungen, Suche und Exporterzeugung.

### `visualization`

Plotly-Figuren und Karten.

### `design`

Farben, CSS und Layoutgrundlagen.

### `ui`

Routing, Seiten, Komponenten und Interaktion.

### `documentation`

Manuelle deutschsprachige Dokumentationsseiten für MkDocs Material.

## Datenordner

| Pfad | Inhalt |
|---|---|
| `data/kalib_beo_ERA5/` | modellierte Monatsdaten und GWK-Geometrien |
| `data/MKZ_GWK.csv` | Messstellen-GWK-Zuordnung |
| `cache/Export_MKZ_Uebersicht.csv` | Messstellenübersicht mit Koordinaten und Metadaten |
| `cache/ExportSN_GWS-Rohdaten_*.csv` | vorhandene Grundwasserstands-Rohdaten einzelner Stationen |

## Script-Bibliothek

`script_library/` enthält Einzeldateien und Werkzeugordner. Die Dateien sind Downloadinhalte und kein automatisch ausgeführter Bestandteil der Webanwendung.

## Tests

| Ordner | Schwerpunkt |
|---|---|
| `tests/unit/` | isolierte Fach- und Komponentenlogik |
| `tests/integration/` | Zusammenspiel von Repository und Services |
| `tests/smoke/` | Imports und Streamlit-Routen |

## Dokumentationsausgabe

`docs_build/` enthält die statische HTML-Ausgabe. Dieser Ordner kann mit `scripts/build_docs.py` neu erzeugt werden.
