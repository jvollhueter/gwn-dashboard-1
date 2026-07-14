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
```

Die Architektur trennt fachliche Modelle, Datenzugriff, Berechnungen, Visualisierung und Streamlit-Oberfläche. Die GUI greift ausschließlich über den `DashboardService` auf die Datenverarbeitung zu.
