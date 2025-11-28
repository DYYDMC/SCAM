# ----------------------------------------------------------------------------
# board.py
# Pin definitions
#
# The MIT License (MIT)
# Copyright (c) 2025 Yuyao Deng, adapted the format from Thomas Euler
# 2025-11-27, v1
# ----------------------------------------------------------------------------
from micropython import const

# SteppersS
STEP_TILT   = 32
DIR_TILT    = 33
STEPS_PER_DEG_TILT = 262

#PAN
STEP_PAN   = 25
DIR_PAN    = 26
STEPS_PER_DEG_PAN = 80

# TO-DO
#PAN_RANGE_DEG  = [-45, 45]
#TLT_RANGE_DEG  = [-45, 45]
