#!/usr/bin/env python3
import argparse
import os

import numpy as np
import pandas as pd

from spec_data_utils import (
    add_auc_metrics,
    add_interpolated_and_filtered_spectrum,
    save_df_to_npz,
)


def _pick_first_present(df: pd.DataFrame, candidates: list[str], logical_name: str) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"Missing required column for {logical_name}. Tried: {candidates}")


def _pick_optional_present(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def run_for_stsuv_pkl(pkl_path: str, wavelength_npy_path: str, out_npz_path: str | None = None) -> str:
    pkl_path = os.path.abspath(os.path.expanduser(pkl_path))
    wavelength_npy_path = os.path.abspath(os.path.expanduser(wavelength_npy_path))

    df = pd.read_pickle(pkl_path)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected DataFrame in {pkl_path}, got {type(df)}")

    ts_col = _pick_first_present(df, ["unix_ts", "timestamp"], "unix timestamp")
    spec_col = _pick_first_present(df, ["intensity", "ints"], "intensity")
    tint_col = _pick_first_present(df, ["integration_time", "t_int"], "integration time")
    pos_col = _pick_optional_present(df, ["position", "pos"])

    wavelengths = np.load(wavelength_npy_path, allow_pickle=True)
    if wavelengths.ndim != 1:
        wavelengths = np.ravel(wavelengths)

    pos_series = df[pos_col] if pos_col is not None else pd.Series([(0, 0)] * len(df), index=df.index)

    t_int_ms = pd.to_numeric(df[tint_col], errors="coerce")
    invalid_t = (~np.isfinite(t_int_ms)) | (t_int_ms <= 0)
    if invalid_t.any():
        bad_idx = t_int_ms.index[invalid_t][:5].tolist()
        raise ValueError(
            f"Integration time must be finite and > 0 ms. "
            f"Found {int(invalid_t.sum())} invalid row(s), sample indices: {bad_idx}"
        )

    # Normalize raw intensity to a 1 ms integration-time basis before downstream filtering/AUC.
    normed_spectrum = [
        np.asarray(spec, dtype=np.float64) / float(t_ms)
        for spec, t_ms in zip(df[spec_col], t_int_ms)
    ]

    out = pd.DataFrame(
        {
            "timestamp": df[ts_col],
            "t_int": t_int_ms,
            "pos": pos_series,
            "wavelength": [wavelengths] * len(df),
            "adjusted_corrected_spectrum": normed_spectrum,
        }
    )

    out = add_interpolated_and_filtered_spectrum(out, spectrum_col="adjusted_corrected_spectrum")
    out = add_auc_metrics(out)

    if out_npz_path is None:
        base = os.path.splitext(os.path.basename(pkl_path))[0]
        out_npz_path = os.path.join(os.path.dirname(pkl_path), f"{base}_optic_filtered.npz")
    out_npz_path = os.path.abspath(os.path.expanduser(out_npz_path))

    save_df_to_npz(out, out_npz_path)
    return out_npz_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Load STSUV point-scan PKL + wavelength NPY, apply mouse optic filter, "
            "compute opsin AUC metrics, and save NPZ."
        )
    )
    parser.add_argument(
        "pkl_path",
        nargs="?",
        default="./stsuv_100_data/20250422_allDay_pointSpecScan.pkl",
        help="Path to point-scan PKL file",
    )
    parser.add_argument(
        "--wavelength-npy",
        default="./stsuv_100_data/STSUV_nm.npy",
        help="Path to wavelength NPY file",
    )
    parser.add_argument("--out", default=None, help="Output NPZ path")
    args = parser.parse_args()

    out_npz = run_for_stsuv_pkl(args.pkl_path, args.wavelength_npy, args.out)
    print(f"[ok] saved: {out_npz}")


if __name__ == "__main__":
    main()
