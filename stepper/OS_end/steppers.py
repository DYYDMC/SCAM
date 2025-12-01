import serial
import serial.tools.list_ports
import time

class SerialBase:
    def __init__(self, usb_hint=None):
        self.ser = None
        self.SERIAL_BAUDRATE = 115200
        self.is_connected = False
        self.usb_hint = usb_hint  # optional string to filter ports

    def find_serial_port(self):
        ports = serial.tools.list_ports.comports()
        candidates = []

        for port in ports:
            if "usbserial" in port.device or "ACM" in port.device:
                if self.usb_hint is None or self.usb_hint in (port.description or ""):
                    candidates.append(port.device)

        if not candidates:
            raise RuntimeError("No matching serial port found.")
        return candidates[0]

    def initialize_connection(self):
        if self.is_connected:
            return True
        try:
            serial_port = self.find_serial_port()
            print(f"Connecting via Serial @ {serial_port}")
            self.ser = serial.Serial(serial_port, self.SERIAL_BAUDRATE, timeout=1)
            time.sleep(2)
            self.is_connected = True
            print("Serial connection established.")
            return True
        except Exception as e:
            print(f"Failed to connect: {str(e)}")
            self.is_connected = False
            return False

    def close_connection(self):
        if self.ser:
            self.ser.close()
            self.is_connected = False

    def __del__(self):
        self.close_connection()


class StepperController(SerialBase):
    def move_to(self, target_pan=0,target_tilt=0):
        if not self.is_connected:
            if not self.initialize_connection():
                raise RuntimeError("Cannot move: connection failed.")
        pan,tilt = target_pan,target_tilt
        command = f"MOVE:{pan},{tilt}\n"
        print(f"sending {command} over...")
        self.ser.write(command.encode())

        try:
            response = self.ser.readline().decode().strip()
            print("ESP32-stepper Serial Response:", response)
            return response
        except Exception as e:
            print("Serial read error:", str(e))
            raise
    def read_pos(self,):
        if not self.is_connected:
            if not self.initialize_connection():
                raise RuntimeError("Cannot move: connection failed.")
        command = f"POSITION\n"
        print(f"sending {command} over...")
        self.ser.write(command.encode())

        try:
            response = self.ser.readline().decode().strip()
            print("ESP32-stepper Serial Response:", response)
            return response
        except Exception as e:
            print("Serial read error:", str(e))
            raise
    def home_motor(self,):
        if not self.is_connected:
            if not self.initialize_connection():
                raise RuntimeError("Cannot move: connection failed.")
        command = f"HOME\n"
        print(f"sending {command} over...")
        self.ser.write(command.encode())

        try:
            response = self.ser.readline().decode().strip()
            print("ESP32-stepper Serial Response:", response)
            return response
        except Exception as e:
            print("Serial read error:", str(e))
            raise
    def reset_pos(self,):
        if not self.is_connected:
            if not self.initialize_connection():
                raise RuntimeError("Cannot move: connection failed.")
        command = f"RESET\n"
        print(f"sending {command} over...")
        self.ser.write(command.encode())

        try:
            response = self.ser.readline().decode().strip()
            print("ESP32-stepper Serial Response:", response)
            return response
        except Exception as e:
            print("Serial read error:", str(e))
            raise
