# Plattform für Datenaufbereitung und  &#8209;visualisierung – Referat 43

Interne Streamlit-Plattform für die strukturierte Bereitstellung, Visualisierung und Aufbereitung fachlicher Daten und Werkzeuge.

## Bereiche

```text
Plattform für Datenaufbereitung und  &#8209;visualisierung
├── Grundwasserdaten
│   ├── Grundwasserquantität
│   └── Grundwasserqualität
├── Meteorologische Daten
└── Script-Bibliothek
```

### Grundwasserquantität

Der Bereich Grundwasserquantität enthält den GWN Viewer zur räumlichen und zeitlichen Analyse der Grundwasserneubildung in sächsischen Grundwasserkörpern.

Enthalten sind:

- Karten für Referenzwert, Vergleichswert sowie absolute und relative GWN-Änderung
- Messstellenebene mit den Modi „Keine“, „Alle“, „Einzelne Auswahl“ und „Messstellen eines GWK“
- Zeitreihen für GWN mit zuschaltbarem Niederschlag und potenzieller Evapotranspiration
- frei wählbare, nicht überlappende Referenz- und Vergleichszeiträume
- Trend- und Periodenstatistiken
- explorative Beziehung zwischen GWN und Niederschlag
- CSV-, ZIP- und Excel-Exporte

### Grundwasserqualität

Für diesen Bereich sind derzeit noch keine Inhalte hinterlegt.

### Meteorologische Daten

Für diesen Bereich sind derzeit noch keine Inhalte hinterlegt.

### Script-Bibliothek

Die Script-Bibliothek stellt Python-, R- und Jupyter-Werkzeuge bereit. Enthalten sind:

- Volltextsuche über Titel, Beschreibungen, Kategorien, Tags und technische Angaben
- Filter nach Kategorie, Sprache, Bereitstellungsform und Tags
- Kurzbeschreibungen in der Ergebnisübersicht
- eigene Detailseiten mit Langbeschreibung, Abhängigkeiten sowie Ein- und Ausgabeformaten
- direkter Download einzelner Dateien oder vollständiger Werkzeug-Pakete als ZIP
- Metadaten direkt im Kopf einzelner Python- und R-Skripte
- Notebook-Metadaten für Jupyter-Dateien
- `metadata.toml` für mehrteilige Werkzeuge

Neue Veröffentlichungen werden ausschließlich über den Ordner `script_library/` bereitgestellt. Die Plattform liest die Metadaten, importiert oder startet die enthaltenen Programme jedoch nicht.

## Navigation

Die zentrale Landingpage führt zu den drei fachlichen Hauptbereichen. Der Bereich Grundwasserdaten enthält separate Zugänge zu Grundwasserquantität und Grundwasserqualität.

Im GWN Viewer führt der linke Titel zur Landingpage der Grundwasserquantität. Der Link „Home“ führt zur zentralen Plattform-Landingpage.

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

## Tests

```powershell
python -m pytest -v
```

## Projektstruktur

```text
app.py
config/
  app_config.yaml
src/gwn_dashboard/
  application.py
  config.py
  design/
  domain/
  repositories/
  services/
    script_library_service.py
  visualization/
  ui/
    application.py
    navigation.py
    assets/
      landing_background.jpg
      icons/
    components/
      app_header.py
      bottom_navigation.py
      viewer_controls.py
    pages/
      landing_page.py
      script_library_page.py
      map_page.py
      diagram_page.py
      nomogram_page.py
      export_page.py
      information_page.py
script_library/
  einzelne Skripte und Notebooks
  Werkzeugordner mit metadata.toml
tests/
  unit/
  integration/
  smoke/
```

## Rechtliche Inhalte

Die Informationsseite enthält vorgesehene Bereiche für Kontakt, Impressum und Datenschutz. Verbindliche Inhalte sind vor der Bereitstellung durch die zuständigen Stellen festzulegen.

## Lokale Dokumentation

Die Projektdokumentation kombiniert deutschsprachige fachliche Seiten und Benutzerhinweise mit einer automatisch aus englischen Google-Docstrings erzeugten API-Referenz.

```powershell
python scripts/build_docs.py
```

Die HTML-Dokumentation wird unter `docs_build/` erzeugt. Die fachlichen Quelldateien liegen unter `docs/`; die API-Referenz wird aus den Docstrings unter `src/gwn_dashboard/` erzeugt.

Lokaler Dokumentationsserver:

```powershell
python -m mkdocs serve
```
