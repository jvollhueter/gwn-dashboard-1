## Zweck

Das Werkzeug erstellt einen kompakten Kennwertbericht aus täglichen Niederschlags- und ETp-Daten.

## Eingabedaten

Die CSV-Datei benötigt die Spalten `datum`, `niederschlag_mm` und `etp_mm`.

## Ausführung

```bash
Rscript run_analysis.R examples/meteorologie.csv output
```

Im Ausgabeordner entstehen aggregierte Tabellen und eine Jahresgrafik.
