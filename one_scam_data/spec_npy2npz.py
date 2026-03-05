import glob
import os
import sys
from datetime import datetime

import numpy as np


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python spec_npy2npz.py <target_dir>")
        sys.exit(1)

    target_dir = str(sys.argv[1])
    scan_dir = os.path.join(target_dir, "scan_data")
    print(target_dir)
    print(f"turn all the npy files under {scan_dir} to a .npz")

    all_npys = sorted(glob.glob(os.path.join(scan_dir, "*.npy")))
    if not all_npys:
        print(f"No .npy files found under: {scan_dir}")
        sys.exit(1)

    wavelength_list = []
    spectrum_list = []
    dark_corr = []
    int_t = []
    motor_pan = []
    motor_tilt = []
    unix_ts = []
    year = []
    month = []
    day = []
    hour = []
    minute = []
    second = []

    for npy_file in all_npys:
        scan_dict = np.load(npy_file, allow_pickle=True).item()
        dt = datetime.strptime(scan_dict["ts"], "%Y%m%d_%H%M%S")

        # Keep spectral data at float64 as requested.
        wavelength_list.append(np.asarray(scan_dict["wavelengths"], dtype=np.float64))
        spectrum_list.append(np.asarray(scan_dict["intensity"], dtype=np.float64))

        dark_corr.append(scan_dict["metadata"]["dark_correction_applied"])
        int_t.append(scan_dict["metadata"]["integration_time_ms"])
        motor_pan.append(scan_dict["motor_pan"])
        motor_tilt.append(scan_dict["motor_tilt"])

        unix_ts.append(int(dt.timestamp()))
        year.append(dt.year)
        month.append(dt.month)
        day.append(dt.day)
        hour.append(dt.hour)
        minute.append(dt.minute)
        second.append(dt.second)

    wavelength = np.stack(wavelength_list)
    spectrum = np.stack(spectrum_list)

    out_npz = os.path.join(target_dir, "scan_data.npz")
    np.savez_compressed(
        out_npz,
        wavelength=wavelength,
        spectrum=spectrum,
        dark_corr=np.asarray(dark_corr, dtype=np.bool_),
        int_t=np.asarray(int_t, dtype=np.uint32),
        motor_pan=np.asarray(motor_pan, dtype=np.int16),
        motor_tilt=np.asarray(motor_tilt, dtype=np.int16),
        unix_ts=np.asarray(unix_ts, dtype=np.int64),
        year=np.asarray(year, dtype=np.uint16),
        month=np.asarray(month, dtype=np.uint8),
        day=np.asarray(day, dtype=np.uint8),
        hour=np.asarray(hour, dtype=np.uint8),
        minute=np.asarray(minute, dtype=np.uint8),
        second=np.asarray(second, dtype=np.uint8),
    )

    print(f"saved: {out_npz}")
    print(f"rows: {spectrum.shape[0]}, channels: {spectrum.shape[1]}")


if __name__ == "__main__":
    main()
