import csv
import os
import requests
import time
import json
import subprocess
from datetime import datetime, timedelta, timezone
from skyfield.api import load, wgs84

# Archivos
GPS_FILE = "gps_data.csv"
TLE_FILE = "TLE.txt"
PASSES_FILE = "PASSES.csv"
TARGET_FILE = "next_target.json"

# Satélites a rastrear
SATELLITES = [
    "NOAA 15", "NOAA 18", "NOAA 19", "METEOR-M2 3", "METEOR-M2 4"
]

# URL para descargar TLE
TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle"

# Asegurarse de que la carpeta de logs exista
os.makedirs("logs", exist_ok=True)

def get_latest_gps():
    try:
        with open(GPS_FILE, newline='') as csvfile:
            reader = list(csv.reader(csvfile))
            if len(reader) > 1:
                lat, lon, alt = map(float, reader[-1])
                return lat, lon, alt
    except FileNotFoundError:
        print("No se encontró gps_data.csv. Usando coordenadas predeterminadas.")
    except Exception as e:
        print(f"Error al leer el archivo GPS: {e}")
    return 14.6349, -90.5069, 1500

def download_tle():
    if os.path.exists(TLE_FILE):
        print("TLE.txt ya existe. Usando datos almacenados.")
        return
    try:
        response = requests.get(TLE_URL)
        response.raise_for_status()
        with open(TLE_FILE, "w") as file:
            file.write(response.text)
        print("TLE descargado y guardado en TLE.txt")
    except requests.RequestException as e:
        print(f"Error al descargar TLE: {e}")

def load_tle():
    try:
        satellites = load.tle_file(TLE_FILE)
        return {sat.name: sat for sat in satellites if sat.name in SATELLITES}
    except FileNotFoundError:
        print("No se encontró TLE.txt. Descargue los datos primero.")
        return {}

def calculate_passes(tle_data, lat, lon, alt):
    print("Iniciando cálculo de pases...")
    if not tle_data:
        print("No hay datos TLE disponibles para calcular los pases.")
        return []
    
    observer = wgs84.latlon(lat, lon, alt)
    ts = load.timescale()
    start_time = ts.now()
    end_time = ts.utc(datetime.now(timezone.utc) + timedelta(days=3))
    passes = []
    
    for name, sat in tle_data.items():
        print(f"Calculando pases para {name}...")
        times, events = sat.find_events(observer, start_time, end_time, altitude_degrees=0.0)
        
        for i in range(len(times) - 2):
            rise_time, culm_time, set_time = times[i], times[i+1], times[i+2]
            difference = sat - observer
            topocentric_culm = difference.at(culm_time)
            alt_culm, _, _ = topocentric_culm.altaz()
            max_elevation = alt_culm.degrees

            if max_elevation < 10:
                continue

            passes.append([name, rise_time.utc_iso(), set_time.utc_iso(), f"{max_elevation:.2f}"])
    
    passes.sort(key=lambda x: x[1])

    # Guardar en PASSES.csv
    with open(PASSES_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Satélite", "Inicio", "Fin", "AlturaMax"])
        writer.writerows(passes)

    return passes

def write_target_json(name, sat, t, observer):
    difference = sat - observer
    topocentric = difference.at(t)
    elev, azim, _ = topocentric.altaz()
    elevacion = max(elev.degrees, 0.0)
    azimut = azim.degrees

    data = {
        "SAT": name,
        "ELEV": round(elevacion, 2),
        "AZIM": round(azimut, 2),
        "STATUS": "ready"
    }

    with open(TARGET_FILE, "w") as f:
        json.dump(data, f)

    print(f"[TLE] next_target.json creado: {data}")

def track_satellites(passes, tle_data, lat, lon, alt):
    ts = load.timescale()
    observer = wgs84.latlon(lat, lon, alt)

    while passes:
        now = datetime.now(timezone.utc)
        found_active = False

        for i, (name, rise_time, set_time, _) in enumerate(passes):
            rise_dt = datetime.fromisoformat(rise_time.replace('Z', '')).replace(tzinfo=timezone.utc)
            set_dt = datetime.fromisoformat(set_time.replace('Z', '')).replace(tzinfo=timezone.utc)

            if now > set_dt:
                print(f"{name} ya pasó. Eliminando de la lista...")
                passes.pop(i)
                break

            elif (rise_dt - now).total_seconds() <= 60 and now < rise_dt:
                print(f"[TLE] Generando JSON para {name} (1 min antes del pase)...")
                sat = tle_data.get(name)
                if sat:
                    t_predicho = ts.from_datetime(rise_dt)
                    write_target_json(name, sat, t_predicho, observer)
                while datetime.now(timezone.utc) < rise_dt:
                    time.sleep(1)
                break

            elif rise_dt <= now <= set_dt:
                sat = tle_data.get(name)
                if not sat:
                    print(f"No se encontró TLE para {name}. Omitiendo...")
                    passes.pop(i)
                    break

                print(f"{name} en seguimiento en tiempo real...")

                # Inicializar log del pase
                log_filename = f"log_{name.replace(' ', '_')}_{rise_dt.strftime('%Y%m%dT%H%M%S')}.csv"
                log_data = [["UTC", "Azimut", "Altitud"]]

                while datetime.now(timezone.utc) < set_dt:
                    t = ts.now()
                    difference = sat - observer
                    topocentric = difference.at(t)
                    alt, az, _ = topocentric.altaz()
                    elev = max(alt.degrees, 0.0)
                    azim = az.degrees

                    print(f"{datetime.now(timezone.utc).isoformat()} | {name} | Azimut: {azim:.2f}° | Altitud: {elev:.2f}°")

                    data = {
                        "SAT": name,
                        "ELEV": round(elev, 2),
                        "AZIM": round(azim, 2),
                        "STATUS": "ready"
                    }

                    with open("next_target.json", "w") as f:
                        json.dump(data, f)

                    log_data.append([datetime.now(timezone.utc).isoformat(), f"{azim:.2f}", f"{elev:.2f}"])

                    time.sleep(2)

                # Guardar log al finalizar el pase
                with open(os.path.join("logs", log_filename), "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerows(log_data)

                print(f"[LOG] Pase registrado en logs/{log_filename}")

                with open("reset.flag", "w") as f:
                    f.write("RESET=TRUE\n")

                print(f"{name} ha pasado. Eliminando de la lista...")
                passes.pop(i)
                found_active = True
                break

        if not found_active and passes:
            next_rise = datetime.fromisoformat(passes[0][1].replace('Z', '')).replace(tzinfo=timezone.utc)
            print(f"Esperando la aparición de {passes[0][0]} a las {next_rise.isoformat()} UTC...")
            while datetime.now(timezone.utc) < next_rise:
                time.sleep(1)

    print("No hay más satélites por rastrear.")

# --- Flujo principal ---
lat, lon, alt = get_latest_gps()
download_tle()
tle_data = load_tle()
passes = calculate_passes(tle_data, lat, lon, alt)

print("Iniciando MOTOR.py en segundo plano...")
motor_process = subprocess.Popen(["python3", "MOTOR.py"])
time.sleep(2)

# Generar primer objetivo desde ahora (sin esperar)
if passes:
    name, rise_time, set_time, _ = passes[0]
    ts = load.timescale()
    observer = wgs84.latlon(lat, lon, alt)
    sat = tle_data.get(name)

    if sat:
        now = datetime.now(timezone.utc)
        rise_dt = datetime.fromisoformat(rise_time.replace('Z', '')).replace(tzinfo=timezone.utc)
        if now <= datetime.fromisoformat(set_time.replace('Z', '')).replace(tzinfo=timezone.utc):
            t_init = ts.from_datetime(rise_dt if now < rise_dt else now)
            write_target_json(name, sat, t_init, observer)
else:
    print("No hay pases disponibles para enviar.")

track_satellites(passes, tle_data, lat, lon, alt)
