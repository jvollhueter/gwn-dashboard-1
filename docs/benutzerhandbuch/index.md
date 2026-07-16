# Benutzerhandbuch

## Anwendung starten

Nach Installation der Abhängigkeiten wird die Anwendung im Projektverzeichnis gestartet:

```powershell
python -m streamlit run app.py
```

Streamlit zeigt anschließend eine lokale URL an. Die Anwendung wird über einen Webbrowser bedient.

## Übergeordnete Landing-Page

Die übergeordnete Landing-Page bietet drei Einstiege:

- **Grundwasserdaten**
- **Meteorologische Daten**
- **Script-Bibliothek**

Die Kacheln sind vollständig anklickbar. Die Kopfzeile zeigt den Namen der Plattform und einen Home-Link. Innerhalb der Grundwasserquantität führt **Home** zurück zur übergeordneten Landing-Page.

## Grundwasserdaten

Die Landing-Page Grundwasserdaten unterscheidet:

- **Grundwasserquantität:** bestehender GWN Viewer,
- **Grundwasserqualität:** Platzhalterseite ohne fachliche Inhalte.

## Grundwasserquantität

### Räumliche Auswahl

Die Auswahl kann auf alle vorhandenen Grundwasserkörper oder auf eine eigene Teilmenge beschränkt werden. Zusätzlich wird ein **Detail-GWK** festgelegt. Dieser wird für Einzelzeitreihen, Kennzahlen und explorative Diagramme verwendet.

Eine Mehrfachauswahl beeinflusst aggregierte Tabellen und Karten. Der Detail-GWK muss nicht als hierarchisch untergeordnete Einheit interpretiert werden; er bezeichnet lediglich die für Detailansichten gewählte Einheit.

### Referenz- und Vergleichszeitraum

Zwei Bereichs-Schieberegler legen die Zeiträume fest. Beide Grenzen werden eingeschlossen.

Gültigkeitsregeln:

- jede Periode umfasst mindestens zwei Jahre,
- Referenz- und Vergleichsperiode überschneiden sich nicht,
- der Referenzzeitraum liegt vor dem Vergleichszeitraum,
- die Grenzen liegen innerhalb des gemeinsamen Datenzeitraums.

Die Auswahl wirkt auf Karten, Kennzahlen, Diagramme, statistische Vergleiche und periodengebundene Exporte.

## Kartenansicht

### Parameter

Die Karte kann unterschiedliche Größen darstellen, insbesondere:

- mittlere GWN im Referenzzeitraum,
- mittlere GWN im Vergleichszeitraum,
- absolute Änderung in `mm/a`,
- relative Änderung in Prozent.

### Interaktion

Die Plotly-Werkzeugleiste ermöglicht Zoom, Verschieben, Zurücksetzen und Bildexport. Beim Überfahren einer GWK-Fläche werden die zugehörigen Werte angezeigt.

### Messstellen

Die Messstellenebene bietet vier Modi:

1. **Keine:** keine Punkte werden angezeigt.
2. **Alle:** alle vorhandenen Messstellen werden dargestellt.
3. **Einzelne Auswahl:** eine oder mehrere Messstellen werden anhand Name oder MKZ ausgewählt.
4. **Messstellen eines GWK:** alle über `GWK25` zugeordneten Messstellen eines ausgewählten GWK werden angezeigt.

Messstellen erscheinen als schwarze Punkte. Ihre Darstellung verändert weder GWN-Berechnungen noch Auswahlstatistiken der Flächen.

Der Tooltip enthält – soweit vorhanden – Messstellenname, MKZ, Messzeitraum und GWK-2025-Zuordnung.

## Diagrammansicht

Die Diagrammansicht kombiniert mehrere Auswertungen.

### Zeitreihe

Dargestellt wird die jährliche GWN des Detail-GWK. Optional können Niederschlag und ETp eingeblendet werden. Die drei Größen verwenden klar unterscheidbare Farben.

Referenz- und Vergleichsperioden werden visuell markiert. Periodenmittelwerte werden als zusätzliche Orientierung dargestellt.

### Vergleich

Der Periodenvergleich zeigt die Ergebnisse der ausgewählten GWK. Absolute und relative Änderung werden auf Basis der Mittelwerte beider Perioden berechnet.

### Statistische Auswertungen

Je nach Ansicht sind verfügbar:

- Mittelwert,
- Median,
- Minimum und Maximum,
- Standardabweichung,
- lineare Trendsteigung,
- Korrelationskoeffizient,
- p-Wert,
- Kendall-Tau,
- Histogramme und Boxplots.

## Nomogramme

Die Nomogrammseite visualisiert die Beziehung zwischen jährlicher Grundwasserneubildung und Niederschlag für den ausgewählten Detail-GWK. Die Darstellung dient der explorativen Analyse. Eine statistische Beziehung darf nicht automatisch als Ursache-Wirkungs-Beziehung interpretiert werden.

## Datenexport

### Räumliche Auswahl

Der Export kann auf alle oder ausgewählte GWK beschränkt werden.

### Zeitraumwahl

Referenz- und Vergleichszeitraum werden direkt auf der Exportseite festgelegt. Die gleichen Validierungsregeln wie im Viewer gelten.

### Formate

Je nach Datentabelle stehen bereit:

- CSV-Einzeldateien,
- ZIP-Archive mit mehreren CSV-Dateien,
- Excel-Arbeitsmappen mit mehreren Tabellenblättern.

Zeitreihen- und Trendtabellen können den vollständigen Datenzeitraum umfassen. Periodenvergleichstabellen verwenden die ausgewählten Zeiträume. Dateinamen enthalten aussagekräftige Angaben zu Zeitraum und räumlichem Umfang.

## Script-Bibliothek

### Suche

Die Volltextsuche berücksichtigt Titel, Kurzbeschreibung, Langbeschreibung, Tags, Kategorien, Sprache, Ein- und Ausgabeformate sowie technische Angaben.

### Filter

Filter können kombiniert werden:

- Kategorie,
- Sprache,
- Bereitstellungsform,
- Tags.

### Detailseite

Die Detailseite enthält:

- Kurz- und Langbeschreibung,
- Kategorie und Tags,
- Sprache und Laufzeitanforderungen,
- Abhängigkeiten,
- Ein- und Ausgabeformate,
- Einstiegspunkt,
- README-Inhalt,
- Download-Schaltfläche.

### Download

Einzeldateien werden in ihrem Originalformat bereitgestellt. Mehrteilige Werkzeuge werden als ZIP-Paket erzeugt. Bibliotheksdateien werden durch die Plattform nicht ausgeführt.

## Fehler- und Hinweismeldungen

- Fehlende Daten oder Geometrien werden als verständliche Fehlermeldung angezeigt.
- Ungültige Perioden werden nicht zur Berechnung verwendet.
- Eine leere Auswahl führt zu einem Hinweis statt zu einem nicht nachvollziehbaren Ergebnis.
- Fehlerhafte Bibliotheksmetadaten verhindern die Veröffentlichung des betreffenden Werkzeugs.
