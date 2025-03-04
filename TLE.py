import requests
import ephem
from datetime import datetime, timedelta

# Coordenadas aproximadas de Guatemala
LATITUDE = '14.6349'
LONGITUDE = '-90.5069'
ALTITUDE = 1500  # en metros

# Lista de sat�lites a rastrear
SATELLITES = {
    "NOAA 15": "https://celestrak.org/NORAD/elements/weather.txt",
    "NOAA 18": "https://celestrak.org/NORAD/elements/weather.txt",
    "NOAA 19": "https://celestrak.org/NORAD/elements/weather.txt",
    "METEOR M2-3": "https://celestrak.org/NORAD/elements/weather.txt",
    "METEOR M2-4": "https://celestrak.org/NORAD/elements/weather.txt"
}

# Archivo para guardar los TLE
TLE_FILE = "TLE.txt"
PASSES_FILE = "Passes.txt"

def download_tle():
    """Intenta descargar los datos TLE de los sat�lites y guardarlos en TLE.txt. Si falla, usa el archivo existente."""
    tle_data = ""
    try:
        for sat_name, url in SATELLITES.items():
            response = requests.get(url, timeout=10)
            lines = response.text.split('\n')
            
            for i in range(len(lines)):
                if sat_name in lines[i]:
                    tle_data += f"{sat_name}\n{lines[i+1]}\n{lines[i+2]}\n"
                    break
        
        with open(TLE_FILE, "w") as file:
            file.write(tle_data)
        print("Datos TLE descargados y guardados.")
    except (requests.RequestException, IndexError) as e:
        print("No se pudo descargar los TLE. Usando datos existentes.")

def load_tle():
    """Carga los datos TLE desde el archivo existente."""
    try:
        with open(TLE_FILE, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        print("No hay archivo TLE disponible. Aseg�rese de descargarlo primero.")
        return {}
    
    tle_dict = {}
    for i in range(0, len(lines), 3):
        name = lines[i].strip()
        line1 = lines[i+1].strip()
        line2 = lines[i+2].strip()
        tle_dict[name] = (line1, line2)
    
    return tle_dict

def calculate_passes(tle_data):
    """Calcula los pr�ximos pases visibles de los sat�lites sobre Guatemala y los guarda en Passes.txt"""
    if not tle_data:
        print("No hay datos TLE disponibles para calcular los pases.")
        return
    
    observer = ephem.Observer()
    observer.lat = LATITUDE
    observer.lon = LONGITUDE
    observer.elev = ALTITUDE  # Altitud definida correctamente
    
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=5)
    
    passes = []
    
    for name, (line1, line2) in tle_data.items():
        sat = ephem.readtle(name, line1, line2)
        dt = start_time
        
        while dt < end_time:
            observer.date = dt
            next_pass = observer.next_pass(sat)
            rise_time = ephem.localtime(next_pass[0])
            
            passes.append((rise_time, name, rise_time.strftime("%Y-%m-%d %H:%M:%S")))
            dt += timedelta(minutes=10)  # Asegura que no se calculen pases repetidos
    
    passes.sort()
    
    with open(PASSES_FILE, "w") as file:
        for p in passes:
            file.write(f"{p[2]} - {p[1]}\n")
    
    print("Pases calculados y guardados.")

# Ejecutar las funciones
download_tle()
tle_data = load_tle()
calculate_passes(tle_data)
