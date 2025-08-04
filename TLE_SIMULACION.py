import subprocess
import time
import csv
import json
import os

LOG_FILE = "log_NOAA_19_20250803T155113.csv"
SAT_NAME = "SIMULACION"

def lanzar_motor():
    print("[SIMULADOR] Iniciando MOTOR.py en segundo plano...")
    return subprocess.Popen(["python3", "MOTOR.py"])

def simular_pase():
    print("[SIMULADOR] Simulando pase desde log...")
    with open(LOG_FILE, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Saltar encabezado

        for row in reader:
            timestamp, azim, elev = row

            data = {
                "SAT": SAT_NAME,
                "ELEV": float(elev),
                "AZIM": float(azim),
                "STATUS": "ready"
            }

            with open("next_target.json", "w") as f:
                json.dump(data, f)

            print(f"[SIMULADOR] Enviado → AZIM: {azim}°, ELEV: {elev}°")
            time.sleep(2)

    print("[SIMULADOR] Pase completo simulado.")

if __name__ == "__main__":
    motor_process = lanzar_motor()
    time.sleep(3)  # Tiempo para que MOTOR.py arranque
    simular_pase()

    print("[SIMULADOR] Finalizado. Puedes presionar Ctrl+C para cerrar MOTOR.py si deseas.")
