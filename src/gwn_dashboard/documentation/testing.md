# Teststrategie

## Ziel

Die Tests sichern fachliche Berechnungen, Datenzugriffe, Visualisierungsverträge, Navigation und grundlegende Startfähigkeit der Anwendung.

## Testebenen

### Unit-Tests

Prüfen isolierte Einheiten, insbesondere:

- Periodenlogik,
- Aggregation,
- GWN-Berechnung,
- Periodenstatistik,
- Trendberechnung,
- Vergleichslogik,
- Farben und Designrollen,
- Script-Metadaten und Filter,
- Kartenebenen für Messstellen.

### Integrationstests

Prüfen das Zusammenspiel mehrerer Schichten, beispielsweise `DashboardService` mit einem kontrollierten Repository oder das Laden realer Messstellenmetadaten.

### Smoke-Tests

Prüfen:

- Importierbarkeit der Module,
- Start aller Streamlit-Routen,
- Vorhandensein zentraler Seitenelemente,
- Downloadaktionen ohne Laufzeitfehler.

## Testdaten

Für fachliche Unit-Tests werden kleine synthetische Daten verwendet. Erwartete Ergebnisse müssen manuell nachvollziehbar sein. Große reale Dateien werden nur verwendet, wenn die Dateiintegration selbst geprüft werden soll.

## Periodentests

Besonders zu prüfen sind:

- inklusive Grenzen,
- Perioden mit fehlenden Jahren,
- nicht überlappende Auswahl,
- Änderung der Ergebnisse bei geänderten Zeiträumen,
- korrekte Dateinamen im Export.

## Karten- und Messstellentests

- keine Stationsebene im Modus „Keine“,
- vollständige Stationsebene im Modus „Alle“,
- korrekte Einzelwahl,
- Filterung nach `GWK25`,
- schwarze Marker,
- unveränderte GWK-Werte.

## Script-Bibliothekstests

- Parser für Python, R, Jupyter und `metadata.toml`,
- Pflichtfelder,
- doppelte IDs,
- Volltextsuche,
- kombinierte Filter,
- Einzeldatei-Download,
- ZIP-Erzeugung,
- Ausschluss unerwünschter Dateien.

## Dokumentationstests

- alle Dokumentationsmodule importierbar,
- Markdown-Dateien vorhanden,
- MkDocs-Build erfolgreich,
- öffentliche Python-Objekte besitzen Docstrings,
- Links und Bildpfade sind lokal auflösbar.
