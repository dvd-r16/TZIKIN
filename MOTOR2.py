from gpiozero import OutputDevice
from time import sleep
import keyboard

# Pines del motor de elevaci�n
pul_elev = OutputDevice(17)
dir_elev = OutputDevice(27)

# Pines del motor de azimuth
pul_azim = OutputDevice(22)
dir_azim = OutputDevice(23)

# Tiempo entre pasos
step_delay = 0.005  # 10 ms

print("Controles:")
print("W = Subir (elevaci�n) | S = Bajar (elevaci�n)")
print("A = Izquierda (azimuth) | D = Derecha (azimuth)")
print("Ctrl+C para salir.")

try:
    while True:
        if keyboard.is_pressed('w'):
            print("? Elevaci�n: Subiendo...")
            dir_elev.on()
            while keyboard.is_pressed('w'):
                pul_elev.on()
                sleep(step_delay)
                pul_elev.off()
                sleep(step_delay)
            print("? Elevaci�n detenida (W liberado)")

        elif keyboard.is_pressed('s'):
            print("? Elevaci�n: Bajando...")
            dir_elev.off()
            while keyboard.is_pressed('s'):
                pul_elev.on()
                sleep(step_delay)
                pul_elev.off()
                sleep(step_delay)
            print("? Elevaci�n detenida (S liberado)")

        elif keyboard.is_pressed('a'):
            print("?? Azimuth: Izquierda...")
            dir_azim.off()
            while keyboard.is_pressed('a'):
                pul_azim.on()
                sleep(step_delay)
                pul_azim.off()
                sleep(step_delay)
            print("? Azimuth detenido (A liberado)")

        elif keyboard.is_pressed('d'):
            print("?? Azimuth: Derecha...")
            dir_azim.on()
            while keyboard.is_pressed('d'):
                pul_azim.on()
                sleep(step_delay)
                pul_azim.off()
                sleep(step_delay)
            print("? Azimuth detenido (D liberado)")

        else:
            sleep(0.01)

except KeyboardInterrupt:
    print("\nMovimiento interrumpido por el usuario.")
