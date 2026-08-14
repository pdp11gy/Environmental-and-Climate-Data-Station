# test/demo program with matplotlib : Graphical analysis 
# of the WS3 sensor, temperature data : 2026-07-13
import json
from datetime import datetime
import matplotlib.pyplot as plt

DATEI = "/mnt/ssd/data/2026_KW28/2026-07-13/daten.json"

zeiten = []
temperaturen = []

with open(DATEI, "r") as f:
    for zeile in f:
        try:
            daten = json.loads(zeile)
        except:
            continue
        if daten.get("sensor") != "ws3":
            continue

        zeit = datetime.strptime(
            daten["timestamp"],
            "%Y-%m-%d %H:%M:%S"
        )

        temperaturen.append(daten["temperature"])
        zeiten.append(zeit)

plt.figure(figsize=(10,4))
plt.plot(zeiten, temperaturen)
plt.title("Temperaturverlauf")
plt.xlabel("Zeit")
plt.ylabel("°C")
plt.grid(True)
plt.tight_layout()
plt.savefig("/mnt/ssd/diagramme/Temp_heute.png", dpi=150)
plt.close()
print("Diagramm gespeichert.")