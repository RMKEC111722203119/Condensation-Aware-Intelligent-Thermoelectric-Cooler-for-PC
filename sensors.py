import serial
import csv
from datetime import datetime
import time
import math

# --- CONFIG ---
PORT = "COM3"       # Change to your Arduino port
BAUDRATE = 115200   # Must match Serial.begin()
CSV_FILE = "sensor_log.csv"
INTERVAL = 1        # 🔹 log every 1 second

# --- Dew Point Formula (Arden Buck) ---
def calculate_dew_point(temp_c, humidity):
    if temp_c is None or humidity is None:
        return None
    try:
        a = 6.1121
        b = 18.678
        c = 257.14
        d = 234.5
        gamma = math.log(humidity / 100.0) + (b * temp_c) / (c + temp_c)
        dew_point = (c * gamma) / (b - gamma)
        return round(dew_point, 2)
    except Exception:
        return None

# --- Safe/Unsafe Check (using DHT11 temp) ---
def check_safety(dht_temp, dew_point):
    if dht_temp is None or dew_point is None:
        return "UNKNOWN"
    return "UNSAFE" if dht_temp <= dew_point+2 else "SAFE"

# --- Serial Setup ---
ser = serial.Serial(PORT, BAUDRATE, timeout=1)
print(f"✅ Connected to {PORT}")
print("⏳ Waiting for valid sensor data...")

with open(CSV_FILE, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "Timestamp", 
        "DHT11_Temp (°C)", 
        "Humidity (%)", 
        "DS18B20_Temp (°C)", 
        "DewPoint (°C)", 
        "Status"
    ])

    try:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            parts = line.split(",")
            if len(parts) != 3:
                continue  # skip junk lines

            try:
                dht_temp = None if parts[0] == "-999" else float(parts[0])
                humidity = None if parts[1] == "-999" else float(parts[1])
                ds_temp = None if parts[2] == "-999" else float(parts[2])
            except ValueError:
                continue  # skip invalid numbers

            dew_point = calculate_dew_point(dht_temp, humidity)
            status = check_safety(dht_temp, dew_point)

            # Skip if everything is invalid
            if dht_temp is None and humidity is None and ds_temp is None:
                continue

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [
                timestamp,
                dht_temp if dht_temp is not None else "NULL",
                humidity if humidity is not None else "NULL",
                ds_temp if ds_temp is not None else "NULL",
                dew_point if dew_point is not None else "NULL",
                status
            ]

            writer.writerow(row)
            print("📌", row)

            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\n⏹ Logging stopped. Data saved to", CSV_FILE)

ser.close()
