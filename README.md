# 💧 GWN Dashboard – Grundwasserneubildung Sachsen

Interaktives Streamlit-Dashboard zur Analyse der Grundwasserneubildung in sächsischen Grundwasserkörpern.

## Funktionen

- Zeitreihenanalyse der Grundwasserneubildung
- Vergleich der Perioden 1961–1990 und 1991–2020
- Korrelationsdarstellung mit Niederschlag
- Trendstatistiken
- interaktive GWK-Karte
- CSV- und Excel-Export
- zentrales, am GWN-Sachsen-Viewer orientiertes Farbsystem für Oberfläche, Diagramme und Karte

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Start

```bash
streamlit run app.py
```

`app.py` ist der einzige Einstiegspunkt der Anwendung.

## Tests

Die Entwicklungsabhängigkeiten einschließlich `pytest` werden mit folgendem Befehl installiert:

```bash
python -m pip install -r requirements-dev.txt
```

Alle Tests ausführen:

```bash
python -m pytest -v
```

Nur Unit-Tests ausführen:

```bash
python -m pytest tests/unit -v
```

Nur den Service-Integrationstest ausführen:

```bash
python -m pytest -m integration -v
```

Die aktuelle Basissuite prüft Periodenmodelle, zeitliche Aggregation, die komponentenweise GWN-Berechnung aus `rg1` und `rg2`, Mapping und GWK-Filterung, Perioden- und Trendstatistiken, Periodenvergleiche sowie den vollständigen Service-Datenfluss mit einem kurzen synthetischen Datensatz. Fachlich noch nicht abschließend festgelegte Regeln zu unvollständigen Jahren, fehlenden GWN-Komponenten und zur räumlichen Gewichtung werden bewusst noch nicht als erwartetes Verhalten festgeschrieben.


## Farbschema und Designsystem

Das Farbschema wird zentral unter `src/gwn_dashboard/design/` verwaltet:

- `theme.py`: semantische Farbrollen für Branding, Fachdaten und Ergebnisse
- `plotly_theme.py`: gemeinsames Layout für Plotly-Diagramme und Karten
- `styles.css`: globale Streamlit-Oberflächenstile
- `style_loader.py`: Laden des zentralen Stylesheets

Die Grundfarben des Streamlit-Themes stehen zusätzlich in `.streamlit/config.toml`. Änderungen an den Brand-Farben müssen deshalb in `theme.py`, `styles.css` und `.streamlit/config.toml` gemeinsam vorgenommen werden.

Das aktuelle Farbschema ist aus dem bereitgestellten Screenshot des GWN-Sachsen-Viewers abgeleitet. Übernommen werden ausschließlich die Farbwirkung und die zentralen Farbfamilien: Dunkelgrün (`#337E33`), Weiß, Hellgrau, Blau (`#007BFF`) und ein gedämpftes Rot (`#F45B5B`). Aufbau, Navigation und Funktionen des Viewers werden nicht kopiert. Die Werte werden nicht als offizieller LfULG-Corporate-Design-Leitfaden ausgegeben.

Die Farbrollen sind bewusst getrennt:

- Dunkelgrün: Identität, Navigation und aktive Elemente
- Blau: Grundwasserneubildung und Niederschlag
- Gedämpftes Rot: potenzielle Evapotranspiration und Rückgänge
- Grün: Zunahmen
- Grau: Referenzperiode und neutrale Zustände

## Projektstruktur

```text
app.py
config/
  app_config.yaml
src/gwn_dashboard/
  application.py
  design/
    theme.py
    plotly_theme.py
    style_loader.py
    styles.css
  config.py
  domain/
  repositories/
  services/
  visualization/
  ui/
    components/
    pages/
tests/
  unit/
  integration/
  smoke/
```

Die Architektur trennt fachliche Modelle, Datenzugriff, Berechnungen, Visualisierung und Streamlit-Oberfläche. Die GUI greift ausschließlich über den `DashboardService` auf die Datenverarbeitung zu.
