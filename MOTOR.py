import time
import os
import json
import threading
from gpiozero import OutputDevice

# Pines GPIO
pul_elev = OutputDevice(17)
dir_elev = OutputDevice(27)

pul_azim = OutputDevice(22)
dir_azim = OutputDevice(23)

# Constantes de movimiento
GRADOS_POR_PASO_ELEV = 0.0908
GRADOS_POR_PASO_AZIM = 0.0781
PASOS_POR_GRADO_ELEV = 1 / GRADOS_POR_PASO_ELEV
PASOS_POR_GRADO_AZIM = 1 / GRADOS_POR_PASO_AZIM
PASOS_POR_REVOLUCION_AZIM = int(360 * PASOS_POR_GRADO_AZIM)

# Posiciones absolutas iniciales
POSICION_INICIAL_ELEV_GRADOS = 90.0
POSICION_INICIAL_AZIM_GRADOS = 0.0

paso_actual_elev = int(POSICION_INICIAL_ELEV_GRADOS * PASOS_POR_GRADO_ELEV)
paso_actual_azim = int(POSICION_INICIAL_AZIM_GRADOS * PASOS_POR_GRADO_AZIM)


def calcular_delta_circular(paso_actual, paso_deseado, pasos_por_revolucion):
    delta = paso_deseado - paso_actual
    delta = (delta + pasos_por_revolucion // 2) % pasos_por_revolucion - pasos_por_revolucion // 2
    return delta


def mover_a_pasos_absolutos(pul, dir_pin, paso_actual, paso_deseado, nombre, circular=False, pasos_max=None):
    if circular and pasos_max:
        delta = calcular_delta_circular(paso_actual, paso_deseado, pasos_max)
    else:
        delta = paso_deseado - paso_actual

    if delta == 0:
        print(f"[{nombre}] Ya en posición. No se mueve.")
        return paso_actual

    dir_pin.value = delta > 0
    print(f"[{nombre}] Moviendo {abs(delta)} pasos hacia {'+' if delta > 0 else '-'}")

    for _ in range(abs(delta)):
        pul.on()
        time.sleep(0.001)
        pul.off()
        time.sleep(0.001)

    return (paso_actual + delta) % pasos_max if circular and pasos_max else paso_deseado


def mover_elevacion_a(grados_destino):
    global paso_actual_elev
    if grados_destino < 10:
        print(f"[ELEV] Elevación mínima es 10°. Ajustando.")
        grados_destino = 10.0
    elif grados_destino > 180:
        print(f"[ELEV] Elevación máxima es 180°. Ajustando.")
        grados_destino = 180.0

    paso_deseado = int(grados_destino * PASOS_POR_GRADO_ELEV)
    paso_actual_elev = mover_a_pasos_absolutos(pul_elev, dir_elev, paso_actual_elev, paso_deseado, "ELEV")


def mover_azimut_a(grados_destino):
    global paso_actual_azim
    paso_deseado = int(grados_destino * PASOS_POR_GRADO_AZIM)
    paso_actual_azim = mover_a_pasos_absolutos(
        pul_azim, dir_azim, paso_actual_azim, paso_deseado, "AZIM",
        circular=True, pasos_max=PASOS_POR_REVOLUCION_AZIM
    )


def guardar_estado_motor():
    estado = {
        "paso_elev": paso_actual_elev,
        "paso_azim": paso_actual_azim
    }
    with open("estado_motor.json", "w") as f:
        json.dump(estado, f)
    print("[MOTOR] Estado guardado en estado_motor.json.")


def cargar_estado_motor():
    global paso_actual_elev, paso_actual_azim
    if not os.path.exists("estado_motor.json"):
        print("[MOTOR] No se encontró estado_motor.json, usando valores por defecto.")
        return
    with open("estado_motor.json", "r") as f:
        estado = json.load(f)
        paso_actual_elev = estado.get("paso_elev", paso_actual_elev)
        paso_actual_azim = estado.get("paso_azim", paso_actual_azim)
    print(f"[MOTOR] Estado restaurado: elev={paso_actual_elev}, azim={paso_actual_azim}")


def volver_por_donde_vino():
    if not os.path.exists("estado_motor.json"):
        print("[MOTOR] No hay estado previo. Volviendo a HOME normal.")
        volver_a_home()
        return

    with open("estado_motor.json", "r") as f:
        estado = json.load(f)
        paso_deseado_elev = estado["paso_elev"]
        paso_deseado_azim = estado["paso_azim"]

    print("[MOTOR] Regresando por el mismo camino al punto inicial del pase...")

    def mover_elev_reverso():
        global paso_actual_elev
        paso_actual_elev = mover_a_pasos_absolutos(
            pul_elev, dir_elev, paso_actual_elev, paso_deseado_elev, "ELEV"
        )

    def mover_azim_reverso():
        global paso_actual_azim
        paso_actual_azim = mover_a_pasos_absolutos(
            pul_azim, dir_azim, paso_actual_azim, paso_deseado_azim, "AZIM",
            circular=True, pasos_max=PASOS_POR_REVOLUCION_AZIM
        )

    t1 = threading.Thread(target=mover_elev_reverso)
    t2 = threading.Thread(target=mover_azim_reverso)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("[MOTOR] Regreso completo.")


def calibrar_azimut_inicial():
    global paso_actual_azim
    print("[MOTOR] Calibrando azimut inicial: girando -90° hacia el oeste...")
    pasos_90 = int(90 * PASOS_POR_GRADO_AZIM)
    dir_azim.value = False
    for _ in range(pasos_90):
        pul_azim.on()
        time.sleep(0.001)
        pul_azim.off()
        time.sleep(0.001)
    paso_actual_azim = 0
    time.sleep(2)


def volver_a_home():
    global paso_actual_elev, paso_actual_azim
    print("[MOTOR] Volviendo a posición HOME (AZIM=0°, ELEV=90°)...")
    t1 = threading.Thread(target=mover_elevacion_a, args=(90.0,))
    t2 = threading.Thread(target=mover_azimut_a, args=(0.0,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("[MOTOR] HOME alcanzado.")


# ----------------------------
print("[MOTOR] Sistema de posicionamiento absoluto iniciado.")
calibrar_azimut_inicial()
# cargar_estado_motor()  # <-- Puedes descomentar esta línea si quieres que recuerde posición tras reinicio

while True:
    if os.path.exists("next_target.json"):
        try:
            with open("next_target.json", "r") as f:
                datos = json.load(f)

            if datos.get("STATUS") != "ready":
                time.sleep(0.5)
                continue

            sat = datos.get("SAT", "SAT")
            elev_destino = datos.get("ELEV", POSICION_INICIAL_ELEV_GRADOS)
            azim_destino = datos.get("AZIM", POSICION_INICIAL_AZIM_GRADOS)

            print(f"[MOTOR] Nuevo objetivo: {sat}")
            print(f" - Elevación objetivo: {elev_destino:.2f}°")
            print(f" - Azimut objetivo:    {azim_destino:.2f}°")

            t1 = threading.Thread(target=mover_elevacion_a, args=(elev_destino,))
            t2 = threading.Thread(target=mover_azimut_a, args=(azim_destino,))
            t1.start()
            t2.start()
            t1.join()
            t2.join()

            guardar_estado_motor()

            datos["STATUS"] = "done"
            with open("next_target.json", "w") as f:
                json.dump(datos, f)

            print("[MOTOR] Movimiento completado. STATUS actualizado a 'done'.")

        except Exception as e:
            print(f"[MOTOR] Error al procesar next_target.json: {e}")

    elif os.path.exists("reset.flag"):
        print("[MOTOR] Pase finalizado. Regresando por el mismo camino...")
        volver_por_donde_vino()
        os.remove("reset.flag")
        print("[MOTOR] Esperando el siguiente pase...")
        time.sleep(5)

    time.sleep(0.5)
