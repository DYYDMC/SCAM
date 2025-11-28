print("first line in main.py...")
import sys
import board
from driver.servo import Servo
from machine import Pin
import time
import random

# Initialize with unique motor IDs
stepperPAN = Servo(board.STEP_PAN, board.DIR_PAN, 
                   board.STEPS_PER_DEG_PAN, motor_id="PAN")
stepperTILT = Servo(board.STEP_TILT, board.DIR_TILT, 
                    board.STEPS_PER_DEG_TILT, motor_id="TILT")


# Print current positions from persistent storage
print(f"PAN current position: {stepperPAN.get_current_position()}°")
print(f"TILT current position: {stepperTILT.get_current_position()}°")

print("Ready for commands...")

while True:
    command = sys.stdin.readline().strip()
    command = command.upper()
    if command.startswith("MOVE:"):
        try:
            parts = command.split(":")[1].split(",")
            target_PAN_degree = int(parts[0])*-1
            target_TILT_degree = int(parts[1])
            
            stepperPAN.move_to_degree(target_PAN_degree, delay_us=1000)
            time.sleep(1)
            stepperTILT.move_to_degree(target_TILT_degree, delay_us=1000)
            time.sleep(1)
            
            # Structured response
            print(f"SUCCESS:MOVE|PAN:{stepperPAN.get_current_position()}|TILT:{stepperTILT.get_current_position()}")
            
        except Exception as e:
            print(f"ERROR:MOVE|{str(e)}")
    
    elif command == "POSITION":
        print(f"SUCCESS:POSITION|PAN:{stepperPAN.get_current_position()}|TILT:{stepperTILT.get_current_position()}")
    
    elif command == "HOME":
        stepperPAN.home_motor(home_position=0)
        stepperTILT.home_motor(home_position=0)
        print("SUCCESS:HOME|Both motors returned to zero")
    
    else:
        print("ERROR:UNKNOWN_COMMAND|Use: MOVE:x,y, POSITION, HOME")
