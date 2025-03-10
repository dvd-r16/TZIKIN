import csv
import os
import requests
from datetime import datetime, timedelta, timezone
from skyfield.api import load, wgs84

# Archivos
GPS_FILE = "gps_data.csv"
TLE_FILE = "TLE.txt"
PASSES_FILE = "PASSES.csv"

# Satélites a rastrear
SATELLITES = [
    "NOAA 15", "NOAA 18", "NOAA 19", "METEOR-M2 3", "METEOR-M2 4"
]

# URL para descargar TLE
TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle"

def get_latest_gps():
    """Obtiene las coordenadas más recientes del archivo gps_data.csv"""
    try:
        with open(GPS_FILE, newline='') as csvfile:
            reader = list(csv.reader(csvfile))
            if len(reader) > 1:  # Hay datos disponibles
                lat, lon, alt = map(float, reader[-1])  # Última fila
                return lat, lon, alt
    except FileNotFoundError:
        print("No se encontró gps_data.csv. Usando coordenadas predeterminadas.")
    except Exception as e:
        print(f"Error al leer el archivo GPS: {e}")
    return 14.6349, -90.5069, 1500  # Coordenadas predeterminadas

def download_tle():
    """Descarga el TLE de los satélites si no existe el archivo."""
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
    """Carga los datos TLE desde el archivo TLE.txt"""
    try:
        satellites = load.tle_file(TLE_FILE)
        return {sat.name: sat for sat in satellites if sat.name in SATELLITES}
    except FileNotFoundError:
        print("No se encontró TLE.txt. Descargue los datos primero.")
        return {}

def calculate_passes(tle_data, lat, lon, alt):
    """Calcula los pases visibles de los satélites para los próximos 3 días y los guarda en PASSES.csv"""
    print("Iniciando cálculo de pases...")
    if not tle_data:
        print("No hay datos TLE disponibles para calcular los pases.")
        return
    
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
            rise_az, culm_az, set_az = None, None, None
            max_elevation = 0.0
            
            difference = sat - observer
            topocentric_rise = difference.at(rise_time)
            alt_rise, az_rise, _ = topocentric_rise.altaz()
            rise_az = az_rise.degrees
            
            topocentric_culm = difference.at(culm_time)
            alt_culm, az_culm, _ = topocentric_culm.altaz()
            culm_az, max_elevation = az_culm.degrees, alt_culm.degrees
            
            topocentric_set = difference.at(set_time)
            alt_set, az_set, _ = topocentric_set.altaz()
            set_az = az_set.degrees
            
            if max_elevation < 10:
                continue  # Ignorar pases con culminación menor a 10°
            
            warning = "WARNING" if 10 <= max_elevation < 20 else ""
            
            passes.append([name, rise_time.utc_iso(), f"{rise_az:.2f}", 
                           culm_time.utc_iso(), f"{culm_az:.2f}", f"{max_elevation:.2f}", 
                           set_time.utc_iso(), f"{set_az:.2f}", warning])
    
    passes.sort(key=lambda x: x[1])
    
    with open(PASSES_FILE, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter='|')
        writer.writerow(["Satelite", "Hora de salida (UTC)", "Azimut salida (°)", 
                         "Hora de culminacion (UTC)", "Azimut culminacion (°)", "Elevacion maxima (°)", 
                         "Hora de puesta (UTC)", "Azimut puesta (°)", "Advertencia"])
        writer.writerows(passes)
    
    print(f"Pases calculados y guardados en {PASSES_FILE}.")

lat, lon, alt = get_latest_gps()
download_tle()
tle_data = load_tle()
calculate_passes(tle_data, lat, lon, alt)
