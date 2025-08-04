import time
from gpiozero import OutputDevice

# Pines GPIO
pul_azim = OutputDevice(22)
dir_azim = OutputDevice(23)
pul_elev = OutputDevice(17)
dir_elev = OutputDevice(27)

# Parámetros
GRADOS_POR_PASO_ELEV = 0.0908
GRADOS_POR_PASO_AZIM = 0.0781

def mover_motor(pul, dir_pin, grados, grados_por_paso, nombre, invertir_sentido=False):
    if invertir_sentido:
        grados = -grados  # Invierte sentido si se solicita

    pasos = int(abs(grados) / grados_por_paso)
    sentido = 1 if grados >= 0 else -1
    dir_pin.value = sentido > 0
    print(f"[TEST {nombre}] Moviendo {'HORARIO' if sentido > 0 else 'ANTIHORARIO'} {abs(grados):.2f}° → {pasos} pasos")

    for _ in range(pasos):
        pul.on()
        time.sleep(0.001)
        pul.off()
        time.sleep(0.001)

print("\n=== TEST DE MOTOR: AZIMUT (con inversión lógica) ===")
print("1️⃣ Giro HORARIO (ej. hacia la derecha)")
mover_motor(pul_azim, dir_azim, 30.0, GRADOS_POR_PASO_AZIM, "AZIM", invertir_sentido=True)
time.sleep(2)
print("2️⃣ Giro ANTIHORARIO (ej. hacia la izquierda)")
mover_motor(pul_azim, dir_azim, -30.0, GRADOS_POR_PASO_AZIM, "AZIM", invertir_sentido=True)

time.sleep(2)

print("\n=== TEST DE MOTOR: ELEVACIÓN ===")
print("1️⃣ Giro HACIA ARRIBA")
mover_motor(pul_elev, dir_elev, 20.0, GRADOS_POR_PASO_ELEV, "ELEV")
time.sleep(2)
print("2️⃣ Giro HACIA ABAJO")
mover_motor(pul_elev, dir_elev, -20.0, GRADOS_POR_PASO_ELEV, "ELEV")

print("\n✅ TEST FINALIZADO")
