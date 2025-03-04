import serial
import smbus2
import time
import math

#GPIO
#vcc (5V) - pin 2  (5v)
#gnd      - pin 6  (GND)
#tx       - pin 10 (GPIO 15)
#rx       - pin 8  (GPIO 14)
#sda comp - pin 3  (GPIO 2, SDA1)
#scl comp - pin 5  (GPIO 3, SCL1)

#Configuracion del puerto UART
gps_port = "/dev/ttyAMA2" # o "/dev/ttyS0"
baud_rate = 9600
ser = serial.Serial(gps_port, baud_rate, timeout=1)

#configuracion del compass I2C (HMC5883L)
I2C_ADDRESS = 0x1E #Direccion del dispositivo en I2C
bus = smbus2.SMBus(1)

#Inicializacion del sensor HMC5883L
def init_compass():
    bus.write_byte_data(I2C_ADDRESS, 0x02, 0x00) #Modo continuo

#Leer datos del Compass
def read_compass():
    data = bus.read_i2c_block_data(I2C_ADDRESS, 0x03, 6) #Leer 6 bytes de datos
    x = (data[0] << 8) | data[1]
    z = (data[2] << 8) | data[3]
    y = (data[4] << 8) | data[5]
     
    # Convertir valores negativos
    x = x - 65536 if x > 32767 else x
    y = y - 65536 if y > 32767 else y

    # Calcular el angulo en grados
    heading = math.atan2(y, x) * (180 / math.pi)
    if heading < 0:
        heading += 360
    return heading

#Extraer datos de GPS desde GPGGA
def parse_gpgga(setence):
    data = setence.split(",")
    if setence.startswith("$GPGGA"):
        utc_time = data[1]
        lat_raw = data[2]
        lat_dir = data[3]
        lon_raw = data[4]
        lon_dir = data[5]
        fix_quality = data[6]
        num_satellites = data[7]

        #Convertir coordenadas a formato decimal
        lat = float(lat_raw[:2]) + float(lat_raw[2:]) / 60 if lat_raw else 0.0
        lon = float(lon_raw[:3]) + float(lon_raw[3:]) / 60 if lon_raw else 0.0

        if lat_dir == "S":
            lat = -lat
        if lon_dir == "W":
            lon = -lon

        #Convertir UTC a formato HH:MM:SS
        utc_hh = utc_time[:2] if len(utc_time) >= 2 else "00"
        utc_mm = utc_time[2:4] if len(utc_time) >= 4 else "00"
        utc_ss = utc_time[4:6] if len(utc_time) >= 6 else "00"
        utc_formatted = f"{utc_hh}:{utc_mm}:{utc_ss} UTC"

        return lat, lon,utc_formatted, fix_quality, num_satellites
    return None

#Inicializar la brujula
init_compass()

#Leer y mostrar datos GPS y Compass
try:
    while True:
        #Leer brujula
        heading = read_compass()
        #Leer GPS
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        gps_data = parse_gpgga(line)

        if gps_data:
            lat, lon, utc_time, fix_quality, num_satellites = gps_data
            print(f"latitud: {lat}, longitud: {lon}")
            print(f"hora UTC: {utc_time}")
            print(f"satelites: {num_satellites}, calidad de señal: {fix_quality}")
            print(f"rumbo: {heading:.2f}grados")
            print("-" * 40)
        time.sleep(1)
except KeyboardInterrupt:
    print("\nSaliendo...")
    ser.close()