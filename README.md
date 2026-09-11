<p align="center">
  <img src="brand/logo.png" alt="Envertech API" width="360">
</p>

<h1 align="center">Envertech API for Home Assistant</h1>

<p align="center">
  <strong>Lokale TCP-Überwachung für Envertech-Mikrowechselrichter — ohne Cloud.</strong>
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS"></a>
  <a href="https://github.com/jimmybonesde/Envertech_local/releases"><img src="https://img.shields.io/github/v/release/jimmybonesde/Envertech_local?style=flat" alt="Aktuelles Release"></a>
  <a href="https://github.com/jimmybonesde/Envertech_local/actions/workflows/hacs-validation.yaml"><img src="https://github.com/jimmybonesde/Envertech_local/actions/workflows/hacs-validation.yaml/badge.svg" alt="HACS-Validierung"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT-Lizenz"></a>
</p>

<p align="center">
  <a href="#-installation">Installation</a> ·
  <a href="#-sensoren">Sensoren</a> ·
  <a href="#-einrichtung">Einrichtung</a> ·
  <a href="#-unterstützte-geräte">Geräte</a>
</p>

> **Envertech API** liest die Daten deines Wechselrichters direkt im lokalen Netzwerk. Nach der Einrichtung wird kein Cloud-Konto benötigt.

Maintained fork by [JimmyBones](https://github.com/jimmybonesde), based on [Kaiserdragon2/Envertech_local](https://github.com/Kaiserdragon2/Envertech_local).

## ✨ Highlights

- 🏠 **100 % lokal** — direkte TCP-Verbindung zum Wechselrichter
- ⚡ **Live-Werte pro Panel** und für die gesamte Anlage
- 📈 **Energie-Dashboard-kompatibel** — Gesamt-, Tages-, Monats- und Jahresenergie
- 🔌 **Automatische Erkennung** im lokalen Netzwerk sowie manuelle Einrichtung
- 🌍 **Deutsch, Englisch und Polnisch**
- 🧩 **HACS-kompatibel**

## 📦 Installation

### HACS · empfohlen

[![Home Assistant öffnen und dieses Repository in HACS hinzufügen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jimmybonesde&repository=Envertech_local&category=integration)

1. Öffne in Home Assistant **HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories**.
2. Füge `https://github.com/jimmybonesde/Envertech_local` mit Kategorie **Integration** hinzu.
3. Suche nach **Envertech API** und installiere die Integration.
4. Starte Home Assistant neu.
5. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen** und wähle **Envertech API**.

### Manuell

1. Kopiere `custom_components/envertech_local` nach `config/custom_components/` deiner Home-Assistant-Installation.
2. Starte Home Assistant neu.
3. Füge **Envertech API** über **Einstellungen → Geräte & Dienste** hinzu.

## ⚙️ Einrichtung

1. Wähle einen automatisch gefundenen Wechselrichter oder **Manueller Eintrag**.
2. Prüfe IP-Adresse und TCP-Port. Der Standardport ist `14889`.
3. Nach dem ersten Datenpaket werden die passenden Sensoren automatisch angelegt.

> 💡 Für den Zugriff muss Home Assistant den Wechselrichter im lokalen Netzwerk auf TCP-Port `14889` erreichen können.

## 📊 Sensoren

Die verfügbaren Sensoren richten sich nach deinem Wechselrichter und dessen Panel-Konfiguration.

### ⚡ Je Panel

| Icon | Sensor | Einheit | Beschreibung |
| :--: | --- | :--: | --- |
| ⚡ | Leistung | W | Momentane Leistung des Panels |
| 🔋 | Energie | kWh | Vom Panel erzeugte Gesamtenergie |
| 🔌 | Eingangsspannung | V | DC-Eingangsspannung |
| 🌡️ | Temperatur | °C | Gemeldete Modultemperatur |
| ⚙️ | Netzspannung | V | AC-Netzspannung |
| 〰️ | Netzfrequenz | Hz | AC-Netzfrequenz |
| 🆔 | Modul-Seriennummer | — | Seriennummer des einzelnen Moduls |

Beispiele für Entity-IDs: `…_p1_power`, `…_p1_temperature`, `…_p1_grid_voltage`.

### 🏡 Wechselrichter & Anlage

| Icon | Sensor | Einheit | Beschreibung |
| :--: | --- | :--: | --- |
| ⚡ | Gesamtleistung | W | Aktuelle Leistung der gesamten Anlage |
| 🔋 | Gesamtenergie | kWh | Lebenszeitenergie der Anlage |
| 📅 | Tagesenergie | kWh | Erzeugung seit lokalem Mitternacht |
| 🗓️ | Monatsenergie | kWh | Erzeugung im aktuellen Monat |
| 📆 | Jahresenergie | kWh | Erzeugung im aktuellen Jahr |
| 🧠 | Firmware-Version | — | Vom Wechselrichter gemeldete Firmware |

Die Energie-Sensoren für Gesamt-, Tages-, Monats- und Jahreswerte sind für das **Home-Assistant-Energie-Dashboard** vorgesehen.

## 🔧 Unterstützte Geräte

Die Integration unterstützt Envertech-Mikrowechselrichter mit lokaler TCP-Schnittstelle, beispielsweise Geräte der **EMT-Serie**. Sie ist für Anlagen mit mehreren Panels ausgelegt.

Dein Modell funktioniert nicht oder liefert andere Daten? Bitte [erstelle ein Issue](https://github.com/jimmybonesde/Envertech_local/issues) und nenne Modell, Firmware-Version sowie – falls möglich – anonymisierte Log-Ausgaben.

## 🤝 Mitwirken

Beiträge, Fehlerberichte und Ideen sind willkommen:

- 🐛 [Issue melden](https://github.com/jimmybonesde/Envertech_local/issues)
- 🔀 [Pull Request öffnen](https://github.com/jimmybonesde/Envertech_local/pulls)
- ⭐ Das Repository markieren, wenn es dir hilft

## 🙏 Danksagung & Lizenz

- Originalarbeit: [Kaiserdragon2](https://github.com/Kaiserdragon2/Envertech_local)
- Pflege und Weiterentwicklung: **JimmyBones** ([@jimmybonesde](https://github.com/jimmybonesde))
- Polnische Übersetzung: [@vaGpl](https://github.com/vaGpl)

Veröffentlicht unter der [MIT-Lizenz](LICENSE).
