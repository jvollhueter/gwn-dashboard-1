# GWN Viewer – Grundwasserneubildung Sachsen

Interaktive Streamlit-Anwendung zur räumlichen und zeitlichen Analyse der Grundwasserneubildung in sächsischen Grundwasserkörpern.

## Oberfläche

Die Oberfläche wurde anhand der bereitgestellten Screenshots des GWN-Viewers neu aufgebaut. Enthalten sind:

- eigene Landingpage mit Hintergrundbild und vier Modulkarten
- feste dunkelgrüne Kopfzeile mit „GWN Viewer | Interne Plattform Referat 43“ und ausschließlich dem Link „Home“
- feste dunkelgrüne Modulnavigation am unteren Fensterrand
- Kartenmodul mit linker Parameterauswahl, großer Kartenfläche und rechter Statistikspalte
- Diagrammmodul mit linker Steuerfläche und großer Ergebnisfläche
- Diagrammtypen Zeitreihen, Periodenvergleich und Statistiken
- Nomogramm-Modul auf Basis der vorhandenen Korrelationsanalyse
- formularartig aufgebauter Datenexport
- Informationsseite mit vorgesehenen Bereichen für Kontakt, Impressum und Datenschutz

Die Gestaltung orientiert sich möglichst eng an den gelieferten Referenzbildern. Die fachliche Berechnungslogik bleibt davon getrennt.

## Funktionen

- Karten für Referenzwert, Vergleichswert sowie absolute und relative GWN-Änderung
- Zeitreihen für GWN mit unabhängig zuschaltbarem Niederschlag und ETp
- Periodenvergleich 1961–1990 gegenüber 1991–2020
- Trend- und Periodenstatistiken
- explorative Beziehung zwischen GWN und Niederschlag
- Excel-Export oder ZIP-Archiv mit ausgewählten CSV-Dateien sowie die vier Direktexporte der vorherigen Oberfläche

## Installation

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

## Start

```powershell
python -m streamlit run app.py
```

Die Anwendung startet auf der Landingpage. Die Module werden über die Kacheln oder die untere Navigation geöffnet.

## Tests

```powershell
python -m pytest -v
```

Die Tests prüfen die fachlichen Services, das zentrale Farbsystem, die Navigation, die Landingpage-Assets, alle Streamlit-Routen und die Übernahme der bisherigen Diagramm-, Karten- und Exportfunktionen. Eine vollständige Zuordnung steht in `docs/FUNCTIONAL_COMPATIBILITY.md`.

## Projektstruktur

```text
app.py
config/
  app_config.yaml
src/gwn_dashboard/
  application.py
  config.py
  design/
    theme.py
    plotly_theme.py
    style_loader.py
    styles.css
  domain/
  repositories/
  services/
  visualization/
  ui/
    application.py
    navigation.py
    assets/
      landing_background.jpg
    components/
      app_header.py
      bottom_navigation.py
      viewer_controls.py
    pages/
      landing_page.py
      map_page.py
      diagram_page.py
      nomogram_page.py
      export_page.py
      information_page.py
tests/
  unit/
  integration/
  smoke/
```

## Rechtliche Inhalte

Die Bereiche Kontakt, Impressum und Datenschutzerklärung sind technisch vorbereitet, enthalten aber bewusst noch keine verbindlichen Rechtstexte. Vor einer öffentlichen Bereitstellung müssen dort die vom LfULG freigegebenen Inhalte ergänzt werden.
