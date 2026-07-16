# Betrieb und Wartung

## Regulärer Start

```powershell
python -m streamlit run app.py
```

## Regulärer Dokumentationsbuild

```powershell
python scripts\build_docs.py
```

## Aktualisierung der Modelldaten

1. neue Dateien außerhalb des produktiven Ordners prüfen,
2. Spalten, Zeitbereich und IDs vergleichen,
3. Sicherung des vorhandenen Datenbestands erstellen,
4. Dateien im konfigurierten Ordner ersetzen oder ergänzen,
5. Tests ausführen,
6. Cache leeren oder Anwendung neu starten,
7. Stichproben in Karte, Diagramm und Export vergleichen.

## Aktualisierung der Messstellen

Zu prüfen sind:

- eindeutige MKZ,
- numerische Koordinaten,
- korrektes CRS,
- gültige GWK25-Zuordnung,
- Anzahl zugeordneter und nicht zugeordneter Stationen,
- Kartenpositionen anhand von Stichproben.

## Veröffentlichung eines Bibliothekswerkzeugs

1. Datei oder Werkzeugordner unter `script_library/` ablegen,
2. Metadaten validieren,
3. README und Abhängigkeiten prüfen,
4. sicherstellen, dass keine Zugangsdaten enthalten sind,
5. Tests ausführen,
6. Darstellung und Download in der Plattform kontrollieren.

## Fehlerdiagnose

### Anwendung startet nicht

- virtuelle Umgebung aktiviert?
- Abhängigkeiten installiert?
- Start im Projektordner?
- YAML syntaktisch gültig?

### Daten fehlen

- Pfad in `app_config.yaml` korrekt?
- erwartete Datei vorhanden?
- Pflichtspalten vorhanden?
- Parametercode stimmt mit Ordnernamen überein?

### Karte bleibt leer

- Geometriedateien vollständig?
- CRS definiert?
- GWK-Kennung in Geometrie und Vergleichstabelle identisch?

### Bibliothekseintrag fehlt

- Metadatenblock korrekt begrenzt?
- Pflichtfelder vorhanden?
- ID eindeutig?
- Dateityp unterstützt?

## Sicherungen

Vor Austausch von Daten oder strukturellen Änderungen sollte der vollständige Projektordner gesichert oder über Versionsverwaltung nachvollziehbar gespeichert werden. Rohdaten und erzeugte Exporte sind getrennt zu behandeln.
