# test/demo program with matplotlib : Graphical analysis 
# of the WS3 sensor, temperature and CO2 data : 2026-07-13
import json
from datetime import datetime
import matplotlib.pyplot as plt

DATEI = "/mnt/ssd/data/2026_KW28/2026-07-13/daten.json"

zeiten_temp = []
temperaturen = []
zeiten_co2 = []
co2_werte = []

with open(DATEI, "r") as f:
    for zeile in f:
        try:
            daten = json.loads(zeile)
        except:
            continue

        zeit = datetime.strptime(
            daten["timestamp"],
            "%Y-%m-%d %H:%M:%S")

        sensor = daten.get("sensor")

        if sensor == "ws3":
            zeiten_temp.append(zeit)
            temperaturen.append(daten["temperature"])

        elif sensor == "co2":
            zeiten_co2.append(zeit)
            co2_werte.append(daten["co2"])

fig, ax1 = plt.subplots(figsize=(12, 5))

#ax1.grid(axis="both", linestyle="--", alpha=0.5)
ax1.grid(axis="x", linestyle="--", alpha=0.5)

ax1.plot(
    zeiten_temp,
    temperaturen,
    label="Temperatur",
    color="blue",
    linewidth=2
)

ax1.tick_params(axis="y", labelcolor="blue")
ax1.set_ylabel("Temperatur °C", color="blue")

ax2 = ax1.twinx()

ax2.plot(
    zeiten_co2,
    co2_werte,
    label="CO₂",
    color="red",
    linewidth=1
)
ax2.tick_params(axis="y", labelcolor="red")
ax2.set_ylabel("CO₂ ppm", color="red")
plt.title("Temperatur und CO₂ – Station-1")
plt.grid(True)
plt.tight_layout()
Ausgabe = "/mnt/ssd/diagramme/temp_co2.png"
plt.savefig(AUSGABE, dpi=150)
plt.show()
print("Diagramm gespeichert.")

