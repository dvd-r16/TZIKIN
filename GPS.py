import serial
import pynmea2
import csv

# Configuraci�n del puerto serie
GPS_PORT = "/dev/ttyAMA0"  # Cambia a "/dev/serial0" si es necesario
BAUD_RATE = 9600
OUTPUT_FILE = "gps_data.csv"

def leer_gps():
    contador = 0  # Contador de datos almacenados

    try:
        # Abre la conexi�n con el GPS
        with serial.Serial(GPS_PORT, BAUD_RATE, timeout=0.1) as ser, open(OUTPUT_FILE, mode="a", newline="") as file:
            ser.flushInput()  # Limpiar el buffer del GPS

            writer = csv.writer(file)
            writer.writerow(["Latitud", "Longitud", "Altura (m)"])

            while True:
                linea = ser.readline().decode(errors="ignore").strip()
                
                # Filtrar solo l�neas con $GNGGA o $GPGGA
                if linea.startswith("$GNGGA") or linea.startswith("$GPGGA"):
                    try:
                        mensaje = pynmea2.parse(linea)

                        if mensaje.latitude and mensaje.longitude:  # Verifica si hay datos v�lidos
                            hora = mensaje.timestamp
                            latitud = mensaje.latitude
                            longitud = mensaje.longitude
                            altura = mensaje.altitude

                            # Mostrar siempre la hora
                            print(f"Hora: {hora}", end="")

                            if contador < 10:
                                print(f", Latitud: {latitud}, Longitud: {longitud}, Altura: {altura}m")
                                # Guardar en archivo CSV solo los primeros 10 datos
                                writer.writerow([latitud, longitud, altura])
                                file.flush()
                                contador += 1
                            else:
                                print()  # Solo muestra la hora sin otros datos

                    except pynmea2.ParseError:
                        pass  # Ignorar errores de parseo

    except serial.SerialException as e: 
        print(f"Error al conectar con el GPS: {e}")

if __name__ == "__main__":
    leer_gps()
