import serial
import serial.tools.list_ports
import time
import sys

# Settings
SERIAL_BAUDRATE = 115200

# Global serial object
ser = None

def find_esp32_serial_port():
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        if sys.platform =='darwin':
            if "usbmodem" in port.device or "usbserial" in port.device:
                return port.device
        else:
            # un-mac
            if "USB" in port.device or "ACM" in port.device:
                return port.device
    raise RuntimeError("ESP32 serial port not found.")

def initialize_connection():
    global ser
    serial_port = find_esp32_serial_port()
    print(f"Connecting to ESP32 via Serial @ {serial_port}")
    ser = serial.Serial(serial_port, SERIAL_BAUDRATE, timeout=1)
    time.sleep(2)  # allow time for connection setup
    print("✅ Serial connection established.")

def move_to_esp32(pan, tilt):
    """Send move command to ESP32 via serial."""
    if ser is None:
        raise RuntimeError("Serial connection not initialized.")
    command = f"MOVE:{pan},{tilt}\n"
    ser.write(command.encode())
    try:
        response = ser.readline().decode().strip()
        print("ESP32 Serial Response:", response)
    except Exception as e:
        print("Serial read error:", str(e))

def close_connection():
    if ser:
        ser.close()

