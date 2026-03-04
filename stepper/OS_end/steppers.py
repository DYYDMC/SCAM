import serial
import serial.tools.list_ports
import time
import sys
import re

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
            if sys.platform.startswith("darwin"):
                # mac
                if "usbserial" in port.device or "ACM" in port.device:
                    if self.usb_hint is None or self.usb_hint in (port.description or ""):
                        candidates.append(port.device)
            elif sys.platform.startswith("linux"):
                # linux
                if "USB" in port.device or "ACM" in port.device:
                    if self.usb_hint is None or self.usb_hint in (port.description or ""):
                        candidates.append(port.device)
            else:
                # windows
                if "COM" in port.device:
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
    @staticmethod
    def _parse_position_response(response):
        # Expected format example: "...|PAN:12|TILT:-3"
        m = re.search(r"\|PAN:([+-]?\d+)\|TILT:([+-]?\d+)", response)
        if not m:
            raise ValueError(f"Malformed position response: {response!r}")
        pan = int(m.group(1)) * -1
        tilt = int(m.group(2)) * -1
        return pan, tilt

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
    def read_pos(self, max_retries=4):
        if not self.is_connected:
            if not self.initialize_connection():
                raise RuntimeError("Cannot move: connection failed.")
        last_err = None
        for _ in range(max_retries):
            command = "POSITION\n"
            print(f"sending {command} over...")
            try:
                # Clear stale serial bytes from previous commands.
                if hasattr(self.ser, "reset_input_buffer"):
                    self.ser.reset_input_buffer()
                self.ser.write(command.encode())
                response = self.ser.readline().decode(errors="ignore").strip()
                print("ESP32-stepper Serial Response:", response)
                if not response:
                    last_err = ValueError("Empty serial response")
                    time.sleep(0.05)
                    continue
                return self._parse_position_response(response)
            except Exception as e:
                last_err = e
                print("Serial read error:", str(e))
                time.sleep(0.05)
        raise RuntimeError(f"Failed to read valid POSITION response after {max_retries} retries: {last_err}")
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
