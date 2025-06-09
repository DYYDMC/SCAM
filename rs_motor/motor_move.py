from ESP32_utils import initialize_connection, move_to_esp32, close_connection
import time
### === INIT === ###
initialize_connection()
v_max = 36
v_min = -54
move_to_esp32(0, 0)
time.sleep(2)
move_to_esp32(0,v_max)
time.sleep(2)
move_to_esp32(0,v_min)