#!/usr/bin/env python3
import argparse
import os
import pickle
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd

from apply_optic_filter import add_interpolated_spectrum


def normalize_target_dir(path: str) -> str:
    path = path.strip()
    if path.startswith("~Github/"):
        path = "~/Github/" + path[len("~Github/") :]
    return os.path.abspath(os.path.expanduser(path))


def ensure_scan_npz(target_dir: str) -> str:
    scan_npz = os.path.join(target_dir, "scan_data.npz")
    if os.path.exists(scan_npz):
        return scan_npz

    converter = os.path.join(os.path.dirname(__file__), "spec_npy2npz.py")
    cmd = [sys.executable, converter, target_dir]
    print(f"[info] scan_data.npz not found, running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    if not os.path.exists(scan_npz):
        raise FileNotFoundError(f"Failed to create {scan_npz}")
    return scan_npz


def build_temp_df(z: np.lib.npyio.NpzFile) -> pd.DataFrame:
    keys = list(z.keys())
    if not keys:
        raise ValueError("NPZ has no keys.")

    lengths = {}
    for k in keys:
        arr = z[k]
        lengths[k] = int(arr.shape[0]) if arr.ndim > 0 else 1
    n_rows = max(lengths.values())

    data: dict[str, Any] = {}
    for k in keys:
        arr = z[k]
        if arr.ndim == 0:
            data[k] = [arr.item()] * n_rows
        elif arr.shape[0] == n_rows and arr.ndim == 1:
            data[k] = arr
        elif arr.shape[0] == n_rows:
            data[k] = list(arr)
        else:
            data[k] = [arr] * n_rows
    return pd.DataFrame(data)


def column_to_np_array(series: pd.Series) -> np.ndarray:
    vals = series.tolist()
    if not vals:
        return np.asarray([], dtype=np.float64)
    first = vals[0]
    if isinstance(first, np.ndarray):
        return np.stack(vals)
    return np.asarray(vals)


def load_pr_kernels() -> dict[str, np.ndarray]:
    pkl_path = os.path.expanduser("~/Github/SCAM/config/mouse_PR_sensitivity_KF.pkl")
    with open(pkl_path, "rb") as f:
        d = pickle.load(f)

    w = np.asarray(d["wavelength"])
    s = np.asarray(d["Scone"])
    m = np.asarray(d["Mcone"])
    r = np.asarray(d["rod"])

    mask = (w >= 300) & (w <= 599)
    return {
        "wavelength": w[mask],
        "scone": s[mask],
        "mcone": m[mask],
        "rod": r[mask],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Ensure scan_data.npz exists, apply optic filter, "
            "and save scan_data_optic_filtered.npz."
        )
    )
    parser.add_argument("target_dir", help="Path like ~/Github/SCAM/one_scam_data/ONE_SCAM_XXXXXX/")
    args = parser.parse_args()

    target_dir = normalize_target_dir(args.target_dir)
    if not os.path.isdir(target_dir):
        raise NotADirectoryError(f"Target directory does not exist: {target_dir}")

    scan_npz = ensure_scan_npz(target_dir)
    z = np.load(scan_npz, allow_pickle=True)

    df = build_temp_df(z)
    df["adjusted_corrected_spectrum"] = df["spectrum"]
    filtered_df = add_interpolated_spectrum(df)
    kernels = load_pr_kernels()

    if len(kernels["wavelength"]) != len(filtered_df.iloc[0]["filtered_spectrum"]):
        raise ValueError("Kernel wavelength length does not match filtered_spectrum length.")

    filt_stack = np.stack(filtered_df["filtered_spectrum"].to_list())
    x = kernels["wavelength"]
    filtered_df["auc_scone"] = np.trapezoid(filt_stack * kernels["scone"], x=x, axis=1)
    filtered_df["auc_mcone"] = np.trapezoid(filt_stack * kernels["mcone"], x=x, axis=1)
    filtered_df["auc_rod"] = np.trapezoid(filt_stack * kernels["rod"], x=x, axis=1)

    out_npz = os.path.join(target_dir, "scan_data_optic_filtered.npz")
    out_data = {col: column_to_np_array(filtered_df[col]) for col in filtered_df.columns}
    np.savez_compressed(out_npz, **out_data)

    print(f"[ok] saved: {out_npz}")
    print(
        "[ok] shapes:",
        f"spectrum={column_to_np_array(filtered_df['spectrum']).shape},",
        f"filtered_spectrum={column_to_np_array(filtered_df['filtered_spectrum']).shape},",
        f"auc_scone={column_to_np_array(filtered_df['auc_scone']).shape}",
    )


if __name__ == "__main__":
    main()
