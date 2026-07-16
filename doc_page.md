# Plattform für Datenaufbereitung und  &#8209;visualisierung

**Interne Plattform Referat 43**

Die Dokumentation beschreibt die Bedienung, Datenbasis, fachlichen Methoden, Softwarearchitektur, Script-Bibliothek sowie Entwicklung und Betrieb der Anwendung.

## Dokumentationsbereiche

- [Projektüberblick](gwn_dashboard/documentation/overview.html)
- [Benutzerhandbuch](gwn_dashboard/documentation/user_guide.html)
- [Daten und fachliche Methoden](gwn_dashboard/documentation/data_methods.html)
- [Softwarearchitektur](gwn_dashboard/documentation/architecture.html)
- [Script-Bibliothek](gwn_dashboard/documentation/script_library.html)
- [Konfiguration](gwn_dashboard/documentation/configuration.html)
- [Teststrategie](gwn_dashboard/documentation/testing.html)
- [Betrieb und Wartung](gwn_dashboard/documentation/operations.html)
- [Referenz der Projektdateien](gwn_dashboard/documentation/file_reference.html)
- [Entwicklung](gwn_dashboard/documentation/development.html)
- [Glossar](gwn_dashboard/documentation/glossary.html)

## Web-Struktur

![Aktuelle Struktur der Web-Anwendung](documentation/images/web_application_structure.png)

## API-Referenz

Die Navigation der HTML-Dokumentation enthält sämtliche Python-Pakete, Module, Klassen, Methoden und Funktionen. Code-Docstrings sind englisch; fachliche und nutzerbezogene Seiten sind deutsch.

## Wesentliche fachliche Definition

Die jährliche Grundwasserneubildung wird in der Anwendung aus den Jahreswerten der beiden modellierten Speicherzuflüsse berechnet:

```text
GWN = rg1 + rg2
```

Weitere Einzelheiten enthält die Seite **Daten und fachliche Methoden**.
