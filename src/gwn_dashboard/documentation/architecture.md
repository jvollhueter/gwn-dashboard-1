# Softwarearchitektur

## Architekturprinzip

Die Anwendung folgt einer geschichteten, objektorientierten Struktur. Jede Schicht besitzt eine klar abgegrenzte Verantwortung. Dadurch können Datenquellen, fachliche Verarbeitung, Visualisierungen und UI unabhängig getestet und erweitert werden.

```text
app.py
  ↓
StreamlitApplication
  ↓
UI pages and components
  ↓
DashboardService / ScriptLibraryService
  ↓
AggregationService / AnalysisService / ComparisonService / ExportService
  ↓
Repository interfaces
  ↓
CSV, GIS and script-library files
```

## Einstiegspunkt

`app.py` ist der einzige reguläre Einstiegspunkt der Webanwendung. Die Datei lädt die Konfiguration, erzeugt den Anwendungskontext und startet die Streamlit-Anwendung. Fachliche Berechnungen gehören nicht in den Einstiegspunkt.

## Anwendungskomposition

`gwn_dashboard.application.create_app_context` erzeugt:

- Grundwasser-Repository,
- Script-Bibliotheks-Repository,
- Aggregationsservice,
- Analyseservice,
- Vergleichsservice,
- Exportservice,
- Dashboardservice,
- Script-Bibliotheksservice,
- Diagramm- und Kartenfabriken.

Der resultierende `AppContext` wird an die UI übergeben. Dadurch sind Abhängigkeiten zentral sichtbar und austauschbar.

## Domain-Schicht

Die Domain-Schicht enthält fachliche Datenobjekte ohne Streamlit-Abhängigkeit. Dazu gehören:

- `Period`: inklusiver Jahreszeitraum,
- `DashboardData`: vorbereitete Tabellen der Anwendung,
- `SidebarSelection`: aktuelle räumliche und zeitliche Auswahl,
- `ScriptLibraryItem`: Metadaten einer Bibliotheksveröffentlichung.

Die Objekte dienen als stabile Verträge zwischen Services und Benutzeroberfläche.

## Repository-Schicht

### Grundwasser-Repository

Das Interface `GroundwaterDataRepository` definiert den erwarteten Datenzugriff. Die Implementierung `CsvGroundwaterDataRepository` liest:

- Parameterzeitreihen,
- ID-GWK-Mapping,
- GWK-Geometrien,
- Messstellenübersicht,
- Messstellen-GWK-Zuordnung.

Das Repository validiert Dateistruktur und Pflichtspalten. Fachliche Aggregationen werden nicht im Repository durchgeführt.

### Script-Bibliotheks-Repository

`ScriptLibraryRepository` durchsucht den Bibliotheksordner, erkennt unterstützte Veröffentlichungsformen, liest Metadaten und erzeugt Downloadpakete. Es importiert oder startet die gefundenen Programme nicht.

## Service-Schicht

### AggregationService

Verantwortlich für:

- Monats- zu Jahressummen,
- Berechnung `GWN = rg1 + rg2`,
- Anfügen der GWK-Kennung,
- räumliche Aggregation,
- Filterung auf ausgewählte GWK.

### AnalysisService

Berechnet deskriptive Statistik und Trends. Fehlende oder zu kurze Reihen werden kontrolliert behandelt.

### ComparisonService

Verknüpft Referenz- und Vergleichsstatistik und berechnet absolute sowie relative Änderung.

### DashboardService

Orchestriert den vollständigen Datenfluss. Er kennt die Reihenfolge der Datenaufbereitung, delegiert Berechnungen jedoch an spezialisierte Services.

### ExportService

Erzeugt CSV-, ZIP- und Excel-Inhalte im Arbeitsspeicher. Die Streamlit-Seite erhält fertige Bytes bzw. Texte und muss keine Dateiformatlogik implementieren.

### ScriptLibraryService

Stellt Suche, Filter, Detailzugriff und Downloadvorbereitung für Bibliotheksobjekte bereit.

## Visualisierungsschicht

`ChartFactory` und `MapFactory` kapseln Plotly-spezifische Logik. Sie erhalten vorbereitete Daten und erzeugen Figuren. Dadurch bleiben Seitenklassen auf Layout und Interaktion konzentriert.

## Design-Schicht

Die Design-Schicht enthält:

- semantische Farben,
- Plotly-Grundlayouts,
- globale CSS-Regeln,
- Laden der Styles.

Farbrollen werden zentral definiert, damit Diagramme und Oberfläche konsistent bleiben.

## UI-Schicht

### StreamlitApplication

Die Hauptanwendung liest die aktuelle Route, stellt gemeinsame Abhängigkeiten bereit und rendert die passende Seite.

### Komponenten

Wiederverwendbare Bestandteile sind beispielsweise:

- Kopfzeile,
- Fußnavigation,
- Kontextleiste,
- Kennzahlenpanel,
- Exportpanel,
- Auswahlsteuerung.

### Seiten

Seiten kapseln zusammenhängende Arbeitsbereiche. Direkte Dateizugriffe innerhalb einer Seite sind zu vermeiden.

## Navigation

Die Navigation verwendet Queryparameter. Wichtige Routen sind:

| Route | Bedeutung |
|---|---|
| `platform` | übergeordnete Landing-Page |
| `groundwater-data` | Landing-Page Grundwasserdaten |
| `groundwater-quantity` | Landing-Page Grundwasserquantität |
| `maps` | Kartenansicht |
| `diagrams` | Diagrammansicht |
| `nomograms` | Nomogramme |
| `export` | Datenexport |
| `groundwater-quality` | Platzhalter Grundwasserqualität |
| `meteorological-data` | Platzhalter Meteorologische Daten |
| `script-library` | Script-Bibliothek |

## Session State

Der Streamlit Session State hält UI-Zustände, darunter:

- räumlicher Auswahlmodus,
- ausgewählte GWK,
- Detail-GWK,
- Referenz- und Vergleichszeitraum,
- Messstellenmodus,
- ausgewählte Messstellen,
- ausgewählter Messstellen-GWK,
- Diagrammoptionen,
- Such- und Filterzustände der Bibliothek.

Session State ist kein dauerhafter Datenspeicher. Ein Neustart der Sitzung kann Werte zurücksetzen.

## Caching

`st.cache_data` reduziert wiederholte Dateizugriffe und Berechnungen. Cache-Schlüssel müssen alle fachlich relevanten Eingaben enthalten. Bei periodenabhängigen Berechnungen gehören alle Jahresgrenzen zum Schlüssel.

## Fehlerbehandlung

Repository- und Servicefehler werden möglichst früh erkannt. Die UI fängt erwartbare Ladefehler ab und zeigt verständliche Hinweise. Fehler dürfen nicht durch leere oder scheinbar plausible Ergebnisse verdeckt werden.
