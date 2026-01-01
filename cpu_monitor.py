import wmi
import time
import csv
import os
import math
from datetime import datetime, timedelta

# Connect to OpenHardwareMonitor WMI
w = wmi.WMI(namespace="root\\OpenHardwareMonitor")

# Output CSV file
FNAME = "cpu_log.csv"

HEADERS = [
    "Timestamp",
    "Core1_Temp_C", "Core1_Load_pct",
    "Core2_Temp_C", "Core2_Load_pct",
    "Package_Temp_C", "Package_Power_W",
    "CPU_Total_Load_pct"
]

# ----------------------------
# Set start time here (24-hr format)
START_TIME = "10:12:00"  # Example → will wait until 13:40:00 today
# ----------------------------

# Parse start time
now = datetime.now()
start_today = datetime.strptime(f"{now.date()} {START_TIME}", "%Y-%m-%d %H:%M:%S")

# If start time already passed today → schedule for tomorrow
if start_today <= now:
    start_today = start_today + timedelta(days=1)

print(f"Waiting until {start_today} to start logging...")
while datetime.now() < start_today:
    time.sleep(1)

print("Start time reached. Logging CPU data... Press Ctrl+C to stop.")

# Create CSV header if file does not exist
if not os.path.exists(FNAME):
    with open(FNAME, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)

def get_sensor_value(sensors, keyword, stype):
    """Find the first matching sensor by keyword (in Name) and SensorType"""
    for s in sensors:
        if s.Value is None:
            continue
        if keyword.lower() in s.Name.lower() and str(s.SensorType).lower() == stype.lower():
            try:
                return round(float(s.Value), 2)
            except (ValueError, TypeError):
                return math.nan
    return math.nan

try:
    with open(FNAME, "a", newline="") as f:
        writer = csv.writer(f)
        while True:
            sensors = w.Sensor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Collect values
            core1_temp  = get_sensor_value(sensors, "core #1", "temperature")
            core1_load  = get_sensor_value(sensors, "core #1", "load")
            core2_temp  = get_sensor_value(sensors, "core #2", "temperature")
            core2_load  = get_sensor_value(sensors, "core #2", "load")
            pkg_temp    = get_sensor_value(sensors, "package", "temperature")
            pkg_power   = get_sensor_value(sensors, "package", "power")
            total_load  = get_sensor_value(sensors, "cpu total", "load")

            # Print to console
            print(f"{timestamp} | "
                  f"C1 Temp={core1_temp}°C Load={core1_load}% | "
                  f"C2 Temp={core2_temp}°C Load={core2_load}% | "
                  f"Pkg Temp={pkg_temp}°C Power={pkg_power}W | "
                  f"CPU Total Load={total_load}%")

            # Write to CSV
            writer.writerow([
                timestamp,
                core1_temp, core1_load,
                core2_temp, core2_load,
                pkg_temp, pkg_power,
                total_load
            ])
            f.flush()
            time.sleep(1)

except KeyboardInterrupt:
    print("\nStopped logging.")
