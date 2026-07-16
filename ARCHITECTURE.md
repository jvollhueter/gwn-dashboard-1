# Architektur

Die Plattform verbindet eine mehrstufige Navigation mit einer geschichteten Facharchitektur für die Grundwasserquantität.

```text
Zentrale Plattform-Landingpage
├── Grundwasserdaten
│   ├── Grundwasserquantität
│   │   └── GWN Viewer
│   └── Grundwasserqualität
├── Meteorologische Daten
└── Script-Bibliothek
```

## Fachliche Schichten der Grundwasserquantität

```text
GWN Viewer
    ↓
StreamlitApplication
    ↓
DashboardService
    ↓
AggregationService / AnalysisService / ComparisonService
    ↓
GroundwaterDataRepository
    ↓
CSV- und Geodaten
```

- `domain`: fachliche Datenobjekte
- `repositories`: Datenzugriff auf CSV, Geodaten und Script-Metadaten
- `services`: Aggregation, Statistik, Vergleich und Export
- `visualization`: Plotly-Diagramme und Karten
- `design`: Farben, CSS und Plotly-Grundlayout
- `ui`: Navigation, Landingpages, Steuerelemente und Fachmodule

## Navigation

Die Navigation verwendet URL-Queryparameter:

```text
?view=platform              Zentrale Plattform-Landingpage
?view=groundwater-data      Landingpage Grundwasserdaten
?view=groundwater-quantity  Landingpage Grundwasserquantität
?view=groundwater-quality   Grundwasserqualität
?view=meteorological-data   Meteorologische Daten
?view=script-library        Script-Bibliothek und Werkzeugdetails
?view=maps                  Karten
?view=diagrams              Diagramme und Statistiken
?view=nomograms             Nomogramme und Korrelation
?view=export                Datenexport
?view=information           Information
```

## Kopfzeile

In der Plattform- und Bereichsnavigation zeigt die Kopfzeile:

```text
Plattform für Datenaufbereitung und  &#8209;visualisierung | Interne Plattform Referat 43
```

Im Bereich Grundwasserquantität zeigt die Kopfzeile:

```text
GWN Viewer | Interne Plattform Referat 43
```

Der linke Titel führt dort zur Landingpage der Grundwasserquantität. „Home“ führt zur zentralen Plattform-Landingpage.

## UI-Komposition

```text
AppHeader
    routeabhängige Kopfzeile und Home-Link

PlatformLandingPage
    drei Hauptbereiche

GroundwaterDataLandingPage
    Grundwasserquantität und Grundwasserqualität

LandingPage
    Karten, Diagramme, Nomogramme und Export der Grundwasserquantität

PlaceholderLandingPage
    sachliche Statusseite für Bereiche ohne hinterlegte Inhalte

ScriptLibraryPage
    Suche, Filter, Ergebnisübersicht, Detaildarstellung und Downloads

ScriptLibraryService
    Volltextsuche, Metadatenfilterung und ZIP-Erzeugung

ScriptLibraryRepository
    Einlesen von Python-, R-, Jupyter- und Paketmetadaten

ViewerControls
    Raum- und Detailauswahl sowie Referenz- und Vergleichszeitraum

MapPage
    Parameterleiste | Kartenfläche | Statistikleiste

DiagramPage
    Steuerleiste | Zeitreihe, Periodenvergleich oder Statistik

NomogramPage
    Modell- und Raumfilter | Korrelationsdiagramm

ExportPage
    Datenauswahl und Download

BottomNavigation
    Modulnavigation der Grundwasserquantität
```

Die UI greift nicht direkt auf Fachdaten zu. Datenzugriff und Berechnung erfolgen über den `DashboardService`.


## Veröffentlichungsformen der Script-Bibliothek

```text
script_library/
├── einzelnes_werkzeug.py       Metadatenblock im Dateikopf
├── einzelnes_werkzeug.R        Metadatenblock im Dateikopf
├── analyse.ipynb               metadata.ref43_library
└── mehrteiliges_werkzeug/
    ├── metadata.toml
    ├── README.md
    ├── Einstiegspunkt
    └── weitere Projektdateien
```

Die Plattform führt Bibliotheksinhalte nicht aus. Mehrteilige Werkzeuge werden für den Download dynamisch als ZIP-Datei zusammengestellt; Cache-, Umgebungs- und Zugangsdaten werden ausgeschlossen.
