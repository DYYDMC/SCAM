import serial
import serial.tools.list_ports
import time

class MotorController:
    def __init__(self):
        self.ser = None
        self.SERIAL_BAUDRATE = 115200
        self.is_connected = False
    
    def find_esp32_serial_port(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "USB" in port.device or "ACM" in port.device:
                return port.device
        raise RuntimeError("ESP32 serial port not found.")
    
    def initialize_connection(self):
        """Initialize connection to ESP32"""
        if self.is_connected:
            return True
            
        try:
            serial_port = self.find_esp32_serial_port()
            print(f"Connecting to ESP32 via Serial @ {serial_port}")
            self.ser = serial.Serial(serial_port, self.SERIAL_BAUDRATE, timeout=1)
            time.sleep(2)  # allow time for connection setup
            self.is_connected = True
            print("Serial connection established.")
            return True
        except Exception as e:
            print(f"Failed to connect to ESP32: {str(e)}")
            self.is_connected = False
            return False
    
    def move_to(self, pan, tilt):
        """Send move command to ESP32 via serial."""
        if not self.is_connected:
            if not self.initialize_connection():
                raise RuntimeError("Cannot move: ESP32 connection failed.")
        
        command = f"MOVE:{pan},{tilt}\n"
        self.ser.write(command.encode())
        try:
            response = self.ser.readline().decode().strip()
            print("ESP32 Serial Response:", response)
            return response
        except Exception as e:
            print("Serial read error:", str(e))
            raise
    
    def close_connection(self):
        if self.ser:
            self.ser.close()
            self.is_connected = False
    
    def __del__(self):
        self.close_connection()