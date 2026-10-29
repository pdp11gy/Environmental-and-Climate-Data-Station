# Climate_Data_Analysis_DE.py , Version 1.0
# ============================================================
# Environmental and Climate Data Station
# Interactive Sensor Data Analysis and Visualization
# ============================================================
#
# Project: CHAPDP11GY-ENV-PICO-2025
# Author:  Reinhard Heuberger, info@pdp11gy.com
#
# Project concept, sensor hardware, data acquisition,
# and project integration by Reinhard H.
# User settings are stored in config.ini next to this file.
#
# AI assistance: OpenAI ChatGPT
# Development support for Python code, GUI implementation,
# data processing, debugging, and visualization.
#
# ============================================================

import calendar
import configparser
import csv
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime, date, timedelta

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# --------------------------------------------------
# Konfiguration aus config.ini
# --------------------------------------------------

# Die Konfigurationsdatei liegt neben diesem Python-Programm.
CONFIG_DATEI = Path(__file__).resolve().with_name("config.ini")

CONFIG_STANDARDWERTE = {
    "Paths": {
        "data_folder": r"H:\data",
        "data_filename": "daten.json",
        "output_folder": r"H:\1save_klima",
        "output_filename": "klimadaten.png",
    }
}


def speichere_konfiguration():
    """Schreibt die aktuellen Einstellungen in config.ini."""
    with CONFIG_DATEI.open("w", encoding="utf-8") as datei:
        KONFIGURATION.write(datei)


def lade_konfiguration():
    """Lädt config.ini und ergänzt fehlende Einträge mit Standardwerten."""
    konfiguration = configparser.ConfigParser()
    if CONFIG_DATEI.is_file():
        konfiguration.read(CONFIG_DATEI, encoding="utf-8")

    geaendert = False
    for abschnitt, eintraege in CONFIG_STANDARDWERTE.items():
        if not konfiguration.has_section(abschnitt):
            konfiguration.add_section(abschnitt)
            geaendert = True
        for schluessel, standardwert in eintraege.items():
            if (not konfiguration.has_option(abschnitt, schluessel)
                    or not konfiguration.get(abschnitt, schluessel).strip()):
                konfiguration.set(abschnitt, schluessel, standardwert)
                geaendert = True

    if geaendert or not CONFIG_DATEI.exists():
        with CONFIG_DATEI.open("w", encoding="utf-8") as datei:
            konfiguration.write(datei)

    return konfiguration


KONFIGURATION = lade_konfiguration()
DATEN_ORDNER = KONFIGURATION.get("Paths", "data_folder")
DATEN_DATEINAME = KONFIGURATION.get("Paths", "data_filename")
AUSGABE_ORDNER = KONFIGURATION.get("Paths", "output_folder")
AUSGABE_DATEINAME = KONFIGURATION.get("Paths", "output_filename")

MAX_SENSOREN = 4

FARBEN = [
    "tab:blue",
    "tab:orange",
    "tab:green",
    "tab:red",
]

STATION_NAMEN = {
    "station1": "Station 1",
    "station2": "Station 2",
    "station1u2": "Strahlungsstation",
}

FELD_INFO = {
    "co2": ("CO₂", "ppm"),
    "pm25": ("PM2.5", "µg/m³"),
    "pm10": ("PM10", "µg/m³"),
    "temperature": ("Temperatur", "°C"),
    "temp": ("Temperatur (Sensor)", "°C"),
    "humidity": ("Luftfeuchtigkeit", "%"),
    "pressure": ("Luftdruck", "hPa"),
    "wind_speed": ("Windgeschwindigkeit", ""),
    "wind_gust": ("Windböen", ""),
    "rain_rate": ("Niederschlagsrate", ""),
    "rain_total": ("Niederschlag gesamt", ""),
    "usvh": ("Strahlungsdosisleistung", "µSv/h"),
    "cpm": ("Geiger-Zählrate", "CPM"),
    "uv_raw": ("UV-Rohwert", ""),
}


# --------------------------------------------------
# Dateipfad aus Datenordner und ausgewähltem Datum bilden
# --------------------------------------------------

def dateipfad_fuer_datum(daten_ordner, datum, dateiname=None):
    """Erzeugt .../YYYY_KWxx/YYYY-MM-DD/<Dateiname>."""
    # Die vorhandenen Datenordner verwenden %W: Wochenbeginn Montag,
    # wobei die Tage vor dem ersten Montag als KW00 zählen.
    kalenderwoche = int(datum.strftime("%W"))
    if dateiname is None:
        dateiname = DATEN_DATEINAME
    return (
        Path(daten_ordner)
        / f"{datum.year}_KW{kalenderwoche:02d}"
        / datum.isoformat()
        / dateiname
    )


def finde_neuestes_datum(daten_ordner, dateiname):
    """Findet den jüngsten Tag, für den die konfigurierte Datei existiert."""
    basis = Path(daten_ordner).expanduser()
    if not basis.is_dir():
        return None

    gefundene_tage = []
    try:
        wochenordner = [p for p in basis.iterdir()
                        if p.is_dir() and "_KW" in p.name]
        for wochenordner_eintrag in wochenordner:
            for tagesordner in wochenordner_eintrag.iterdir():
                if not tagesordner.is_dir():
                    continue
                try:
                    tag = date.fromisoformat(tagesordner.name)
                except ValueError:
                    continue
                erwartete_datei = dateipfad_fuer_datum(
                    basis, tag, dateiname
                )
                if erwartete_datei.is_file():
                    gefundene_tage.append(tag)
    except OSError:
        return None

    return max(gefundene_tage) if gefundene_tage else None


def naechste_freie_versionspfade(dateistamm, endungen):
    """Liefert die erste freie V1-, V2- usw. Dateinamengruppe.

    Sobald auch nur eine Datei der betreffenden Version existiert, wird
    die nächste Versionsnummer verwendet. Damit bleiben zusammengehörige
    Wochen-Diagramme und CSV-Statistiken unter derselben Version.
    """
    ausgabe_ordner = Path(AUSGABE_ORDNER)
    version = 1

    while True:
        pfade = [
            ausgabe_ordner / f"V{version}-{dateistamm}{endung}"
            for endung in endungen
        ]
        if not any(pfad.exists() for pfad in pfade):
            return pfade
        version += 1


def ausgabepfad_fuer_datum(datum):
    """Erzeugt z. B. V1-klimadaten_2026-09-19.png, ohne Dateien zu überschreiben."""
    vorlage = Path(AUSGABE_DATEINAME).name
    vorlagenpfad = Path(vorlage)
    endung = vorlagenpfad.suffix or ".png"
    dateistamm = vorlagenpfad.stem if vorlagenpfad.suffix else vorlage
    basisname = f"{dateistamm}_{datum.isoformat()}"
    return naechste_freie_versionspfade(basisname, [endung])[0]


AKTUELLES_DATUM = finde_neuestes_datum(DATEN_ORDNER, DATEN_DATEINAME)
if AKTUELLES_DATUM is None:
    raise SystemExit(
        "Keine passende Datendatei gefunden.\n\n"
        f"Datenordner: {DATEN_ORDNER}\n"
        f"Dateiname: {DATEN_DATEINAME}\n\n"
        f"Bitte prüfen Sie die Einstellungen in:\n{CONFIG_DATEI}"
    )

DATEI = str(dateipfad_fuer_datum(DATEN_ORDNER, AKTUELLES_DATUM))


# --------------------------------------------------
# JSON-Datei laden
# Unterstützt JSON-Liste und JSON pro Zeile
# --------------------------------------------------

def lade_daten(datei):
    text = Path(datei).read_text(encoding="utf-8-sig").strip()

    if not text:
        return []

    try:
        daten_ganz = json.loads(text)
        if isinstance(daten_ganz, list):
            return daten_ganz
        if isinstance(daten_ganz, dict):
            return [daten_ganz]
    except json.JSONDecodeError:
        pass

    daten_zeilen = []
    for zeile in text.splitlines():
        try:
            eintrag = json.loads(zeile)
            if isinstance(eintrag, dict):
                daten_zeilen.append(eintrag)
        except json.JSONDecodeError:
            continue

    return daten_zeilen


# --------------------------------------------------
# Verfügbare Messgrößen erkennen
# --------------------------------------------------

def erkenne_sensoren(daten_eingabe):
    verfuegbar = set()

    for eintrag in daten_eingabe:
        station = eintrag.get("station")
        sensor = eintrag.get("sensor")

        if not station or not sensor:
            continue

        for feld, wert in eintrag.items():
            if feld in ("station", "sensor", "timestamp", "status"):
                continue

            if isinstance(wert, (int, float)) and not isinstance(wert, bool):
                verfuegbar.add((station, sensor, feld))

    return sorted(verfuegbar)


def sensor_name(schluessel):
    station, sensor, feld = schluessel
    station_name = STATION_NAMEN.get(station, station)
    messname, einheit = FELD_INFO.get(feld, (feld, ""))
    text = f"{station_name} – {messname}"

    if einheit:
        text += f" ({einheit})"
    if feld == "temp":
        text += f" [{sensor}]"

    return text


# --------------------------------------------------
# Messreihen aus ausgewählten Messgrößen sammeln
# --------------------------------------------------

def messreihen_laden(daten_eingabe, ausgewaehlt):
    messreihen = []

    for schluessel in ausgewaehlt:
        station, sensor, feld = schluessel
        zeiten = []
        werte = []

        for eintrag in daten_eingabe:
            if eintrag.get("station") != station:
                continue
            if eintrag.get("sensor") != sensor:
                continue
            if feld not in eintrag:
                continue

            wert = eintrag[feld]
            if not isinstance(wert, (int, float)) or isinstance(wert, bool):
                continue

            try:
                zeit = datetime.strptime(
                    eintrag["timestamp"], "%Y-%m-%d %H:%M:%S"
                )
            except (KeyError, ValueError, TypeError):
                continue

            zeiten.append(zeit)
            werte.append(wert)

        if zeiten:
            sortiert = sorted(zip(zeiten, werte))
            zeiten, werte = zip(*sortiert)
            messreihen.append((schluessel, list(zeiten), list(werte)))
        else:
            messagebox.showwarning(
                "Keine Messwerte",
                f"Keine gültigen Werte gefunden für:\n{sensor_name(schluessel)}",
            )

    return messreihen


# --------------------------------------------------
# Diagramme erstellen
# modus: "einzeln" oder "gemeinsam"
# --------------------------------------------------

def diagramme_erstellen(ausgewaehlt, modus):
    fig = None

    try:
        # Es werden die aktuell geladenen Daten verwendet.
        if not daten:
            messagebox.showwarning(
                "Keine Daten", "Die Datendatei enthält keine Messwerte."
            )
            return

        messreihen = messreihen_laden(daten, ausgewaehlt)
        if not messreihen:
            return

        if modus == "gemeinsam":
            fig, ax_links = plt.subplots(figsize=(12, 6))
            fig.suptitle("Klimadaten – gemeinsames Diagramm", fontsize=14)
            alle_achsen = []

            for index, (schluessel, zeiten, werte) in enumerate(messreihen):
                station, sensor, feld = schluessel
                messname, einheit = FELD_INFO.get(feld, (feld, ""))
                farbe = FARBEN[index % len(FARBEN)]
                beschriftung = sensor_name(schluessel)

                if index == 0:
                    ax = ax_links
                    ax.set_ylabel(
                        f"{messname} ({einheit})" if einheit else messname,
                        color=farbe,
                    )
                    ax.tick_params(axis="y", colors=farbe)
                    ax.spines["left"].set_color(farbe)
                else:
                    ax = ax_links.twinx()
                    if index >= 2:
                        ax.spines["right"].set_position(
                            ("outward", 55 * (index - 1))
                        )
                    ax.set_ylabel(
                        f"{messname} ({einheit})" if einheit else messname,
                        color=farbe,
                    )
                    ax.tick_params(axis="y", colors=farbe)
                    ax.spines["right"].set_color(farbe)

                ax.plot(
                    zeiten, werte, color=farbe, linewidth=1.3,
                    label=beschriftung
                )
                alle_achsen.append(ax)

            rechter_rand = min(
                0.92, 0.92 - 0.055 * max(0, len(messreihen) - 1)
            )
            fig.subplots_adjust(right=max(0.58, rechter_rand))
            ax_links.grid(True, linestyle="--", alpha=0.5)
            ax_links.set_xlabel("Uhrzeit")
            ax_links.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

            linien, etiketten = [], []
            for ax in alle_achsen:
                handles, labels = ax.get_legend_handles_labels()
                linien.extend(handles)
                etiketten.extend(labels)
            ax_links.legend(linien, etiketten, loc="upper left")
            achsen = [ax_links]

        else:
            anzahl = len(messreihen)
            fig, achsen_array = plt.subplots(
                anzahl,
                1,
                figsize=(12, 3.2 * anzahl),
                sharex=True,
                squeeze=False,
            )
            achsen = list(achsen_array[:, 0])
            fig.suptitle("Klimadaten – einzelne Diagramme", fontsize=14)

            for index, (ax, reihe) in enumerate(zip(achsen, messreihen)):
                schluessel, zeiten, werte = reihe
                station, sensor, feld = schluessel
                messname, einheit = FELD_INFO.get(feld, (feld, ""))

                ax.plot(
                    zeiten,
                    werte,
                    color=FARBEN[index % len(FARBEN)],
                    linewidth=1.3,
                    label=sensor_name(schluessel),
                )
                ax.set_ylabel(
                    f"{messname} ({einheit})" if einheit else messname
                )
                ax.grid(True, linestyle="--", alpha=0.5)
                ax.legend(loc="upper left")

        achsen[-1].set_xlabel("Uhrzeit")
        achsen[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        fig.tight_layout(rect=[0, 0, 1, 0.95])

        # Das Datum der aktuell ausgewählten Messdatei an den Namen anhängen,
        # zum Beispiel: klimadaten_2026-09-19.png
        ausgabe_pfad = ausgabepfad_fuer_datum(AKTUELLES_DATUM)
        ausgabe_pfad.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(ausgabe_pfad, dpi=150)

        print(f"Datendatei: {DATEI}")
        print(f"Diagramm gespeichert (neue Version): {ausgabe_pfad}")
        print(f"Anzahl dargestellter Messgrößen: {len(messreihen)}")
        print(f"Darstellungsart: {modus}")
        plt.show()

    except (OSError, json.JSONDecodeError) as fehler:
        messagebox.showerror("Dateifehler", str(fehler))
    finally:
        if fig is not None:
            plt.close(fig)


# --------------------------------------------------
# Wochenanalyse: Montag bis Sonntag
# --------------------------------------------------

def ausgabepfade_fuer_woche(datum):
    """Liefert freie Pfade für Wochen-Diagramm und CSV derselben Version."""
    vorlage = Path(AUSGABE_DATEINAME).name
    vorlagenpfad = Path(vorlage)
    dateistamm = vorlagenpfad.stem if vorlagenpfad.suffix else vorlage
    endung = vorlagenpfad.suffix or ".png"
    kw = int(datum.strftime("%W"))
    kennung = f"KW{kw:02d}_{datum.year}"
    basisname = f"{dateistamm}_{kennung}"
    return naechste_freie_versionspfade(
        basisname, [endung, "_statistik.csv"]
    )


def fuege_diagramm_luecken_ein(zeiten, werte, luecke_minuten=30):
    """Fügt NaN-Punkte bei großen Messlücken ein, damit Linien nicht irreführen."""
    if not zeiten:
        return [], []

    x_werte = [zeiten[0]]
    y_werte = [werte[0]]
    grenze = timedelta(minutes=luecke_minuten)

    for zeit, wert, vorherige_zeit in zip(zeiten[1:], werte[1:], zeiten[:-1]):
        if zeit - vorherige_zeit > grenze:
            mitte = vorherige_zeit + (zeit - vorherige_zeit) / 2
            x_werte.append(mitte)
            y_werte.append(float("nan"))
        x_werte.append(zeit)
        y_werte.append(wert)

    return x_werte, y_werte


def wochenanalyse_erstellen(ausgewaehlt, modus):
    """Lädt die sieben Tagesdateien der gewählten Woche und erstellt Wochencharts/Statistik."""
    wochenstart = AKTUELLES_DATUM - timedelta(days=AKTUELLES_DATUM.weekday())
    wochenende = wochenstart + timedelta(days=6)

    alle_daten = []
    geladene_tage = []
    fehlende_tage = []

    for offset in range(7):
        tag = wochenstart + timedelta(days=offset)
        dateipfad = dateipfad_fuer_datum(DATEN_ORDNER, tag)
        if not dateipfad.is_file():
            fehlende_tage.append(tag.isoformat())
            continue

        try:
            tagesdaten = lade_daten(dateipfad)
        except (OSError, json.JSONDecodeError) as fehler:
            fehlende_tage.append(f"{tag.isoformat()} (Lesefehler: {fehler})")
            continue

        if not tagesdaten:
            fehlende_tage.append(f"{tag.isoformat()} (Datei leer)")
            continue

        alle_daten.extend(tagesdaten)
        geladene_tage.append(tag)

    if not alle_daten:
        messagebox.showwarning(
            "Keine Wochenmessdaten",
            "Für die ausgewählte Woche wurden keine lesbaren Tagesdateien gefunden.\n\n"
            f"Zeitraum: {wochenstart:%d.%m.%Y} bis {wochenende:%d.%m.%Y}\n"
            f"Datenordner: {DATEN_ORDNER}",
        )
        return

    messreihen = messreihen_laden(alle_daten, ausgewaehlt)
    if not messreihen:
        return

    kw = int(AKTUELLES_DATUM.strftime("%W"))
    wochenkennung = f"{AKTUELLES_DATUM.year}_KW{kw:02d}"
    titel_zeitraum = f"{wochenstart:%d.%m.%Y} – {wochenende:%d.%m.%Y}"
    fig = None

    try:
        if modus == "gemeinsam":
            fig, ax_links = plt.subplots(figsize=(13, 6))
            fig.suptitle(
                f"Klimadaten – Wochenanalyse {wochenkennung}\n{titel_zeitraum}",
                fontsize=14,
            )
            alle_achsen = []

            for index, (schluessel, zeiten, werte) in enumerate(messreihen):
                _, _, feld = schluessel
                messname, einheit = FELD_INFO.get(feld, (feld, ""))
                farbe = FARBEN[index % len(FARBEN)]
                beschriftung = sensor_name(schluessel)
                x_werte, y_werte = fuege_diagramm_luecken_ein(zeiten, werte)

                if index == 0:
                    ax = ax_links
                    ax.set_ylabel(
                        f"{messname} ({einheit})" if einheit else messname,
                        color=farbe,
                    )
                    ax.tick_params(axis="y", colors=farbe)
                    ax.spines["left"].set_color(farbe)
                else:
                    ax = ax_links.twinx()
                    if index >= 2:
                        ax.spines["right"].set_position(
                            ("outward", 55 * (index - 1))
                        )
                    ax.set_ylabel(
                        f"{messname} ({einheit})" if einheit else messname,
                        color=farbe,
                    )
                    ax.tick_params(axis="y", colors=farbe)
                    ax.spines["right"].set_color(farbe)

                ax.plot(
                    x_werte, y_werte, color=farbe, linewidth=1.1,
                    label=beschriftung
                )
                alle_achsen.append(ax)

            rechter_rand = min(
                0.92, 0.92 - 0.055 * max(0, len(messreihen) - 1)
            )
            fig.subplots_adjust(right=max(0.58, rechter_rand))
            ax_links.grid(True, linestyle="--", alpha=0.5)
            ax_links.set_xlabel("Datum und Uhrzeit")

            linien, etiketten = [], []
            for ax in alle_achsen:
                handles, labels = ax.get_legend_handles_labels()
                linien.extend(handles)
                etiketten.extend(labels)
            ax_links.legend(linien, etiketten, loc="upper left")
            achsen = [ax_links]

        else:
            anzahl = len(messreihen)
            fig, achsen_array = plt.subplots(
                anzahl,
                1,
                figsize=(13, 3.2 * anzahl),
                sharex=True,
                squeeze=False,
            )
            achsen = list(achsen_array[:, 0])
            fig.suptitle(
                f"Klimadaten – Wochenanalyse {wochenkennung}\n{titel_zeitraum}",
                fontsize=14,
            )

            for index, (ax, reihe) in enumerate(zip(achsen, messreihen)):
                schluessel, zeiten, werte = reihe
                _, _, feld = schluessel
                messname, einheit = FELD_INFO.get(feld, (feld, ""))
                x_werte, y_werte = fuege_diagramm_luecken_ein(zeiten, werte)

                ax.plot(
                    x_werte,
                    y_werte,
                    color=FARBEN[index % len(FARBEN)],
                    linewidth=1.1,
                    label=sensor_name(schluessel),
                )
                ax.set_ylabel(
                    f"{messname} ({einheit})" if einheit else messname
                )
                ax.grid(True, linestyle="--", alpha=0.5)
                ax.legend(loc="upper left")

        # Eine lesbare Datums-/Uhrzeitachse für den gesamten Wochenverlauf.
        formatter_achse = achsen[-1]
        formatter_achse.set_xlabel("Datum und Uhrzeit")
        formatter_achse.xaxis.set_major_locator(
            mdates.AutoDateLocator(minticks=5, maxticks=12)
        )
        formatter_achse.xaxis.set_major_formatter(
            mdates.DateFormatter("%d.%m.\n%H:%M")
        )
        fig.tight_layout(rect=[0, 0, 1, 0.93])

        png_pfad, csv_pfad = ausgabepfade_fuer_woche(AKTUELLES_DATUM)
        png_pfad.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(png_pfad, dpi=150)

        # Wochenstatistik: Anzahl, Minimum, Mittelwert und Maximum je Messreihe.
        with csv_pfad.open("w", newline="", encoding="utf-8-sig") as datei:
            schreiber = csv.writer(datei, delimiter=";")
            schreiber.writerow([
                "Station", "Sensor", "Messgröße", "Einheit",
                "Anzahl Messwerte", "Minimum", "Mittelwert", "Maximum"
            ])
            for schluessel, _, werte in messreihen:
                station, sensor, feld = schluessel
                messname, einheit = FELD_INFO.get(feld, (feld, ""))
                minimum = min(werte)
                maximum = max(werte)
                mittelwert = sum(werte) / len(werte)
                dezimal = lambda zahl: f"{zahl:.3f}".replace(".", ",")
                schreiber.writerow([
                    STATION_NAMEN.get(station, station),
                    sensor,
                    messname,
                    einheit,
                    len(werte),
                    dezimal(minimum),
                    dezimal(mittelwert),
                    dezimal(maximum),
                ])

        print(f"Wochenanalyse: {wochenstart.isoformat()} bis {wochenende.isoformat()}")
        print(f"Geladene Tage: {len(geladene_tage)} von 7")
        print(f"Wochen-Diagramm gespeichert (neue Version): {png_pfad}")
        print(f"Wochenstatistik gespeichert (neue Version): {csv_pfad}")
        plt.show()

        hinweis = (
            f"Wochenanalyse abgeschlossen.\n\n"
            f"Zeitraum: {wochenstart:%d.%m.%Y} bis {wochenende:%d.%m.%Y}\n"
            f"Gefundene Tagesdateien: {len(geladene_tage)} von 7\n\n"
            f"Diagramm:\n{png_pfad}\n\n"
            f"Statistik:\n{csv_pfad}"
        )
        if fehlende_tage:
            hinweis += "\n\nFehlende oder nicht lesbare Tage:\n" + "\n".join(fehlende_tage)
        messagebox.showinfo("Wochenanalyse", hinweis)

    except (OSError, csv.Error, ValueError) as fehler:
        messagebox.showerror("Fehler bei der Wochenanalyse", str(fehler))
    finally:
        if fig is not None:
            plt.close(fig)


# --------------------------------------------------
# Tkinter-Kalender als Fenster im Hauptprogramm
# --------------------------------------------------

class KalenderFenster:
    def __init__(self, parent, startdatum, callback):
        self.parent = parent
        self.callback = callback
        self.jahr = startdatum.year
        self.monat = startdatum.month
        self.ausgewaehltes_datum = startdatum

        self.top = tk.Toplevel(parent)
        self.top.title("Messtag auswählen")
        self.top.transient(parent)
        self.top.resizable(False, False)

        kopf = tk.Frame(self.top)
        kopf.pack(padx=10, pady=(10, 4), fill="x")

        tk.Button(kopf, text="◀", width=4, command=self.monat_zurueck).pack(
            side="left"
        )
        self.monats_label = tk.Label(kopf, width=19, font=("Arial", 12, "bold"))
        self.monats_label.pack(side="left", expand=True)
        tk.Button(kopf, text="▶", width=4, command=self.monat_vor).pack(
            side="right"
        )

        self.tage_frame = tk.Frame(self.top)
        self.tage_frame.pack(padx=10, pady=4)

        self.auswahl_label = tk.Label(
            self.top,
            text="",
            font=("Arial", 10),
        )
        self.auswahl_label.pack(pady=5)

        knopf_rahmen = tk.Frame(self.top)
        knopf_rahmen.pack(pady=(2, 10))
        tk.Button(
            knopf_rahmen,
            text="Datum übernehmen",
            command=self.datum_uebernehmen,
        ).pack(side="left", padx=5)
        tk.Button(
            knopf_rahmen,
            text="Abbrechen",
            command=self.top.destroy,
        ).pack(side="left", padx=5)

        self.zeichne_kalender()
        self.top.grab_set()

    def monat_zurueck(self):
        if self.monat == 1:
            self.monat = 12
            self.jahr -= 1
        else:
            self.monat -= 1
        self.zeichne_kalender()

    def monat_vor(self):
        if self.monat == 12:
            self.monat = 1
            self.jahr += 1
        else:
            self.monat += 1
        self.zeichne_kalender()

    def datum_anklicken(self, tag):
        self.ausgewaehltes_datum = date(self.jahr, self.monat, tag)
        self.auswahl_label.config(
            text=f"Ausgewählt: {self.ausgewaehltes_datum.isoformat()}"
        )
        self.zeichne_kalender()

    def zeichne_kalender(self):
        for kind in self.tage_frame.winfo_children():
            kind.destroy()

        self.monats_label.config(
            text=f"{calendar.month_name[self.monat]} {self.jahr}"
        )
        wochentage = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"]
        for spalte, name in enumerate(wochentage):
            tk.Label(
                self.tage_frame,
                text=name,
                width=4,
                font=("Arial", 9, "bold"),
            ).grid(row=0, column=spalte, padx=1, pady=2)

        kalender = calendar.Calendar(firstweekday=calendar.SUNDAY)
        wochen = kalender.monthdayscalendar(self.jahr, self.monat)

        for zeile, woche in enumerate(wochen, start=1):
            for spalte, tag in enumerate(woche):
                if tag == 0:
                    tk.Label(self.tage_frame, text="", width=4).grid(
                        row=zeile, column=spalte, padx=1, pady=1
                    )
                    continue

                ist_ausgewaehlt = (
                    self.ausgewaehltes_datum.year == self.jahr
                    and self.ausgewaehltes_datum.month == self.monat
                    and self.ausgewaehltes_datum.day == tag
                )
                tk.Button(
                    self.tage_frame,
                    text=str(tag),
                    width=3,
                    relief="sunken" if ist_ausgewaehlt else "raised",
                    command=lambda t=tag: self.datum_anklicken(t),
                ).grid(row=zeile, column=spalte, padx=1, pady=1)

        self.auswahl_label.config(
            text=f"Ausgewählt: {self.ausgewaehltes_datum.isoformat()}"
        )

    def datum_uebernehmen(self):
        self.top.destroy()
        self.callback(self.ausgewaehltes_datum)


# --------------------------------------------------
# Oberfläche
# --------------------------------------------------

try:
    daten = lade_daten(DATEI)
    sensor_liste = erkenne_sensoren(daten)
except (OSError, json.JSONDecodeError) as fehler:
    raise SystemExit(f"Fehler beim Laden der Messdaten: {fehler}")

if not sensor_liste:
    raise SystemExit("Keine Messgrößen gefunden.")

fenster = tk.Tk()
fenster.title("Klimastation – Sensorauswahl")
fenster.geometry("680x790")
fenster.minsize(520, 500)

# Pfad- und Kalenderknöpfe
knopf_rahmen = tk.Frame(fenster)
knopf_rahmen.pack(fill="x", padx=8, pady=5)

tk.Button(
    knopf_rahmen,
    text="📅 Datum auswählen",
    command=lambda: KalenderFenster(fenster, AKTUELLES_DATUM, lade_datum),
).pack(side="left", padx=5)

tk.Button(
    knopf_rahmen,
    text="📁 Datenordner auswählen",
    command=lambda: datenordner_waehlen(),
).pack(side="left", padx=5)

pfad_anzeige = tk.StringVar(value=f"Aktuelle Datendatei:\n{DATEI}")
tk.Label(
    fenster,
    textvariable=pfad_anzeige,
    font=("Consolas", 9),
    justify="left",
    anchor="w",
    wraplength=650,
).pack(fill="x", padx=12, pady=(4, 2))

ordner_anzeige = tk.StringVar(value=f"Datenordner: {DATEN_ORDNER}")
tk.Label(
    fenster,
    textvariable=ordner_anzeige,
    font=("Arial", 9),
    justify="left",
    anchor="w",
    wraplength=650,
).pack(fill="x", padx=12, pady=(0, 4))

tk.Label(
    fenster,
    text="Bis zu vier Messgrößen auswählen",
    font=("Arial", 13, "bold"),
).pack(pady=6)

anzahl_anzeige = tk.StringVar(value=f"Gefundene Datensätze: {len(daten)}")
tk.Label(fenster, textvariable=anzahl_anzeige).pack(pady=2)

# Darstellungsart
tk.Label(
    fenster,
    text="Darstellungsart:",
    font=("Arial", 10, "bold"),
).pack(anchor="w", padx=14, pady=(8, 2))

modus_variable = tk.StringVar(value="einzeln")
tk.Radiobutton(
    fenster,
    text="Einzelne Grafik pro Messgröße",
    variable=modus_variable,
    value="einzeln",
).pack(anchor="w", padx=18)
tk.Radiobutton(
    fenster,
    text="Alle ausgewählten Messgrößen in einer Grafik",
    variable=modus_variable,
    value="gemeinsam",
).pack(anchor="w", padx=18)

# Scrollbarer Sensorbereich
bereich = tk.Frame(fenster)
bereich.pack(fill="both", expand=True, padx=12, pady=8)
leinwand = tk.Canvas(bereich)
scrollbar = tk.Scrollbar(bereich, orient="vertical", command=leinwand.yview)
rahmen = tk.Frame(leinwand)

rahmen.bind(
    "<Configure>",
    lambda event: leinwand.configure(scrollregion=leinwand.bbox("all")),
)
fenster_fenster = leinwand.create_window((0, 0), window=rahmen, anchor="nw")
leinwand.configure(yscrollcommand=scrollbar.set)
leinwand.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")
leinwand.bind(
    "<Configure>",
    lambda event: leinwand.itemconfigure(fenster_fenster, width=event.width),
)

variablen = {}


def auswahl_geaendert(schluessel):
    aktiv = sum(variable.get() for variable in variablen.values())
    if aktiv > MAX_SENSOREN:
        variablen[schluessel].set(False)
        messagebox.showinfo(
            "Sensorauswahl", "Bitte maximal vier Messgrößen auswählen."
        )


def aktualisiere_checkboxen():
    """Checkboxen anhand der aktuell geladenen Datei neu aufbauen."""
    bisher_ausgewaehlt = {
        schluessel
        for schluessel, variable in variablen.items()
        if variable.get()
    }

    for kind in rahmen.winfo_children():
        kind.destroy()
    variablen.clear()

    for schluessel in sensor_liste:
        variable = tk.BooleanVar(value=schluessel in bisher_ausgewaehlt)
        variablen[schluessel] = variable
        tk.Checkbutton(
            rahmen,
            text=sensor_name(schluessel),
            variable=variable,
            anchor="w",
            command=lambda s=schluessel: auswahl_geaendert(s),
        ).pack(fill="x", pady=2)


def lade_datum(neues_datum):
    """Lädt die JSON-Datei für das ausgewählte Datum und aktualisiert die GUI."""
    global DATEI, daten, sensor_liste, AKTUELLES_DATUM

    neuer_pfad = dateipfad_fuer_datum(DATEN_ORDNER, neues_datum)

    if not neuer_pfad.is_file():
        messagebox.showwarning(
            "Datendatei nicht gefunden",
            f"Für dieses Datum wurde keine Datei gefunden:\n\n{neuer_pfad}\n\n"
            "Der bisherige Datenstand bleibt geöffnet.",
        )
        return

    try:
        neue_daten = lade_daten(neuer_pfad)
    except (OSError, json.JSONDecodeError) as fehler:
        messagebox.showerror("Dateifehler", str(fehler))
        return

    neue_sensor_liste = erkenne_sensoren(neue_daten)
    if not neue_daten or not neue_sensor_liste:
        messagebox.showwarning(
            "Keine Messdaten",
            f"Die Datei enthält keine erkennbaren Messgrößen:\n{neuer_pfad}",
        )
        return

    DATEI = str(neuer_pfad)
    daten = neue_daten
    sensor_liste = neue_sensor_liste
    AKTUELLES_DATUM = neues_datum

    pfad_anzeige.set(f"Aktuelle Datendatei:\n{DATEI}")
    anzahl_anzeige.set(f"Gefundene Datensätze: {len(daten)}")
    aktualisiere_checkboxen()
    print(f"Neue Datendatei geladen: {DATEI}")


def datenordner_waehlen():
    """Öffnet einen kompakten Tkinter-Ordnerdialog statt des Windows-Dialogs."""
    top = tk.Toplevel(fenster)
    top.title("Datenordner auswählen")
    top.geometry("620x420")
    top.minsize(500, 330)
    top.transient(fenster)
    top.grab_set()

    aktueller_pfad = tk.StringVar(value=str(Path(DATEN_ORDNER)))

    tk.Label(
        top,
        text=r"Ordner mit den Klimadaten auswählen (z. B. H:\data):",
        anchor="w",
    ).pack(fill="x", padx=12, pady=(12, 4))

    pfad_rahmen = tk.Frame(top)
    pfad_rahmen.pack(fill="x", padx=12, pady=4)

    pfad_eingabe = tk.Entry(pfad_rahmen, textvariable=aktueller_pfad)
    pfad_eingabe.pack(side="left", fill="x", expand=True)

    listen_rahmen = tk.Frame(top)
    listen_rahmen.pack(fill="both", expand=True, padx=12, pady=8)

    ordner_liste = tk.Listbox(listen_rahmen, height=12)
    ordner_scrollbar = tk.Scrollbar(
        listen_rahmen, orient="vertical", command=ordner_liste.yview
    )
    ordner_liste.configure(yscrollcommand=ordner_scrollbar.set)
    ordner_liste.pack(side="left", fill="both", expand=True)
    ordner_scrollbar.pack(side="right", fill="y")

    def zeige_ordner(pfad=None):
        ziel = Path(pfad if pfad is not None else aktueller_pfad.get()).expanduser()
        if not ziel.exists() or not ziel.is_dir():
            messagebox.showerror(
                "Ordner nicht gefunden",
                f"Diesen Ordner gibt es nicht:\n{ziel}",
                parent=top,
            )
            return

        try:
            unterordner = sorted(
                (eintrag for eintrag in ziel.iterdir() if eintrag.is_dir()),
                key=lambda eintrag: eintrag.name.lower(),
            )
        except OSError as fehler:
            messagebox.showerror("Ordner kann nicht gelesen werden", str(fehler), parent=top)
            return

        aktueller_pfad.set(str(ziel))
        ordner_liste.delete(0, tk.END)
        for eintrag in unterordner:
            ordner_liste.insert(tk.END, eintrag.name)

    def einen_ordner_oeffnen(event=None):
        auswahl = ordner_liste.curselection()
        if not auswahl:
            return
        zeige_ordner(Path(aktueller_pfad.get()) / ordner_liste.get(auswahl[0]))

    def eine_ebene_hoch():
        aktueller = Path(aktueller_pfad.get())
        uebergeordnet = aktueller.parent
        if uebergeordnet != aktueller:
            zeige_ordner(uebergeordnet)

    def ordner_uebernehmen():
        global DATEN_ORDNER
        ordner = Path(aktueller_pfad.get()).expanduser()
        if not ordner.exists() or not ordner.is_dir():
            messagebox.showerror(
                "Ungültiger Ordner",
                f"Bitte einen existierenden Ordner auswählen:\n{ordner}",
                parent=top,
            )
            return

        DATEN_ORDNER = str(ordner)
        ordner_anzeige.set(f"Datenordner: {DATEN_ORDNER}")
        KONFIGURATION.set("Paths", "data_folder", DATEN_ORDNER)
        try:
            speichere_konfiguration()
        except OSError as fehler:
            messagebox.showerror(
                "Konfiguration konnte nicht gespeichert werden",
                f"Der Datenordner wurde für diese Sitzung ausgewählt,\n"
                f"konnte aber nicht in config.ini gespeichert werden:\n{fehler}",
                parent=top,
            )
        top.destroy()

        # Für das aktuelle Datum sofort neu laden, sofern die Datei vorhanden ist.
        erwarteter_pfad = dateipfad_fuer_datum(DATEN_ORDNER, AKTUELLES_DATUM)
        if erwarteter_pfad.is_file():
            lade_datum(AKTUELLES_DATUM)
        else:
            messagebox.showinfo(
                "Datenordner übernommen",
                "Der Datenordner wurde geändert. Für den bisher gewählten Tag gibt es "
                "dort keine Datei. Wähle bitte im Kalender einen Tag, für den Daten "
                "vorhanden sind.",
                parent=fenster,
            )

    tk.Button(pfad_rahmen, text="Öffnen", command=zeige_ordner).pack(
        side="left", padx=(6, 0)
    )
    ordner_liste.bind("<Double-Button-1>", einen_ordner_oeffnen)
    pfad_eingabe.bind("<Return>", lambda event: zeige_ordner())

    knopf_rahmen = tk.Frame(top)
    knopf_rahmen.pack(fill="x", padx=12, pady=(0, 12))
    tk.Button(
        knopf_rahmen, text="Eine Ebene höher", command=eine_ebene_hoch
    ).pack(side="left")
    tk.Button(
        knopf_rahmen, text="Diesen Ordner übernehmen", command=ordner_uebernehmen
    ).pack(side="right", padx=(6, 0))
    tk.Button(knopf_rahmen, text="Abbrechen", command=top.destroy).pack(
        side="right"
    )

    zeige_ordner()
    pfad_eingabe.focus_set()


# Erste Checkboxen anzeigen
aktualisiere_checkboxen()


def aktuelle_sensorenauswahl():
    ausgewaehlt = [
        schluessel
        for schluessel, variable in variablen.items()
        if variable.get()
    ]
    if not ausgewaehlt:
        messagebox.showwarning(
            "Sensorauswahl", "Bitte mindestens eine Messgröße auswählen."
        )
        return None
    return ausgewaehlt


def zeige_auswahl():
    ausgewaehlt = aktuelle_sensorenauswahl()
    if not ausgewaehlt:
        return

    modus = modus_variable.get()
    print("\nAusgewählte Messgrößen:")
    for schluessel in ausgewaehlt:
        print(sensor_name(schluessel), "->", schluessel)

    diagramme_erstellen(ausgewaehlt, modus)


def zeige_wochenanalyse():
    ausgewaehlt = aktuelle_sensorenauswahl()
    if not ausgewaehlt:
        return
    wochenanalyse_erstellen(ausgewaehlt, modus_variable.get())


tk.Button(
    fenster,
    text="Auswahl übernehmen und Tagesdiagramme anzeigen",
    command=zeige_auswahl,
).pack(pady=(8, 3))

tk.Button(
    fenster,
    text="Wochenanalyse erstellen",
    command=zeige_wochenanalyse,
).pack(pady=(3, 12))

fenster.mainloop()
