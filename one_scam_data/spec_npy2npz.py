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

    rows = []

    for npy_file in all_npys:
        scan_dict = np.load(npy_file, allow_pickle=True).item()
        dt = datetime.strptime(scan_dict["ts"], "%Y%m%d_%H%M%S")

        rows.append(
            {
                "wavelength": np.asarray(scan_dict["wavelengths"], dtype=np.float64),
                "spectrum": np.asarray(scan_dict["intensity"], dtype=np.float64),
                "dark_corr": scan_dict["metadata"]["dark_correction_applied"],
                "int_t": scan_dict["metadata"]["integration_time_ms"],
                "motor_pan": scan_dict["motor_pan"],
                "motor_tilt": scan_dict["motor_tilt"],
                "unix_ts": int(dt.timestamp()),
                "year": dt.year,
                "month": dt.month,
                "day": dt.day,
                "hour": dt.hour,
                "minute": dt.minute,
                "second": dt.second,
            }
        )

    rows.sort(key=lambda r: r["unix_ts"])

    wavelength = np.stack([r["wavelength"] for r in rows])
    spectrum = np.stack([r["spectrum"] for r in rows])
    dark_corr = np.asarray([r["dark_corr"] for r in rows], dtype=np.bool_)
    int_t = np.asarray([r["int_t"] for r in rows], dtype=np.uint32)
    motor_pan = np.asarray([r["motor_pan"] for r in rows], dtype=np.int16)
    motor_tilt = np.asarray([r["motor_tilt"] for r in rows], dtype=np.int16)
    unix_ts = np.asarray([r["unix_ts"] for r in rows], dtype=np.int64)
    year = np.asarray([r["year"] for r in rows], dtype=np.uint16)
    month = np.asarray([r["month"] for r in rows], dtype=np.uint8)
    day = np.asarray([r["day"] for r in rows], dtype=np.uint8)
    hour = np.asarray([r["hour"] for r in rows], dtype=np.uint8)
    minute = np.asarray([r["minute"] for r in rows], dtype=np.uint8)
    second = np.asarray([r["second"] for r in rows], dtype=np.uint8)

    out_npz = os.path.join(target_dir, "scan_data.npz")
    np.savez_compressed(
        out_npz,
        wavelength=wavelength,
        spectrum=spectrum,
        dark_corr=dark_corr,
        int_t=int_t,
        motor_pan=motor_pan,
        motor_tilt=motor_tilt,
        unix_ts=unix_ts,
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
    )

    print(f"saved: {out_npz}")
    print(f"rows: {spectrum.shape[0]}, channels: {spectrum.shape[1]}")


if __name__ == "__main__":
    main()
