# Daten und fachliche Methoden

## Datenbestand Grundwasserquantität

Die Anwendung verwendet lokale Monatsdaten aus `data/kalib_beo_ERA5/`. Der dokumentierte Bestand umfasst 84 Grundwasserkörper und die Jahre 1961 bis 2020.

### Verwendete Parameter

| Code | Fachliche Bedeutung | Verarbeitung |
|---|---|---|
| `rg1` | Zufluss zum schnellen Grundwasserspeicher | Monatssumme zu Jahressumme |
| `rg2` | Zufluss zum langsamen Grundwasserspeicher | Monatssumme zu Jahressumme |
| `P` | Niederschlag | Monatssumme zu Jahressumme |
| `ETp` | potenzielle Evapotranspiration | Monatssumme zu Jahressumme |

Die Standardtabellen enthalten mindestens:

- technische räumliche `id`,
- `year`,
- `month`,
- `value`.

## Mapping zu Grundwasserkörpern

Die technische ID wird über `GWK_2025.csv` einer fachlichen GWK-Kennung zugeordnet. Das Mapping wird vor den fachlichen Aggregationen geladen und validiert.

Eine fehlende Zuordnung darf nicht unbemerkt in einer räumlichen Statistik verbleiben. Nicht zugeordnete Datensätze müssen geprüft oder explizit behandelt werden.

## Grundwasserneubildung

Die jährliche Grundwasserneubildung wird berechnet als:

```text
GWN_Jahr = Summe(rg1_Monate) + Summe(rg2_Monate)
```

Die Anwendung berechnet zunächst für jeden Speicherzufluss eine Jahressumme und verbindet anschließend beide Größen über räumliche ID und Jahr.

## Räumliche Aggregation

Nach Zuordnung der GWK-Kennung werden Werte auf Ebene `GWK_ID` und Jahr aggregiert. Die Implementierung unterstützt mehrere technische IDs pro GWK. Bei genau einer ID pro GWK entspricht der aggregierte Wert dem Ausgangswert.

## Zeiträume

`Period` verwendet inklusive Grenzen. Ein Zeitraum 1961–1990 enthält somit 30 Jahre, sofern für jedes Jahr gültige Daten vorliegen.

Die UI verhindert:

- Perioden mit weniger als zwei Jahren,
- überlappende Perioden,
- einen Vergleichszeitraum vor dem Referenzzeitraum,
- Grenzen außerhalb des gemeinsamen Datenbereichs.

## Deskriptive Periodenstatistik

Für jeden GWK und Zeitraum werden berechnet:

- Mittelwert,
- Median,
- Standardabweichung,
- Minimum,
- Maximum,
- Anzahl gültiger Jahreswerte.

Die Anzahl gültiger Werte ist wichtig, da fehlende Jahre die Vergleichbarkeit beeinträchtigen können.

## Periodenvergleich

Die absolute Änderung wird berechnet als:

```text
absolute Änderung = Mittelwert_Vergleich − Mittelwert_Referenz
```

Die relative Änderung wird berechnet als:

```text
relative Änderung [%] = absolute Änderung / Mittelwert_Referenz × 100
```

Ist der Referenzmittelwert null oder nicht gültig, darf keine unendliche oder irreführende Prozentangabe erzeugt werden.

## Trendanalyse

Die Trendanalyse arbeitet auf den jährlichen Werten eines GWK. Sie umfasst:

- lineare Regressionssteigung pro Jahr,
- Achsenabschnitt,
- Pearson-Korrelationskoeffizient der linearen Regression,
- p-Wert,
- Standardfehler,
- Kendall-Tau,
- p-Wert des Kendall-Tests.

Die lineare Steigung beschreibt die mittlere Änderung pro Jahr. Ein statistischer p-Wert ersetzt keine fachliche Prüfung von Datenqualität, Autokorrelation, Strukturbrüchen oder Modellannahmen.

## Niederschlag und ETp

Niederschlag und ETp stammen im aktuellen Anwendungsbestand aus den lokalen Modelldateien. Beide Größen werden für die Darstellung zu Jahreswerten aggregiert. Sie sind von der berechneten GWN getrennte Variablen.

## GWK-Geometrien

Die Geometrien liegen in ETRS89 / UTM-Zone 33N (`EPSG:25833`) vor. Für die Webkarte werden sie nach WGS 84 (`EPSG:4326`) transformiert.

Vor Verwendung werden insbesondere geprüft:

- vorhandenes Koordinatenreferenzsystem,
- gültige GWK-Kennung,
- Geometrietyp,
- erfolgreiche Verknüpfung mit der Vergleichstabelle.

## Messstellen

### Übersicht

Die Messstellenübersicht enthält unter anderem:

- MKZ,
- Messstellenname,
- Rechts- und Hochwert,
- erstes und letztes Messdatum,
- gegebenenfalls zusammengefasste Grundwasserstandskennwerte.

### Koordinaten

Die Koordinaten werden als `EPSG:25833` interpretiert, zu Punktgeometrien verarbeitet und für Plotly nach `EPSG:4326` transformiert.

### GWK-Zuordnung

`data/MKZ_GWK.csv` enthält:

- `GWK`: ältere oder bisherige Zuordnung,
- `GWK25`: Zuordnung zum Gebietsstand GWK 2025.

Die Kartenfilterung verwendet `GWK25`. Fehlende Zuordnungen werden als nicht zugeordnet gekennzeichnet.

### Abgrenzung

Die Messstellenebene ist eine visuelle Zusatzebene. Sie beeinflusst nicht:

- GWN-Werte,
- Periodenstatistiken,
- Trendberechnungen,
- GWK-Flächenfarben.

## Datenexport

Der Export verwendet vorbereitete Tabellen aus `DashboardData`. Dadurch gelten dieselben fachlichen Regeln wie in der Oberfläche. Eine separate Neuberechnung im Exportmodul wird vermieden.

## Datenqualität und Einschränkungen

- Fehlende Werte werden nicht durch automatische fachliche Schätzungen ersetzt.
- Dateistrukturen und Pflichtspalten werden validiert.
- Die Anwendung dokumentiert verfügbare Daten, ersetzt jedoch keine fachliche Plausibilitätsprüfung.
- Modellierte GWN und gemessene Grundwasserstände sind unterschiedliche Größen.
- Vollständige Messreihen sind nicht für jede in der Übersicht enthaltene Messstelle Teil des Projekts.

## Meteorologische Daten

Der Bereich Meteorologische Daten ist eine Platzhalterseite. Es sind dort keine Datenquellen, Berechnungen oder automatischen Abrufe implementiert.
