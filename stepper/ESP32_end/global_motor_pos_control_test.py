# global_pos_control_motor.py (updated)
import board
from driver.servo import Servo
import time

# Initialize with unique motor IDs
stepperPAN = Servo(board.STEP_PAN, board.DIR_PAN, 
                   board.STEPS_PER_DEG_PAN, motor_id="PAN")
stepperTILT = Servo(board.STEP_TILT, board.DIR_TILT, 
                    board.STEPS_PER_DEG_TILT, motor_id="TILT")

# Move to absolute position - position will be remembered after restart
#stepperPAN.move_to_degree(0, delay_us=1000)
stepperTILT.move_to_degree(0, delay_us=1000)
time.sleep(1)
stepperTILT.move_to_degree(10, delay_us=1000)
time.sleep(1)

# After restart, you can check current position:
print(f"PAN position: {stepperPAN.get_current_position()}°")
print(f"TILT position: {stepperTILT.get_current_position()}°")

print("Performing software homing...")
stepperPAN.home_motor(home_position=0)
stepperTILT.home_motor(home_position=0) 