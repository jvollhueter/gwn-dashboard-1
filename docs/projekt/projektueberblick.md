# Projektüberblick

## Zweck und fachlicher Rahmen

Die **Plattform für Datenaufbereitung und  &#8209;visualisierung | Interne Plattform Referat 43** bündelt fachliche Daten, Visualisierungen, Auswertungen und wiederverwendbare Arbeitsskripte in einer gemeinsamen webbasierten Oberfläche. Die Anwendung richtet sich an Mitarbeitende des Referats 43 und unterstützt insbesondere die nachvollziehbare Betrachtung modellierter Grundwasserneubildung auf Ebene der Grundwasserkörper.

Die Plattform verfolgt vier zentrale Ziele:

1. **Einheitlicher Zugang:** Fachliche Inhalte werden über eine gemeinsame Landing-Page und konsistente Navigation bereitgestellt.
2. **Nachvollziehbare Auswertung:** Räumliche und zeitliche Auswahl, statistische Berechnungen und Exporte folgen klar definierten Regeln.
3. **Trennung der Verantwortlichkeiten:** Datenzugriff, fachliche Verarbeitung, Visualisierung und Benutzeroberfläche sind im Quellcode getrennt.
4. **Wiederverwendbarkeit:** Die Script-Bibliothek stellt dokumentierte Python-, R- und Jupyter-Werkzeuge zum Download bereit.

## Web-Struktur

```text
Übergeordnete Landing-Page
├── Grundwasserdaten
│   └── Landing-Page Grundwasserdaten
│       ├── Grundwasserquantität
│       │   └── Landing-Page Grundwasserquantität
│       │       ├── Karten
│       │       ├── Diagramme
│       │       ├── Nomogramme
│       │       └── Datenexport
│       └── Grundwasserqualität
├── Meteorologische Daten
└── Script-Bibliothek
    ├── Suche und Filter
    ├── Detailseite je Veröffentlichung
    └── Download
```

Die Bereiche **Grundwasserqualität** und **Meteorologische Daten** besitzen funktionsfähige Platzhalterseiten. Sie enthalten keine fachlichen Daten oder Auswertungsfunktionen.

## Funktionsumfang Grundwasserquantität

Der Bereich Grundwasserquantität stellt folgende Funktionen bereit:

- Auswahl aller, mehrerer oder einzelner Grundwasserkörper,
- Festlegung eines Detail-GWK für Detaildarstellungen,
- freie Auswahl eines Referenz- und Vergleichszeitraums,
- Darstellung der Grundwasserneubildung als Karte und Zeitreihe,
- Darstellung von Niederschlag und potenzieller Evapotranspiration,
- Berechnung des periodischen Mittelwerts und der absoluten bzw. relativen Änderung,
- statistische Auswertungen und Trendkennwerte,
- Einblendung von Grundwassermessstellen,
- Filterung der Messstellen nach Einzelwahl oder GWK-Zuordnung,
- Export von Tabellen als CSV, ZIP und Excel.

## Funktionsumfang Script-Bibliothek

Die Script-Bibliothek unterstützt:

- Python-Einzeldateien,
- R-Einzeldateien,
- Jupyter-Notebooks,
- mehrteilige Python- oder R-Werkzeuge,
- Volltextsuche,
- Filter nach Kategorie, Sprache, Bereitstellungsform und Tags,
- Kurz- und Langbeschreibung,
- Detailseiten,
- direkten Download einzelner Dateien oder vollständiger ZIP-Pakete.

## Zielgruppen

### Fachliche Anwenderinnen und Anwender

Sie verwenden Karten, Diagramme, Tabellen und Exporte, ohne den Quellcode bearbeiten zu müssen.

### Datenverantwortliche

Sie prüfen Datenstände, Dateistrukturen, fachliche Zuordnungen und die korrekte Bereitstellung neuer Daten.

### Entwicklerinnen und Entwickler

Sie ergänzen Repositories, Services, Visualisierungen, UI-Seiten, Tests oder Veröffentlichungen der Script-Bibliothek.

## Fachliche Grenzen

- Die Grundwasserneubildung ist eine modellierte Größe und kein direkt gemessener Grundwasserstand.
- Die Messstellenpunkte bilden Lage und Metadaten ab; vollständige Messreihen sind nicht für alle Stationen Bestandteil des Projekts.
- Korrelationen zwischen Größen sind explorativ zu interpretieren und stellen keinen Kausalitätsnachweis dar.
- Die Anwendung verarbeitet lokale Dateien. Eine automatische Aktualisierung externer Datenquellen ist nicht Bestandteil des dokumentierten Funktionsumfangs.
