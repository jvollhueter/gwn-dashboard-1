# Entwicklung, Installation und Betrieb

## Systemvoraussetzungen

- Python 3.12,
- pip,
- Zugriff auf den vollständigen Projektordner,
- Webbrowser,
- ausreichender Speicher für Geo- und Modelldaten.

## Virtuelle Umgebung

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Anwendung starten

```powershell
python -m streamlit run app.py
```

## Konfiguration

Die zentrale Konfiguration befindet sich in `config/app_config.yaml`. Pfade werden relativ zum Projektstamm interpretiert. Änderungen an Datenpfaden müssen mit der realen Ordnerstruktur übereinstimmen.

## Tests ausführen

```powershell
python -m pytest -v
```

Gezielte Auswahl:

```powershell
python -m pytest tests\unit -v
python -m pytest tests\integration -v
python -m pytest tests\smoke -v
```

## Dokumentation erzeugen

```powershell
python scripts\build_docs.py
```

Die HTML-Dateien werden unter `docs_build/` erzeugt.

## Dokumentation als lokaler Server

```powershell
python -m mkdocs serve
```

## Docstring-Konvention

Code-Docstrings sind englisch und folgen dem Google-Format. Öffentliche Module, Klassen, Methoden und Funktionen erhalten mindestens:

- prägnante Zusammenfassung,
- Argumentbeschreibung,
- Rückgabewert,
- relevante Fehler,
- fachliche Hinweise,
- Beispiel, wenn die Verwendung nicht unmittelbar ersichtlich ist.

Private Hilfsfunktionen werden dokumentiert, wenn ihre Logik fachlich relevant oder nicht selbsterklärend ist.

## Regeln für Änderungen

### Neue Datenquelle

1. Repository-Interface prüfen oder erweitern.
2. Konkrete Repository-Implementierung anlegen.
3. Datenvalidierung im Repository durchführen.
4. Fachliche Verarbeitung in einem Service implementieren.
5. Tests für gültige und fehlerhafte Eingaben ergänzen.
6. UI nur an vorbereitete Domain-Daten anbinden.
7. Dokumentation der Datenquelle und Methode ergänzen.

### Neue Auswertung

1. Fachliche Definition schriftlich festlegen.
2. Service-Methode mit typisiertem Vertrag implementieren.
3. Unit-Tests mit kontrollierten Beispieldaten schreiben.
4. Visualisierung in ChartFactory oder MapFactory ergänzen.
5. UI-Komponente oder Seite anbinden.
6. Exportauswirkungen prüfen.
7. Benutzer- und Methodendokumentation ergänzen.

### Neue Seite

1. Route in `ui/navigation.py` definieren.
2. Seitenklasse unter `ui/pages/` anlegen.
3. gemeinsame Komponenten wiederverwenden.
4. Route in `StreamlitApplication` anbinden.
5. Navigationselement mit funktionierendem Link ergänzen.
6. Smoke-Test der Route hinzufügen.

### Neue Script-Veröffentlichung

1. unterstützte Struktur wählen,
2. Metadaten vollständig eintragen,
3. README für mehrteilige Werkzeuge ergänzen,
4. Abhängigkeiten dokumentieren,
5. lokal ausführen und prüfen,
6. Bibliothekstests ausführen.

## Typisierung

Öffentliche Schnittstellen sollen Typannotationen besitzen. Pandas- und GeoPandas-Tabellen werden zusätzlich durch dokumentierte Spaltenschemata beschrieben, da der DataFrame-Typ allein keine fachliche Struktur ausdrückt.

## Fehlerbehandlung

- Fehler nicht pauschal unterdrücken.
- Fehlertexte für Nutzer fachlich verständlich formulieren.
- technische Details in Tests und Logs nachvollziehbar halten.
- keine scheinbar gültigen Ersatzwerte erzeugen, wenn Eingangsdaten fehlen.

## Performance

- wiederholte Dateizugriffe cachen,
- große Tabellen nur einmal transformieren,
- Filter früh anwenden,
- keine externen Downloads im normalen Seitenrendering durchführen,
- ZIP- und Excel-Erzeugung nur bei Bedarf ausführen.

## Sicherheit

- Script-Bibliothekscode niemals automatisch importieren oder ausführen,
- Dateipfade auf den erlaubten Projektbereich beschränken,
- keine Zugangsdaten in Repository oder ZIP-Pakete aufnehmen,
- Nutzereingaben nicht als Dateipfad oder Python-Code interpretieren,
- HTML-Ausgabe nur aus kontrollierten Anwendungswerten erzeugen oder escapen.

## Betrieb und Datenpflege

Die Anwendung liest lokale Dateien. Bei Austausch oder Ergänzung von Daten ist zu prüfen:

- Dateinamen und Pfade,
- Spaltenstruktur,
- Datentypen,
- Zeitbereich,
- GWK-Mapping,
- Koordinatenreferenzsystem,
- Cache-Aktualisierung,
- Auswirkungen auf Tests und Dokumentation.
