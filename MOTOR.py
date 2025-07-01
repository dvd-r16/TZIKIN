from gpiozero import OutputDevice
from time import sleep

# Pines GPIO
pul = OutputDevice(17)  # Pin de pulso
dir = OutputDevice(27)  # Pin de direcci�n

# Direcci�n inicial
dir.off()  # Cambia a dir.off() para invertir

print("Movimiento del motor paso a paso...")

try:
    while True:
        pul.on()
        sleep(0.001)  # 1ms encendido
        pul.off()
        sleep(0.001)  # 1ms apagado
except KeyboardInterrupt:
    print("\nMovimiento interrumpido.")
