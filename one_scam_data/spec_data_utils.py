#!/usr/bin/env python3
import os
import pickle
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


SCAM_PATH = os.path.join(os.path.expanduser("~"), "Github", "SCAM")
EYE_FILTER_CSV = os.path.join(SCAM_PATH, "config", "Mouse_transmittance.csv")
PR_SENS_PKL = os.path.join(SCAM_PATH, "config", "mouse_PR_sensitivity_KF.pkl")
UNIVERSAL_WAVELENGTHS = np.arange(300, 600, 1)


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


def build_df_from_npz(npz_path: str) -> pd.DataFrame:
    z = np.load(npz_path, allow_pickle=True)
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


def load_mouse_eye_filter() -> np.ndarray:
    eye_filter = np.loadtxt(EYE_FILTER_CSV, delimiter=",")
    filter_wavelengths = eye_filter[:, 0]
    filter_intensities = eye_filter[:, 1]
    mask = (filter_wavelengths >= 300) & (filter_wavelengths <= 601)
    return filter_intensities[mask]


def add_interpolated_and_filtered_spectrum(
    df: pd.DataFrame, spectrum_col: str = "adjusted_corrected_spectrum"
) -> pd.DataFrame:
    if "wavelength" not in df.columns:
        raise KeyError("Missing required column: wavelength")
    if spectrum_col not in df.columns:
        raise KeyError(f"Missing required column: {spectrum_col}")

    mouse_filter = load_mouse_eye_filter()
    out = df.copy()

    def _interp(row: pd.Series) -> np.ndarray:
        interp_func = interp1d(row["wavelength"], row[spectrum_col])
        return interp_func(UNIVERSAL_WAVELENGTHS)

    out["interpolated_spectrum"] = out.apply(_interp, axis=1)
    out["filtered_spectrum"] = out["interpolated_spectrum"].apply(
        lambda arr: arr * mouse_filter / 100.0
    )
    return out


def load_pr_kernels_300_599() -> dict[str, np.ndarray]:
    with open(PR_SENS_PKL, "rb") as f:
        d = pickle.load(f)

    w = np.asarray(d["wavelength"])
    s = np.asarray(d["Scone"])
    m = np.asarray(d["Mcone"])
    r = np.asarray(d["rod"])

    mask = (w >= 300) & (w <= 599)
    return {"wavelength": w[mask], "scone": s[mask], "mcone": m[mask], "rod": r[mask]}


def add_auc_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if "filtered_spectrum" not in df.columns:
        raise KeyError("Missing required column: filtered_spectrum")

    kernels = load_pr_kernels_300_599()
    out = df.copy()
    filt_stack = np.stack(out["filtered_spectrum"].to_list())
    x = kernels["wavelength"]

    if filt_stack.shape[1] != len(x):
        raise ValueError("Kernel wavelength length does not match filtered_spectrum length.")

    out["auc_scone"] = np.trapezoid(filt_stack * kernels["scone"], x=x, axis=1)
    out["auc_mcone"] = np.trapezoid(filt_stack * kernels["mcone"], x=x, axis=1)
    out["auc_rod"] = np.trapezoid(filt_stack * kernels["rod"], x=x, axis=1)
    return out


def save_df_to_npz(df: pd.DataFrame, out_npz: str) -> None:
    out_data = {col: column_to_np_array(df[col]) for col in df.columns}
    np.savez_compressed(out_npz, **out_data)


def run_optic_filter_and_auc(target_dir: str) -> str:
    scan_npz = ensure_scan_npz(target_dir)
    df = build_df_from_npz(scan_npz)

    if "spectrum" not in df.columns:
        raise KeyError("Expected spectrum column not found in scan_data.npz")

    df["adjusted_corrected_spectrum"] = df["spectrum"]
    df = add_interpolated_and_filtered_spectrum(df, spectrum_col="adjusted_corrected_spectrum")
    df = add_auc_metrics(df)

    out_npz = os.path.join(target_dir, "scan_data_optic_filtered.npz")
    save_df_to_npz(df, out_npz)
    return out_npz
