## Zweck

Das Werkzeug ordnet Punktkoordinaten von Grundwassermessstellen räumlich Grundwasserkörpern zu.

## Eingabedaten

Die Messstellen-CSV benötigt die Spalten `station_id`, `easting` und `northing`. Die Flächendatei benötigt ein Attribut mit der GWK-Kennung.

## Ausführung

```bash
python main.py examples/messstellen.csv examples/gwk.geojson ergebnis.csv --station-crs EPSG:25833 --gwk-column GWK_ID
```

Für eine GeoPackage-Ausgabe kann zusätzlich `--geopackage ergebnis.gpkg` angegeben werden.
