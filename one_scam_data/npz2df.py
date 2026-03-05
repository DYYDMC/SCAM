# in case your pipeline takes df as input, run this first to turn .npz a dataframe
import numpy as np, pandas as pd
z = np.load("scan_data.npz")

df = pd.DataFrame({
    "dark_corr": z["dark_corr"],
    "int_t": z["int_t"],
    "motor_pan": z["motor_pan"],
    "motor_tilt": z["motor_tilt"],
    "unix_ts": z["unix_ts"],
    "year": z["year"],
    "month": z["month"],
    "day": z["day"],
    "hour": z["hour"],
    "minute": z["minute"],
    "second": z["second"],
})
