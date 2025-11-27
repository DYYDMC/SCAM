print("first line in main.py...")
from machine import Pin
import time
import sys

# ---- pin selection ----
STEP_PIN   = 32
DIR_PIN    = 33
# ---- GPIO setup ----

step_pin = Pin(STEP_PIN, Pin.OUT)
dir_pin  = Pin(DIR_PIN,  Pin.OUT)

# adjust according to your motor + microstepping
FULL_STEPS_PER_REV = 400        # typical 1.8° stepper
MICROSTEP          = 1          # 1, 2, 4, 8, 16
STEPS_PER_REV      = FULL_STEPS_PER_REV * MICROSTEP

def step_once(delay_us):
    step_pin.value(1)
    time.sleep_us(delay_us // 2)
    step_pin.value(0)
    time.sleep_us(delay_us // 2)
    
    
def move_steps(n_steps, clockwise=True, delay_us=1000):
    dir_pin.value(1 if clockwise else 0)
    for _ in range(n_steps):
        step_once(delay_us)
        
def move_degrees(angle_deg, clockwise=True, delay_us=1000):
    steps = int(STEPS_PER_REV * angle_deg / 360.0)
    move_steps(steps, clockwise, delay_us)

while True:
    command = sys.stdin.readline().strip()
    #print("📩 Received:", command)  # ✅ Debug log
    if command.startswith("MOVE:"):
        try:
            parts = command.split(":")[1].split(",")
            n_rev=int(parts[0])
            clockwise=True if int(parts[1])==1 else False
            n_step = n_rev*STEPS_PER_REV
            move_steps(n_step,clockwise=False,delay_us=2000)
            print('REVOLVED!')
        except Exception as e:
            print("❌ Invalid command:", str(e))
