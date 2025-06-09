import socket
import time
import serial
import serial.tools.list_ports

# Default settings
ESP32_IP = "192.168.2.102"
ESP32_PORT = 12345
SERIAL_BAUDRATE = 115200
USE_SERIAL = False  # Will be set dynamically

esp_socket = None
ser = None


def find_esp32_serial_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "USB" in port.device or "ACM" in port.device:
            return port.device
    raise RuntimeError("ESP32 serial port not found.")

SERIAL_PORT = find_esp32_serial_port()
def discover_esp32_handshake(port=8266, timeout=5):
    """Wait for ESP32 to announce itself, reply with GOT_IP, return its IP."""
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(('', port))
    udp.settimeout(timeout)

    print("Listening for ESP32 (handshake)...")
    try:
        data, addr = udp.recvfrom(1024)
        msg = data.decode().strip()
        if msg.startswith("I_AM_ESP32:"):
            esp_ip = msg.split(":")[1]
            print(f"ESP32 found at {esp_ip}")
            udp.sendto(b"GOT_IP", addr)
            udp.close()
            return esp_ip
    except socket.timeout:
        print("❌ ESP32 did not respond via Wi-Fi.")
    udp.close()
    return None

def initialize_connection():
    global USE_SERIAL, esp_socket, ser, ESP32_IP, SERIAL_PORT
    print(SERIAL_PORT)
    ESP32_IP = discover_esp32_handshake() or ESP32_IP

    try:
        print(f"Trying Wi-Fi @ {ESP32_IP}:{ESP32_PORT}...")
        esp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        esp_socket.settimeout(3)
        esp_socket.connect((ESP32_IP, ESP32_PORT))
        print("✅ Connected via Wi-Fi.")
    except Exception as e:
        print("⚠️ Wi-Fi connection failed, trying serial instead...")
        try:
            ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=1)
            USE_SERIAL = True
            print(f"✅ Connected via Serial @ {SERIAL_PORT}")
        except Exception as se:
            print("❌ Serial connection also failed.")
            raise se

def move_to_esp32(pan, tilt):
    """Send move command to ESP32 via available connection."""
    command = f"MOVE:{pan},{tilt}\n"

    if USE_SERIAL:
        ser.write(command.encode())
        try:
            response = ser.readline().decode().strip()
            print("ESP32 Serial Response:", response)
        except Exception as e:
            print("Serial read error:", str(e))
    else:
        try:
            esp_socket.sendall(command.encode())
            response = esp_socket.recv(1024).decode().strip()
            print("ESP32 Wi-Fi Response:", response)
        except Exception as e:
            print("Wi-Fi send/receive error:", str(e))

def close_connection():
    if USE_SERIAL and ser:
        ser.close()
    elif esp_socket:
        esp_socket.close()

