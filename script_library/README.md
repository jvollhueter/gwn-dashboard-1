# Veröffentlichung in der Script-Bibliothek

Die Plattform liest Veröffentlichungen direkt aus diesem Ordner. Die Dateien werden für die Kataloganzeige weder importiert noch ausgeführt.

## Einzelnes Python-Skript

Im Kopf der Datei steht ein TOML-Block:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["pandas>=2.2"]
#
# [tool.ref43_library]
# id = "eindeutige-script-id"
# title = "Titel"
# short_description = "Kurze Beschreibung für die Ergebnisliste."
# long_description = """
# Ausführliche Beschreibung für die Detailseite.
# """
# category = "Grundwasserquantität"
# tags = ["messstellen", "zeitreihe"]
# author = "Referat 43"
# version = "1.0.0"
# updated = "2026-07-16"
# language = "Python"
# input_formats = ["CSV"]
# output_formats = ["XLSX"]
# ///
```

## Einzelnes R-Skript

R verwendet das gleiche Metadatenschema mit dem Marker `ref43-script`:

```r
# /// ref43-script
# requires-r = ">=4.2"
# dependencies = []
#
# [tool.ref43_library]
# id = "eindeutige-script-id"
# title = "Titel"
# short_description = "Kurze Beschreibung für die Ergebnisliste."
# long_description = "Ausführliche Beschreibung für die Detailseite."
# category = "Meteorologische Daten"
# tags = ["niederschlag", "aggregation"]
# author = "Referat 43"
# version = "1.0.0"
# updated = "2026-07-16"
# language = "R"
# input_formats = ["CSV"]
# output_formats = ["CSV", "PNG"]
# ///
```

## Jupyter-Notebook

Die Bibliotheksdaten stehen im Notebook unter `metadata.ref43_library`. Die Feldnamen entsprechen den Angaben der Einzeldateien. Die Sprache lautet `Jupyter`.

## Mehrteiliges Werkzeug

Ein mehrteiliges Werkzeug erhält einen eigenen Ordner:

```text
werkzeugname/
├── metadata.toml
├── README.md
├── Einstiegspunkt
└── weitere Projektdateien
```

Die `metadata.toml` enthält eine Tabelle `[library]` mit den gleichen Pflichtfeldern. Zusätzlich ist `entry_point` erforderlich. Der vollständige Ordner wird beim Download als ZIP-Datei bereitgestellt.

## Pflichtfelder

- `id`
- `title`
- `short_description`
- `long_description`
- `category`
- `tags`
- `author`
- `version`
- `updated`

Zulässige Sprachen sind `Python`, `R` und `Jupyter`. Die ID besteht aus Kleinbuchstaben, Zahlen und Bindestrichen. Das Datum wird im Format `JJJJ-MM-TT` angegeben.

## Nicht bereitgestellte Dateien

Bei Werkzeug-Paketen werden unter anderem folgende Inhalte ausgeschlossen:

- `.git/`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.env`
- `credentials.json`
- kompilierte Python-Dateien
