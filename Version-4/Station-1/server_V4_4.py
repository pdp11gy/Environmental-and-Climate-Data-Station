# Version V4_4: CAM support implemented; live image every 5 minutes
#               and save an image daily at 14:00: /mnt/ssd/cam
# Version V4_3: Radiation station implemented, additionally with UV sensor
# Version V4_2: Change to storage method; see def save_data(data)
# Path: /mnt/ssd/data/
#                └─ 2026_KW24/
#                   └─ 2026-06-15/
#                      └─ daten.json
# Version V4: Layout change, display of data from both stations
# server.py, Version 3: SSD support, externally accessible via ngrok
#                       Password protection: "YourName"/"YourPassword"
# Server program for Raspberry Pi Zero (2) W, weather station project
# Support for MH-Z19C (CO2), SDS011 (fine dust)
#             WS3 (Air+Water+Temperature)      @WeatherStation-1
#             RadiationD-V1.1 (CAJOE) + BMP280 @ Both
#             BME680 (Air+Temperature)         @WeatherStation-2
# Project reference with ChatGPT: CHAPDP11GY-ENV-PICO-2025
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

USERNAME = "DeinName"
PASSWORD = "DeinPassword"
def check_auth(username, password):
    return username == USERNAME and password == PASSWORD
def authenticate():
    return Response(
        'Login erforderlich', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )
def requires_auth(f):
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

app = Flask(__name__)

DATA_PATH = "/mnt/ssd/data/"
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

data_store = {}

from datetime import datetime
import os
import json

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

.container {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px 15px;
    max-width: 700px;
    margin: auto;
}

.container h2 {
    margin-top: 20px;
}

.center {
    grid-column: 1 / span 2;
    display: flex;
    justify-content: center;
}

.value {
    font-size: 16px;
    margin: 3px 0;
}

.stationtitle {
    text-align: center;
    margin-bottom: -5px;
}

.center .value {
    font-size: 20px;
}

.box {
    background: white;
    padding: 10px 15px 15px 15px;  /* oben weniger */
    margin: 0;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.15);
    min-height: 140px;
    text-align: left;
}

.timestamp {
    font-size: 12px;
    color: #666;
    margin-top: 10px;
    border-top: 1px solid #ddd;
    padding-top: 5px;
}

.sensor-footer {
    display: flex;
    justify-content: space-between;
    font-size: 0.85em;
    color: #888;
    margin-top: 8px;
    padding-top: 5px;
    border-top: 1px solid #444;
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

.camera-button {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
}

h1 {
    margin-bottom: 10px;
    text-align: center;
}

h2 {
    margin-top: 0px;
    margin-bottom: 2px;
}

h3 {
    margin: 0 0 6px 0;
}

.value {
    font-size: 20px;
    margin: 5px 0;
}

.center .box {
    border: 2px solid #666;
}

.ok { color: green; }
.warn { color: orange; }
.bad { color: red; }

</style>
</head>

<body>

<div class="header">
    <h1>PDP11GY Umweltstationen</h1>

    <div class="camera-button">
        <a href="/cam" target="_blank">
            <button class="cam-btn">📷 Kamera</button>
        </a>
    </div>
</div>

<!-- Geiger oben -->

<div class="center">
  <div class="box">
    <h3>
      <span style="font-size:24px; color:#c28b00;">☢</span>
      Strahlenstation
    </h3>
    {% set geiger = data.get('station1u2', {}).get('geiger', {}) %}
    {% set usvh = geiger.get('usvh') %}
    {% set cpm = geiger.get('cpm') %}
    <!-- CPM -->
    <div class="value">
      CPM: {{ cpm if cpm is not none else "--" }}
    </div>
    <!-- uSv/h mit Farbe -->
    <div class="value
    {% if usvh is not none %}
        {% if usvh < 0.3 %}ok
        {% elif usvh < 1.0 %}warn
        {% else %}bad
        {% endif %}
    {% endif %}
    ">
      uSv/h: {{ "%.3f"|format(usvh) if usvh is not none else "--" }}
    </div>
    <div class="value">
      UV Raw: {{ "%.0f"|format(geiger.get('uv_raw') or 0) }}
    </div>
    <!-- Temp + Druck -->
    <div class="sensor-footer">
     <span>🌡 {{ "%.1f"|format(geiger.get('temperature') or 0) }} °C</span>
     <span>🌦 {{ "%.1f"|format(geiger.get('pressure') or 0) }} hPa</span>
    </div>
    <!-- ZEIT -->
    <div class="timestamp">
      {{ geiger.get('timestamp') if geiger.get('timestamp') else "kein Signal" }}
    </div>
  </div>
</div>

<!-- GRID -->
<div class="container">

  <!-- TITEL -->
  <div class="stationtitle"><h2>Station-1</h2></div>
  <div class="stationtitle"><h2>Station-2</h2></div>

  <!-- CO2 -->
<div class="box">
  <h3>CO2</h3>
  {% set co2 = data.get('station1', {}).get('co2', {}) %}
  {% set value = co2.get('co2') %}
  <div class="value
  {% if value is not none %}
      {% if value < 800 %}ok
      {% elif value < 1200 %}warn
      {% else %}bad
      {% endif %}
  {% endif %}
  ">
    CO2: {{ value if value else "--" }} ppm
  </div>
  <div class="value">
    {% set t = co2.get('temp') %}
    Temp: {{ "%.1f"|format(t) if t is not none else "--" }} °C
  </div>
  <div class="timestamp">
    {{ co2.get('timestamp') if co2.get('timestamp') else "kein Signal" }}
  </div>
</div>

<div class="box">
  <h3>CO2</h3>
  {% set co2 = data.get('station2', {}).get('co2', {}) %}
  {% set value = co2.get('co2') %}
  <div class="value
  {% if value is not none %}
      {% if value < 800 %}ok
      {% elif value < 1200 %}warn
      {% else %}bad
      {% endif %}
  {% endif %}
  ">
    CO2: {{ value if value else "--" }} ppm
  </div>
  <div class="value">
    {% set t = co2.get('temp') %}
    Temp: {{ "%.1f"|format(t) if t is not none else "--" }} °C
  </div>
  <div class="timestamp">
    {{ co2.get('timestamp') if co2.get('timestamp') else "kein Signal" }}
  </div>
</div>

  <!-- FEINSTAUB -->
<div class="box">
  <h3>Feinstaub</h3>
  {% set dust = data.get('station1', {}).get('Feinstaub', {}) %}
  {% set pm25 = dust.get('pm25') %}
  {% set pm10 = dust.get('pm10') %}
  <!-- PM2.5 -->
  <div class="value
  {% if pm25 is not none %}
      {% if pm25 < 15 %}ok
      {% elif pm25 < 35 %}warn
      {% else %}bad
      {% endif %}
  {% endif %}
  ">
    PM2.5: {{ pm25 if pm25 else "--" }} µg/m³
  </div>
  <!-- PM10 -->
  <div class="value
  {% if pm10 is not none %}
      {% if pm10 < 45 %}ok
      {% elif pm10 < 75 %}warn
      {% else %}bad
      {% endif %}
  {% endif %}
  ">
    PM10: {{ pm10 if pm10 else "--" }} µg/m³
  </div>
  <!-- ZEIT -->
  <div class="timestamp">
    {{ dust.get('timestamp') if dust.get('timestamp') else "kein Signal" }}
  </div>
</div>


<div class="box">
  <h3>Feinstaub</h3>
  {% set dust = data.get('station2', {}).get('Feinstaub', {}) %}
  {% set pm25 = dust.get('pm25') %}
  {% set pm10 = dust.get('pm10') %}
  <!-- PM2.5 -->
  <div class="value
  {% if pm25 is not none %}
      {% if pm25 < 15 %}ok
      {% elif pm25 < 35 %}warn
      {% else %}bad
      {% endif %}
  {% endif %}
  ">
    PM2.5: {{ pm25 if pm25 else "--" }} µg/m³
  </div>
  <!-- PM10 -->
  <div class="value
  {% if pm10 is not none %}
      {% if pm10 < 45 %}ok
      {% elif pm10 < 75 %}warn
      {% else %}bad
      {% endif %}
  {% endif %}
  ">
    PM10: {{ pm10 if pm10 else "--" }} µg/m³
  </div>
  <!-- ZEIT -->
  <div class="timestamp">
    {{ dust.get('timestamp') if dust.get('timestamp') else "kein Signal" }}
  </div>
</div>

  <!-- WS3---- / BME680 -->
  <div class="box">
  <h3>WS3</h3>
  {% set ws3 = data.get('station1', {}).get('ws3', {}) %}
  <div class="value">Temp: {{ "%.1f"|format(ws3.temperature) if ws3.get('temperature') else "--" }} °C</div>
  <div class="value">Hum:  {{ "%.1f"|format(ws3.humidity) if ws3.get('humidity') else "--" }} %</div>

  {% set pressure = ws3.get('pressure') %}
  <!-- Luftdruck -->
  <div class="value
  {% if pressure is not none %}
      {% if pressure < 980 or pressure > 1030 %}warn
      {% else %}ok
      {% endif %}
  {% endif %}
  ">
  Pres: {{ "%.1f"|format(pressure) if pressure is not none else "--" }} hPa
  </div>

  <div class="value">Wind: {{ data.get('station1', {}).get('ws3', {}).get('wind_speed', '--') }} km/h</div>
  <div class="value">Gust: {{ data.get('station1', {}).get('ws3', {}).get('wind_gust', '--') }} km/h</div>
  <!-- ZEIT -->
  <div class="timestamp">
    {{ data.get('station1', {}).get('ws3', {}).get('timestamp', '--') }}
  </div>
 </div>

<div class="box">
  <h3>BME680</h3>
  {% set bme = data.get('station2', {}).get('bme680', {}) %}
  {% set t = bme.get('temperature') %}
  {% set h = bme.get('humidity') %}
  {% set p = bme.get('pressure') %}
  <!-- Temperatur -->
  <div class="value
  {% if t is not none %}
      {% if t < 0 or t > 30 %}warn
      {% else %}ok
      {% endif %}
  {% endif %}
  ">
    Temp: {{ "%.1f"|format(t) if t is not none else "--" }} °C
  </div>
  <!-- Luftfeuchte -->
  <div class="value
  {% if h is not none %}
      {% if h < 30 or h > 70 %}warn
      {% else %}ok
      {% endif %}
  {% endif %}
  ">
    Hum: {{ "%.1f"|format(h) if h is not none else "--" }} %
  </div>
  <!-- Luftdruck -->
  <div class="value
  {% if p is not none %}
      {% if p < 980 or p > 1030 %}warn
      {% else %}ok
      {% endif %}
  {% endif %}
  ">
    Pres: {{ "%.1f"|format(p) if p is not none else "--" }} hPa
  </div>
  <!-- ZEIT -->
  <div class="timestamp">
    {{ bme.get('timestamp') if bme.get('timestamp') else "kein Signal" }}
  </div>
</div>

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


@app.route('/data', methods=['POST'])
def receive():
    try:
        data = request.json

        station = data.get("station", "station1")
        sensor = data.get("sensor", "unknown")

        data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

        if station not in data_store:
            data_store[station] = {}

        data_store[station][sensor] = data

        save_data(data)

        return "OK"

    except Exception as e:
        return str(e), 400

@app.route('/')
@requires_auth
def index():
    return render_template_string(HTML, data=data_store)

app.run(host='0.0.0.0', port=5000)

