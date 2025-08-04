from gpiozero import OutputDevice
from time import sleep
import keyboard

# Pines del motor de elevación
pul_elev = OutputDevice(17)
dir_elev = OutputDevice(27)

# Pines del motor de azimuth
pul_azim = OutputDevice(22)
dir_azim = OutputDevice(23)

# Tiempo entre pasos
step_delay = 0.002  # 5 ms

# Configuración de pasos (ajusta según tu sistema mecánico)
GRADOS_POR_PASO_ELEV = 0.0908
GRADOS_POR_PASO_AZIM = 0.0781

# Contadores
pulsos_elev = 0
angulo_elev = 90.0  # ← La antena parte desde 90° hacia arriba

pulsos_azim = 0
angulo_azim = 0.0  # Azimuth empieza desde 0° (puedes cambiarlo si es necesario)

print("Controles:")
print("W = Subir (elevación) | S = Bajar (elevación)")
print("A = Izquierda (azimuth) | D = Derecha (azimuth)")
print("Ctrl+C para salir.")

try:
    while True:
        if keyboard.is_pressed('w'):
            print("↑ Elevación: Subiendo...")
            dir_elev.on()
            while keyboard.is_pressed('w'):
                pul_elev.on()
                sleep(step_delay)
                pul_elev.off()
                sleep(step_delay)
                pulsos_elev += 1
                angulo_elev = 90.0 + pulsos_elev * GRADOS_POR_PASO_ELEV
                print(f"Pulsos Elev: {pulsos_elev} | Ángulo ≈ {angulo_elev:.2f}°", end='\r')
            print("\nElevación detenida (W liberado)")

        elif keyboard.is_pressed('s'):
            print("↓ Elevación: Bajando...")
            dir_elev.off()
            while keyboard.is_pressed('s'):
                pul_elev.on()
                sleep(step_delay)
                pul_elev.off()
                sleep(step_delay)
                pulsos_elev -= 1
                angulo_elev = 90.0 + pulsos_elev * GRADOS_POR_PASO_ELEV
                print(f"Pulsos Elev: {pulsos_elev} | Ángulo ≈ {angulo_elev:.2f}°", end='\r')
            print("\nElevación detenida (S liberado)")

        elif keyboard.is_pressed('a'):
            print("← Azimuth: Izquierda...")
            dir_azim.off()
            while keyboard.is_pressed('a'):
                pul_azim.on()
                sleep(step_delay)
                pul_azim.off()
                sleep(step_delay)
                pulsos_azim -= 1
                angulo_azim = pulsos_azim * GRADOS_POR_PASO_AZIM
                print(f"Pulsos Azim: {pulsos_azim} | Ángulo ≈ {angulo_azim:.2f}°", end='\r')
            print("\nAzimuth detenido (A liberado)")

        elif keyboard.is_pressed('d'):
            print("→ Azimuth: Derecha...")
            dir_azim.on()
            while keyboard.is_pressed('d'):
                pul_azim.on()
                sleep(step_delay)
                pul_azim.off()
                sleep(step_delay)
                pulsos_azim += 1
                angulo_azim = pulsos_azim * GRADOS_POR_PASO_AZIM
                print(f"Pulsos Azim: {pulsos_azim} | Ángulo ≈ {angulo_azim:.2f}°", end='\r')
            print("\nAzimuth detenido (D liberado)")

        else:
            sleep(0.01)

except KeyboardInterrupt:
    print("\n\n✅ Movimiento interrumpido por el usuario.")
    print(f"→ Elevación final: {pulsos_elev} pulsos ≈ {angulo_elev:.2f}°")
    print(f"→ Azimuth final: {pulsos_azim} pulsos ≈ {angulo_azim:.2f}°")
