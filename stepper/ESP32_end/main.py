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
    if command.startswith("MOVE:"):
        try:
            parts = command.split(":")[1].split(",")
            target_PAN_degree = int(parts[0])*-1 # intuitive left:neg, right:positive
            target_TILT_degree = int(parts[1])
            
            stepperPAN.move_to_degree(target_PAN_degree, delay_us=1000)
            time.sleep(1)
            stepperTILT.move_to_degree(target_TILT_degree, delay_us=1000)
            time.sleep(1)
            print(f'MOVED! New position Pan: {stepperPAN.get_current_position()}°,Tilt {stepperTILT.get_current_position()}°')
        except Exception as e:
            print("❌ Invalid command:", str(e))
    
    elif command == "POSITION":
        print(f'The CURRENT position:Pan: {stepperPAN.get_current_position()}°,Tilt {stepperTILT.get_current_position()}°')
    
    else:
        # any other situation, going home
        stepperPAN.home_motor(home_position=0)
        stepperTILT.home_motor(home_position=0)
        print("RECEIVED command other than MOVE or POSITION: ", command)
        print("BRING MOTORS HOME")
