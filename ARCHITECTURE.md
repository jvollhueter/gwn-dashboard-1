# Architektur

Das Dashboard verwendet eine geschichtete, objektorientierte Architektur:

```text
Streamlit UI
    ↓
DashboardService
    ↓
AggregationService / AnalysisService / ComparisonService
    ↓
GroundwaterDataRepository
    ↓
CSV- und Geodaten
```

## Schichten

- `domain`: fachliche Datenobjekte wie `Period`, `Parameter` und `DashboardData`
- `repositories`: austauschbarer Datenzugriff; aktuell CSV und Shapefile
- `services`: Aggregation, Statistik, Periodenvergleich und Export
- `visualization`: Plotly-Diagramme und Karten ohne Streamlit-Abhängigkeit
- `ui`: Streamlit-Anwendung, Komponenten und eigenständige Seitenklassen

`app.py` ist der einzige Startpunkt. Die GUI greift nicht direkt auf Dateien oder Berechnungsfunktionen zu, sondern ausschließlich über den `DashboardService`.
