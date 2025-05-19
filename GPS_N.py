import serial

# Configuración del puerto serie
GPS_PORT = "/dev/ttyAMA0"  # Ajusta si usas otro puerto
BAUD_RATE = 9600

def ver_datos_gps():
    try:
        with serial.Serial(GPS_PORT, BAUD_RATE, timeout=1) as ser:
            print("Leyendo datos del GPS... (Presiona Ctrl+C para detener)")
            while True:
                linea = ser.readline().decode(errors="ignore").strip()
                if linea:
                    print(linea)
    except serial.SerialException as e:
        print(f"Error al abrir el puerto serial: {e}")

if __name__ == "__main__":
    ver_datos_gps()
