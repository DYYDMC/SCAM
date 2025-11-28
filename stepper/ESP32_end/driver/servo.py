# servo.py

# ----------------------------------------------------------------------------
# servo.py
# Simplified stepper motor interface class(es)
#
# The MIT License (MIT)
# Copyright (c) 2025 Yuyao Deng, adapted the format from Thomas Euler
# 2025-11-27, v1
# 2025-11-28, v2, add .json files to remeber the absolte position, add home_motor() bring motro to (0,0) in the end
# servo.py (updated)
from machine import Pin
import json
import os
import time

class Servo():
    def __init__(self, step_pin, dir_pin, steps_per_degree, motor_id="default"):
        self.step_pin = Pin(step_pin, Pin.OUT)
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.steps_per_degree = steps_per_degree
        self.motor_id = motor_id
        self.target_pos_degrees = list(range(-30, 31)) # limited by angle of CAM's lens
        
        # Load saved position or initialize to 0
        self.pos_degree = self._load_position()
        # only deubg msg
        # print(f"Stepper {motor_id} at pins STEP:{step_pin}, DIR:{dir_pin}, current position: {self.pos_degree}°")

    def _get_storage_filename(self):
        return f"./jsn/motor_{self.motor_id}_pos.json"

    def _load_position(self):
        """Load saved position from persistent storage"""
        try:
            filename = self._get_storage_filename()
            with open(filename, 'r') as f:
                data = json.load(f)
                return data.get('position', 0)
        except:
            # REMOVED: print(f"Error saving position: {e}")
            pass  # Or log to a file if needed

    def _save_position(self):
        """Save current position to persistent storage"""
        try:
            filename = self._get_storage_filename()
            with open(filename, 'w') as f:
                json.dump({'position': self.pos_degree}, f)
        except: # REMOVED: print(f"Error saving position: {e}")
            pass  # Or log to a file if needed
    def set_pos_degree(self, pos_degree):
        """Set position and save to persistent storage"""
        self.pos_degree = pos_degree
        self._save_position()

    def move_to_degree(self, target_degree, steps_per_rev=400, delay_us=1000):
        """Move to absolute position and update stored position"""
        if not self.if_target_valid(target_degree):
            # print(f"Target {target_degree}° out of range")
            return False
        
        delta_degree = target_degree - self.pos_degree
        n_steps = int(delta_degree * self.steps_per_degree)
        
        # Set direction
        self.dir_pin.value(1 if n_steps > 0 else 0)
        n_steps_abs = abs(n_steps)
        
        # Move step by step
        for _ in range(n_steps_abs):
            self.step_pin.value(1)
            time.sleep_us(delay_us // 2)
            self.step_pin.value(0)
            time.sleep_us(delay_us // 2)
        
        # Update and save position
        self.set_pos_degree(target_degree)
        # print(f"Moved to {target_degree}°")
        return True

    def if_target_valid(self, tmp_target):
        return tmp_target in self.target_pos_degrees

    def get_current_position(self):
        """Get current position from persistent storage"""
        return self._load_position()
    def home_motor(self, home_switch_pin=None, home_position=0, max_steps=1000):
        self.move_to_degree(home_position)
        self.set_pos_degree(home_position)
        #print(f"Software homing completed for {self.motor_id} - position set to {home_position}°")
        return True

# ----------------------------------------------------------------------------