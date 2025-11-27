# servo.py

# ----------------------------------------------------------------------------
# servo.py
# Simplified stepper motor interface class(es)
#
# The MIT License (MIT)
# Copyright (c) 2025 Yuyao Deng, adapted the format from Thomas Euler
# 2025-11-27, v1
# ----------------------------------------------------------------------------
from machine import Pin
# ----------------------------------------------------------------------------
class Servo():
  """Interface class for stepper motors."""

  def __init__(self, step_pin,dir_pin):
    """ Initialises the pin that connects to the stepper motor, with step_pin
        and dir_pin as numbe.
    """
    self.step_pin = Pin(step_pin, Pin.OUT)
    self.dir_pin = Pin(dir_pin,Pin.OUT)
    super().__init__()
    print("stepper STEP_PIN at pin {0}, DIR_PIN at pin({1}), readd.".format(step_pin,dir_pin))

# ----------------------------------------------------------------------------