import ephem
import csv
import os
import requests
from datetime import datetime, timezone, timedelta

# Archivos
GPS_FILE = "gps_data.csv"
TLE_FILE = "TLE.txt"
PASSES_FILE = "PASSES.csv"

# Sat�lites a rastrear
SATELLITES = [
    "NOAA 15", "NOAA 18", "NOAA 19", "METEOR-M2 3", "METEOR-M2 4"
]

# URL para descargar TLE
TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle"

def get_latest_gps():
    """Obtiene las coordenadas m�s recientes del archivo gps_data.csv"""
    try:
        with open(GPS_FILE, newline='') as csvfile:
            reader = list(csv.reader(csvfile))
            if len(reader) > 1:  # Hay datos disponibles
                lat, lon, alt = map(float, reader[-1])  # �ltima fila
                return lat, lon, alt
    except FileNotFoundError:
        print("No se encontr� gps_data.csv. Usando coordenadas predeterminadas.")
    except Exception as e:
        print(f"Error al leer el archivo GPS: {e}")
    return 14.6349, -90.5069, 1500  # Coordenadas predeterminadas

def download_tle():
    """Descarga el TLE de los sat�lites si el archivo TLE.txt no existe."""
    if os.path.exists(TLE_FILE):
        print("TLE.txt ya existe. Procediendo con el c�lculo de pases.")
        return load_tle()
    
    try:
        response = requests.get(TLE_URL)
        response.raise_for_status()
        tle_data = response.text.splitlines()
        
        with open(TLE_FILE, "w") as file:
            writing = None
            for line in tle_data:
                if any(line.startswith(sat) for sat in SATELLITES):
                    writing = line
                    file.write(line + "\n")
                elif writing and line.startswith('1 '):
                    file.write(line + "\n")
                    writing = None
        print("TLE descargado y guardado en TLE.txt")
    except requests.RequestException as e:
        print(f"Error al descargar TLE: {e}")

def load_tle():
    """Carga los datos TLE desde el archivo TLE.txt"""
    try:
        with open(TLE_FILE, "r") as file:
            lines = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        print("No se encontr� TLE.txt. Descargue los datos primero.")
        return {}
    
    tle_dict = {}
    for i in range(0, len(lines), 3):
        try:
            name = lines[i]
            line1 = lines[i+1]
            line2 = lines[i+2]
            tle_dict[name] = (line1, line2)
        except IndexError:
            print(f"Datos incompletos para {name}")
    
    return tle_dict

def calculate_passes(tle_data, lat, lon, alt):
    print("Iniciando c�lculo de pases...")
    if not tle_data:
        print("No hay datos TLE disponibles para calcular los pases.")
        return
    
    print("Configurando observador...")
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.elev = alt

    print("Obteniendo tiempo de inicio...")
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(days=3)
    passes = []
    seen_passes = set()
    
    print("Iterando sobre sat�lites...")
    for name, (line1, line2) in tle_data.items():
        print(f"Calculando pases para {name}...")
        sat = ephem.readtle(name, line1, line2)
                dt = start_time.replace(tzinfo=None)
        attempt_counter = 0
        last_pass_time = None  # Para detectar bloqueos

        while dt < end_time and attempt_counter < 10:  # M�ximo 10 intentos
            print(f"Estableciendo fecha de observaci�n: {dt}")
            observer.date = ephem.Date(dt)
            print(f"Observador actualizado a la fecha: {observer.date}")
            try:
                print("Buscando pr�ximo pase...")
                next_pass = observer.next_pass(sat)
                print(f"Pr�ximo pase para {name}: {next_pass}")
                
                if not next_pass or (last_pass_time and next_pass[0] == last_pass_time):
                    print(f"No se encontr� pase v�lido o el pase es repetido para {name}. Avanzando tiempo...")
                    attempt_counter += 1
                    dt += timedelta(hours=2)
                    continue
                
                                last_pass_time = next_pass[0].datetime().replace(tzinfo=None)
                rise_time = ephem.localtime(next_pass[0])
                set_time = ephem.localtime(next_pass[4])
                max_elevation = next_pass[3] * (180.0 / ephem.pi)
                azimuth_entry = next_pass[1] * (180.0 / ephem.pi)
                azimuth_exit = next_pass[5] * (180.0 / ephem.pi)
                
                if max_elevation < 10:
                    dt = set_time + timedelta(minutes=1)
                    continue
                
                warning = "WARNING" if 10 <= max_elevation < 20 else ""
                pase_unico = (name, rise_time.strftime('%Y-%m-%d %H:%M:%S'))
                
                if pase_unico not in seen_passes:
                    passes.append([
                        name, rise_time.strftime('%Y-%m-%d %H:%M:%S'),
                        f"{max_elevation:.2f}", f"{azimuth_entry:.2f}",
                        f"{azimuth_exit:.2f}", warning
                    ])
                    seen_passes.add(pase_unico)
                
                dt = set_time + timedelta(minutes=1)
            except (ValueError, ephem.CircumpolarError) as e:
                print(f"Error al calcular pase para {name}: {e}")
                attempt_counter += 1
                dt += timedelta(hours=1)
                continue
    
    passes.sort(key=lambda x: x[1])
    
    with open(PASSES_FILE, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Sat�lite", "Hora de salida (UTC)", "Elevaci�n m�xima", "Azimut de entrada", "Azimut de salida", "Advertencia"])
        writer.writerows(passes)
    
    print(f"Finalizado c�lculo de pases. Datos guardados en {PASSES_FILE}.")
    remove_duplicates()

lat, lon, alt = get_latest_gps()
download_tle()
tle_data = load_tle()
calculate_passes(tle_data, lat, lon, alt)
remove_duplicates()
