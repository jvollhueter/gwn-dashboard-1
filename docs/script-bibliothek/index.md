# Script-Bibliothek

## Zweck

Die Script-Bibliothek stellt fachlich dokumentierte Werkzeuge zentral zum Download bereit. Veröffentlichungen werden ordnerbasiert verwaltet. Die Plattform führt keinen bereitgestellten Code aus.

## Unterstützte Formen

| Form | Metadatenquelle | Download |
|---|---|---|
| Python-Einzeldatei | kommentierter TOML-Block im Dateikopf | `.py` |
| R-Einzeldatei | kommentierter TOML-Block im Dateikopf | `.R` |
| Jupyter-Notebook | `metadata.ref43_library` | `.ipynb` |
| Mehrdateien-Werkzeug | `metadata.toml` im Stammordner | `.zip` |

## Ordnerstruktur

```text
script_library/
├── einzeldatei.py
├── analyse.R
├── notebook.ipynb
└── werkzeug/
    ├── metadata.toml
    ├── README.md
    ├── main.py oder run_analysis.R
    ├── Quellmodule
    └── examples/
```

## Metadatenmodell

Zentrale Felder sind:

- stabile `id`,
- `title`,
- `short_description`,
- `long_description`,
- `category`,
- `tags`,
- `language`,
- `version`,
- `updated`,
- `author`,
- Ein- und Ausgabeformate,
- Laufzeitanforderungen,
- Abhängigkeiten,
- Einstiegspunkt.

## Einzeldateien

Die Metadaten stehen in einem kommentierten TOML-Block am Dateianfang. Kommentare erlauben, dass die Datei in Python oder R weiterhin regulär ausgeführt werden kann.

Die Plattform liest ausschließlich den Textblock. Sie importiert die Python-Datei nicht und ruft keine R-Funktion auf.

## Jupyter-Notebooks

Notebook-Metadaten liegen im JSON-Objekt unter `metadata.ref43_library`. Der Quellcode der Zellen wird für die Katalogisierung nicht ausgeführt.

## Mehrteilige Werkzeuge

Ein Werkzeug mit mehreren Klassen oder Modulen besitzt genau einen Katalogeintrag. Die Metadaten stehen in `metadata.toml`. Der gesamte Ordner wird als ZIP bereitgestellt.

Empfohlene Bestandteile:

- `metadata.toml`,
- `README.md`,
- definierter Einstiegspunkt,
- Abhängigkeitsdatei,
- Quellmodule,
- optionale Beispieldaten.

## Tags

Tags werden strukturiert gespeichert und als Hashtags angezeigt. Empfohlen sind kontrollierte, kleingeschriebene Begriffe aus den Gruppen:

- Fachthema,
- Verarbeitungsschritt,
- Datenformat,
- räumlicher Bezug,
- Ergebnisart.

Unterschiedliche Schreibweisen desselben Begriffs sollen vermieden werden.

## Suche und Filter

Die Suche verwendet normalisierten Volltext aus Metadaten. Strukturierte Filter können gleichzeitig angewendet werden. Das Ergebnis erfüllt alle aktiven Filterbedingungen.

## Detailseite

Die Detailseite stellt alle verfügbaren Angaben dar. README-Inhalte werden ergänzend angezeigt, ersetzen jedoch nicht die strukturierten Pflichtmetadaten.

## Downloaderzeugung

### Einzeldatei

Die Originalbytes werden mit geeignetem MIME-Type und Dateinamen bereitgestellt.

### Mehrdateien-Werkzeug

Das Repository erzeugt ein ZIP im Arbeitsspeicher. Ausgeschlossen werden insbesondere:

- `.git`,
- `.venv` und andere virtuelle Umgebungen,
- `__pycache__`,
- `.pytest_cache`,
- kompilierte Dateien,
- `.env`,
- typische Zugangsdaten,
- temporäre Editor- und Betriebssystemdateien.

## Validierung

Eine Veröffentlichung gilt nur dann als gültig, wenn:

- die ID eindeutig ist,
- Pflichtfelder vorhanden und nicht leer sind,
- Sprache und Typ unterstützt werden,
- Datums- und Versionsangaben formal plausibel sind,
- bei Paketen der Einstiegspunkt existiert,
- Pfade innerhalb des Bibliotheksordners verbleiben.

## Beispielveröffentlichungen

Der Projektstand enthält Beispiele für:

- CSV-Datenprüfung mit Python,
- Grundwasserstand-Zeitreihe mit R,
- Niederschlagsaggregation mit Python,
- explorative GWN-Analyse als Jupyter-Notebook,
- Messstellen-GWK-Zuordnung als Python-Paket,
- meteorologischen Kennwertbericht als R-Paket.

Die Beispiele illustrieren Metadaten- und Paketstrukturen. Vor fachlichem Einsatz müssen Eingabedaten, Einheiten und Randbedingungen geprüft werden.
