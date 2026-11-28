# Version V2_5: Implementation of charts (in progress/preparation)
# Version V2_4: CAM support implemented, live image every 5 minutes
#               and image saved daily at 14:00: /mnt/ssd/cam
# Version V2_3: Radiation station implemented, with additional UV sensor
# Version V2_2: Changes to storage method; see def save_data(data)
# Path: /mnt/ssd/data/
#                └─ 2026_KW24/
#                   └─ 2026-06-15/
#                      └─ daten.json
# Server program for Raspberry Pi Zero (2) W, weather station project
# Support for MH-Z19C (CO2), SDS011 (fine dust)
#             WS3 (air + water + temperature) 	@WeatherStation-1
#             RadiationD-V1.1 (CAJOE) + BMP280  @ Both
#             BME680 (air + temperature)            @WeatherStation-2
#  Project reference with ChatGPT:  CHAPDP11GY-ENV-PICO-2025
#  https://pdp11gy.com/Climatestation.html
#             www.pdp11gy.com   E-mail: info@pdp11gy.com
# ------------------------------------------------------------------
from flask import Flask, request, render_template_string
from datetime import datetime
import time
import os
import json
from flask import Response
from flask import send_file

app = Flask(__name__)

DATA_PATH = "/mnt/ssd/data/"
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

data_store = {}

def save_data(data):
    try:
        now = datetime.now()
        kw = now.strftime("%Y_KW%W")
        datum = now.strftime("%Y-%m-%d")
        ordner = os.path.join(
            DATA_PATH,
            kw,
            datum
        )
        os.makedirs(ordner, exist_ok=True)
        filename = os.path.join(
            ordner,
            "daten.json"
        )
        with open(filename, "a") as f:
            json.dump(data, f)
            f.write("\n")
    except Exception as e:
        print("Speicherfehler:", e)


HTML = """
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="5">
<title>PDP11GY Umweltstation</title>

<style>
body {
    font-family: Arial;
    background: #e6ecf0;
}

.box {
    background: white;
    padding: 15px;
    margin: 15px auto;   /* statt nur 15px */
    border-radius: 10px;
    box-shadow: 0 0 8px #bbb;
    width: 300px;
}

.header {
    position: relative;
    height: 60px;
}

.header h1 {
    text-align: center;
    margin: 0;
    line-height: 60px;
}

.header-buttons {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    gap: 10px;
}

h1 {
    margin-bottom: 10px;
    text-align: center;
}


h2 {
    margin-top: 0;
}

.value {
    font-size: 20px;
    margin: 5px 0;
}

.ok { color: green; }
.warn { color: orange; }
.bad { color: red; }

</style>
</head>

<body>

<div class="header">
    <h1>PDP11GY Umweltstation-2</h1>
    <div class="header-buttons">
        <a href="/cam" target="_blank">
            <button class="cam-btn">📷 Kamera</button>
        </a>
        <a href="/diagramm" target="_blank">
            <button class="cam-btn">📊 Diagramme</button>
        </a>
    </div>
</div>

{% for key, val in data.items() %}
<div class="box">

<h2>{{key}}</h2>

{% if val.sensor == "co2" %}
<div class="value
{% if val.co2 < 800 %}ok
{% elif val.co2 < 1200 %}warn
{% else %}bad
{% endif %}">
CO2: {{val.co2}} ppm
</div>
<div class="value">Temp: {{val.temp}} °C</div>

{% elif val.sensor == "Feinstaub" %}
<div class="value
{% if val.pm25 < 15 %}ok
{% elif val.pm25 < 35 %}warn
{% else %}bad
{% endif %}">
PM2.5: {{val.pm25}} µg/m³
</div>
<div class="value
{% if val.pm10 < 45 %}ok
{% elif val.pm10 < 75 %}warn
{% else %}bad
{% endif %}">
PM10 : {{val.pm10}} µg/m³
</div>

{% elif val.sensor == "ws3" %}
<div class="value">Temp: {{ "%.1f"|format(val.temperature) }} °C</div>
<div class="value">Hum:  {{val.humidity}} %</div>
<div class="value">Pres: {{val.pressure}} hPa</div>
<div class="value">Wind: {{val.wind_speed}} km/h</div>
<div class="value">Gust: {{val.wind_gust}} km/h</div>
<div class="value">RainR: {{val.rain_rate}} </div>
<div class="value">RainT: {{val.rain_total}} </div>

{% elif val.sensor == "bme680" %}
<div class="value">Temp: {{ "%.1f"|format(val.temperature) }} °C</div>
<div class="value">Hum:  {{ "%.1f"|format(val.humidity) }} %</div>
<div class="value">Pres: {{ "%.1f"|format(val.pressure) }} hPa</div>

{% elif val.sensor == "geiger" %}
<h3>
  <span style="font-size:24px; color:#c28b00;">☢</span>
  Strahlenstation
</h3>
<div class="value">CPM:  {{ "%.1f"|format(val.cpm) }} </div>
<div class="value">uSv/h: {{ "%.3f"|format(val.usvh) }}</div>
<div class="value">UV-raw: {{val.uv_raw}}</div>
<div class="value">Temp: {{ "%.1f"|format(val.temperature) }} °C</div>
<div class="value">Pres: {{ "%.1f"|format(val.pressure) }} hPa</div>

{% else %}
<pre>{{val}}</pre>
{% endif %}

<hr>
<div style="font-size:12px;">{{val.timestamp}}</div>

</div>
{% endfor %}

</body>
</html>
"""
@app.route('/cam')
def cam():
    return '''
    <html>
    <head>
        <title>PDP11GY Kamera</title>
        <meta http-equiv="refresh" content="30">
    </head>

    <body style="text-align:center;">
        <h2>PDP11GY Kamera</h2>
        <img src="/cam_image" width="900">
        <p>Automatische Aktualisierung alle 5 Minuten</p>
    </body>
    </html>
    '''

@app.route('/cam_image')
def cam_image():
    return send_file("/mnt/ssd/cam/bild.jpg", mimetype='image/jpeg')

@app.route('/diagramm')
def diagramm():
    return """
    <html>
    <head>
        <title>PDP11GY Diagramme</title>
        <style>
            body {
                font-family: Arial;
                text-align: center;
                margin-top: 100px;
                background-color: #f0f0f0;
            }

            .box {
                background: white;
                width: 400px;
                margin: auto;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 8px #bbb;
            }
        </style>
    </head>

    <body>
        <div class="box">
            <h2>📊 Diagrammauswertung</h2>
            <h3>In Bearbeitung</h3>
            <p>Die Auswertung der Sensordaten wird vorbereitet.</p>
            <p>Hinweise/Anregungen gerne an info@pdp11gy.com</p>
        </div>
    </body>
    </html>
    """

@app.route('/data', methods=['POST'])
def receive():
    try:
        data = request.json
        sensor = data.get("sensor", "unknown")
        data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        data_store[sensor] = data
        save_data(data)
        return "OK"
    except Exception as e:
        return str(e), 400

@app.route('/')
def index():
    return render_template_string(HTML, data=data_store)

app.run(host='0.0.0.0', port=5000)
