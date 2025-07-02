import time
import os
from gpiozero import OutputDevice

# Configuración de pines GPIO
pul_elev = OutputDevice(17)
dir_elev = OutputDevice(27)

pul_azim = OutputDevice(22)
dir_azim = OutputDevice(23)

# Configuración de pasos (ajusta según tu sistema mecánico)
GRADOS_POR_PASO_ELEV = 0.1125  # ejemplo: 1.8°/16 microsteps → 0.1125°
GRADOS_POR_PASO_AZIM = 0.1125

# Posiciones actuales
POSICION_INICIAL_ELEV = 90.0
POSICION_INICIAL_AZIM = 0.0
posicion_actual_elev = POSICION_INICIAL_ELEV
posicion_actual_azim = POSICION_INICIAL_AZIM

def mover_motor(pul, dir_pin, grados, grados_por_paso, nombre):
    pasos = int(abs(grados) / grados_por_paso)
    sentido = 1 if grados >= 0 else -1
    dir_pin.value = sentido > 0
    print(f"[MOTOR {nombre}] Moviendo {'+' if sentido > 0 else '-'}{abs(grados):.2f}° → {pasos} pasos")

    for _ in range(pasos):
        pul.on()
        time.sleep(0.001)
        pul.off()
        time.sleep(0.001)

def mover_elevacion_a(grados_destino):
    global posicion_actual_elev
    delta = grados_destino - posicion_actual_elev
    mover_motor(pul_elev, dir_elev, delta, GRADOS_POR_PASO_ELEV, "ELEV")
    posicion_actual_elev = grados_destino

def mover_azimut_a(grados_destino):
    global posicion_actual_azim
    delta = grados_destino - posicion_actual_azim
    mover_motor(pul_azim, dir_azim, delta, GRADOS_POR_PASO_AZIM, "AZIM")
    posicion_actual_azim = grados_destino

def leer_flag(file):
    datos = {}
    with open(file, "r") as f:
        for linea in f:
            if '=' in linea:
                k, v = linea.strip().split('=')
                datos[k] = float(v)
    return datos

def guardar_deltas(delta_elev, delta_azim):
    with open("last_position.flag", "w") as f:
        f.write(f"DELTA_ELEV={delta_elev:.2f}\n")
        f.write(f"DELTA_AZIM={delta_azim:.2f}\n")

def volver_por_el_mismo_camino():
    if os.path.exists("last_position.flag"):
        datos = leer_flag("last_position.flag")
        delta_elev = datos.get("DELTA_ELEV", 0.0)
        delta_azim = datos.get("DELTA_AZIM", 0.0)

        destino_elev = posicion_actual_elev - delta_elev
        destino_azim = posicion_actual_azim - delta_azim

        print("[MOTOR] Regresando por el mismo camino...")
        mover_elevacion_a(destino_elev)
        mover_azimut_a(destino_azim)

        os.remove("last_position.flag")
    else:
        print("[MOTOR] No se encontró trayectoria previa. Volviendo al HOME.")
        mover_elevacion_a(POSICION_INICIAL_ELEV)
        mover_azimut_a(POSICION_INICIAL_AZIM)

print("[MOTOR] Monitoreo activo iniciado...")

while True:
    if os.path.exists("next_target.flag"):
        datos = leer_flag("next_target.flag")
        sat = datos.get("SAT", "SAT")
        elev_destino = datos.get("ELEV", POSICION_INICIAL_ELEV)
        azim_destino = datos.get("AZIM", POSICION_INICIAL_AZIM)

        print(f"[MOTOR] Nuevo objetivo: {sat}")
        print(f" - Elevación objetivo: {elev_destino}°")
        print(f" - Azimut objetivo:    {azim_destino}°")

        delta_elev = elev_destino - posicion_actual_elev
        delta_azim = azim_destino - posicion_actual_azim

        guardar_deltas(delta_elev, delta_azim)

        mover_elevacion_a(elev_destino)
        mover_azimut_a(azim_destino)

        os.remove("next_target.flag")

    elif os.path.exists("reset.flag"):
        print("[MOTOR] Pase finalizado. Regresando...")
        volver_por_el_mismo_camino()
        os.remove("reset.flag")

    time.sleep(1)
