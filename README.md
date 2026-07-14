# 💧 GWN Dashboard – Grundwasserneubildung Sachsen

Interaktives Streamlit-Dashboard zur Analyse der Grundwasserneubildung in sächsischen Grundwasserkörpern.

## Funktionen

- Zeitreihenanalyse der Grundwasserneubildung
- Vergleich der Perioden 1961–1990 und 1991–2020
- Korrelationsdarstellung mit Niederschlag
- Trendstatistiken
- interaktive GWK-Karte
- CSV- und Excel-Export

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

## Projektstruktur

```text
app.py
config/
  app_config.yaml
src/gwn_dashboard/
  application.py
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
