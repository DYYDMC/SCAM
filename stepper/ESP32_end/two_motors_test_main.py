import board
from driver.servo import Servo
from machine import Pin
import time
import random

# Initialize stepper
stepperPAN = Servo(board.STEP_PAN,board.DIR_PAN)
stepperTILT = Servo(board.STEP_TILT,board.DIR_TILT)


# adjust according to your motor + microstepping
FULL_STEPS_PER_REV = 200        # typical 1.8° stepper, .9° stepper for the test stepper
MICROSTEP          = 1          # 1, 2, 4, 8, 16
STEPS_PER_REV      = FULL_STEPS_PER_REV * MICROSTEP

def step_once(stepper,delay_us):
    stepper.step_pin.value(1)
    time.sleep_us(delay_us // 2)
    stepper.step_pin.value(0)
    time.sleep_us(delay_us // 2)
    
def move_steps(stepper, n_steps, clockwise=True, delay_us=1000):
    stepper.dir_pin.value(1 if clockwise else 0)
    for _ in range(n_steps):
        step_once(stepper,delay_us)

n_rev=1
n_steps = n_rev*FULL_STEPS_PER_REV
move_steps(stepperPAN,n_steps,clockwise=True,delay_us=2000)
time.sleep(1)
move_steps(stepperTILT,n_steps,clockwise=True,delay_us=2000)
time.sleep(1)
#move_steps(200,clockwise=False,delay_us=2000)
#move_steps(200,clockwise=False,delay_us=2000)
