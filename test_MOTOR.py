import time
from gpiozero import OutputDevice

# Configuración de pines
pul_elev = OutputDevice(17)
dir_elev = OutputDevice(27)

pul_azim = OutputDevice(22)
dir_azim = OutputDevice(23)

# Configuración según tu sistema
GRADOS_POR_PASO_ELEV = 0.0908
GRADOS_POR_PASO_AZIM = 0.0781

# Posición inicial
pos_elev = 90.0
pos_azim = 0.0

def mover_motor(pul, dir_pin, delta_grados, grados_por_paso, nombre):
    pasos = int(abs(delta_grados) / grados_por_paso)
    dir_pin.value = delta_grados > 0
    print(f"[{nombre}] Moviendo {'+' if delta_grados > 0 else '-'}{abs(delta_grados):.2f}° ({pasos} pasos)")

    for _ in range(pasos):
        pul.on()
        time.sleep(0.001)
        pul.off()
        time.sleep(0.001)

def mover_elevacion(destino):
    global pos_elev
    destino = max(0, min(180, destino))
    delta = destino - pos_elev
    mover_motor(pul_elev, dir_elev, delta, GRADOS_POR_PASO_ELEV, "ELEV")
    pos_elev = destino

def mover_azimut(destino):
    global pos_azim
    delta = destino - pos_azim
    mover_motor(pul_azim, dir_azim, delta, GRADOS_POR_PASO_AZIM, "AZIM")
    pos_azim = destino

print("[TEST] Iniciando prueba de motores...")

# Elevación: 90 → 0
mover_elevacion(0)
time.sleep(1)

# Elevación: 0 → 180
mover_elevacion(180)
time.sleep(1)

# Elevación: 180 → 90
mover_elevacion(90)
time.sleep(1)

# Azimut: 0 → 180
mover_azimut(180)
time.sleep(1)

# Azimut: 180 → 360
mover_azimut(360)
time.sleep(1)

# Azimut: 360 → 0
mover_azimut(0)
time.sleep(1)

print("[TEST] Prueba finalizada. Motores regresaron a su origen.")
