#!/usr/bin/env python3
import os
import re
import json
import time
import serial
import sqlite3
from datetime import datetime
from grow.moisture import Moisture

# ====== CONFIG ======
DB_PATH = "/home/jasonvega/Desktop/project/plants.db"
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
SERVICE_NAME = "grow-monitor.service"
SYSLOG_PATH = "/var/log/syslog"
# ====================

# --- Moisture Sensor Setup ---
m1 = Moisture(1)
m2 = Moisture(2)
m3 = Moisture(3)

dry_points = [27, 27, 27]
wet_points = [3, 3, 3]


# ==========================
# Database Functions
# ==========================

def setup_database():
    """Create the sensors and pump_log tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sensors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            temp REAL,
            light REAL,
            moisture_1 REAL,
            moisture_2 REAL,
            moisture_3 REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS pump_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            channel INTEGER,
            rate REAL,
            duration REAL
        )
    """)
    conn.commit()
    conn.close()


def log_to_db(timestamp, temp, light, m1_val, m2_val, m3_val):
    """Insert sensor data into the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO sensors (timestamp, temp, light, moisture_1, moisture_2, moisture_3)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, temp, light, m1_val, m2_val, m3_val))
    conn.commit()
    conn.close()
    print(f"✅ Saved to database: Temp={temp}, UV={light}, M1={m1_val}%, M2={m2_val}%, M3={m3_val}%")


# ==========================
# Pump log parser (user-supplied)
# ==========================

import re
import sqlite3

SYSLOG_PATH = "/var/log/syslog"
DB_PATH = "/home/jasonvega/Desktop/project/plants.db"

import re
import sqlite3
from datetime import datetime

SYSLOG_PATHS = [
    "/var/log/syslog",
    "/var/log/syslog.1"
]

DB_PATH = "/home/jasonvega/Desktop/project/plants.db"

def log_pump_events():
    """Parse Grow HAT watering events from current and previous syslog, store only new events with real timestamps."""
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Make sure table exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS pump_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            channel INTEGER,
            rate REAL,
            duration REAL,
            UNIQUE(timestamp, channel, rate, duration)
        )
    """)

    # Pattern matches: 2025-11-04 12:00:57,269 INFO: Watering Channel: 1 - rate 0.60 for 1.00sec
    pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ .*Watering Channel: (\d+) - rate ([\d.]+) for ([\d.]+)sec"
    )

    events = []

    for path in SYSLOG_PATHS:
        try:
            with open(path, "r") as f:
                for line in f:
                    match = pattern.search(line)
                    if match:
                        timestamp = match.group(1)
                        channel = int(match.group(2))
                        rate = float(match.group(3))
                        duration = float(match.group(4))
                        events.append((timestamp, channel, rate, duration))
        except FileNotFoundError:
            continue

    # Sort events by real timestamps (oldest → newest)
    events.sort(key=lambda x: x[0])

    # Insert only new events
    inserted = 0
    for event in events:
        try:
            c.execute(
                "INSERT OR IGNORE INTO pump_log (timestamp, channel, rate, duration) VALUES (?, ?, ?, ?)",
                event
            )
            if c.rowcount > 0:
                inserted += 1
        except:
            pass

    conn.commit()
    conn.close()

    if inserted > 0:
        print(f"✅ Logged {inserted} new pump event(s).")
    else:
        print("ℹ️ No new pump events found.")

# ==========================
# Moisture Sensor Functions
# ==========================

def moisture_percentage(reading, dry, wet):
    """Convert raw moisture reading to a 0–100% scale."""
    if dry <= wet:
        return 0
    pct = (dry - reading) / (dry - wet) * 100
    return max(0, min(100, pct))


def safe_read(sensor):
    """Safely read from a single sensor property."""
    try:
        return sensor.moisture
    except Exception as e:
        print(f"⚠️ Error reading sensor: {e}")
        return None


def read_moisture():
    """Read all moisture sensors and return their percentages."""
    try:
        # double-read to stabilize sensor output
        _ = [safe_read(m) for m in (m1, m2, m3)]
        time.sleep(2.0)
        readings = [safe_read(m) for m in (m1, m2, m3)]

        if any(r is None for r in readings):
            raise ValueError("One or more moisture readings failed")

        pct = [
            moisture_percentage(readings[i], dry_points[i], wet_points[i])
            for i in range(3)
        ]

        print(f"💧 Moisture: 1={pct[0]:.1f}%  2={pct[1]:.1f}%  3={pct[2]:.1f}%")
        return pct
    except Exception as e:
        print(f"⚠️ Error reading moisture sensors: {e}")
        return (None, None, None)


# ==========================
# Arduino Functions
# ==========================

def read_arduino_data():
    """Read UV and temperature data from Arduino."""
    temp = None
    uv = None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=10)
        sensors_needed = {"UV", "AmbientTemp"}
        sensors_seen = set()

        for _ in range(15):
            line = ser.readline().decode("utf-8").strip()
            if not line:
                continue
            if line.startswith("~{"):
                try:
                    data = json.loads(line.strip("~|"))
                    name = data.get("sensorName")
                    value = data.get("value")

                    if name == "AmbientTemp":
                        temp = float(value)
                        sensors_seen.add("AmbientTemp")
                    elif name == "UV":
                        uv = float(value)
                        sensors_seen.add("UV")

                    if sensors_seen == sensors_needed:
                        break
                except Exception as e:
                    print("⚠️ Parse error:", line, e)
        ser.close()
    except Exception as e:
        print(f"⚠️ Error reading Arduino data: {e}")

    print(f"🌡️ Temp={temp}°C | UV={uv}")
    return temp, uv


# ==========================
# Main Function
# ==========================

def main():
    setup_database()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Read sensors
    temp, uv = read_arduino_data()
    m1_pct, m2_pct, m3_pct = read_moisture()

    # Log readings
    if all(v is not None for v in [m1_pct, m2_pct, m3_pct]):
        log_to_db(timestamp, temp, uv, m1_pct, m2_pct, m3_pct)
    else:
        print("⚠️ Skipping database log due to invalid moisture data.")

    # Log pump activity (parses the last ~200 lines of syslog)
    try:
        log_pump_events()
    except Exception as e:
        print(f"⚠️ Error logging pump events: {e}")


# ==========================
# Safe Service Control Wrapper
# ==========================

if __name__ == "__main__":
    print(f"⏸️  Stopping {SERVICE_NAME} ...")
    os.system(f"sudo systemctl stop {SERVICE_NAME}")

    try:
        main()
    except Exception as e:
        print("⚠️ Script error:", e)
    finally:
        print(f"▶️  Restarting {SERVICE_NAME} ...")
        os.system(f"sudo systemctl start {SERVICE_NAME}")
        print("✅ Grow monitor service restarted.")
