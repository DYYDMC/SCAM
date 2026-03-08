#!/usr/bin/env python3
import argparse
import os
from datetime import datetime

import numpy as np

from gif_utils import generate_gif


def resolve_one_scam_path(target: str) -> str:
    t = os.path.expanduser(target)
    if os.path.isdir(t):
        return os.path.abspath(t)

    if target.startswith("ONE_SCAM_"):
        return os.path.abspath(os.path.expanduser(f"~/Github/SCAM/one_scam_data/{target}"))

    if target.startswith("~Github/"):
        return os.path.abspath(os.path.expanduser("~/" + target[len("~") :]))

    raise FileNotFoundError(f"Cannot resolve ONE_SCAM path from: {target}")


def format_titles(npz: np.lib.npyio.NpzFile, n_frames: int) -> list[str]:
    if "unix_ts" not in npz.files:
        return [f"Frame {i}" for i in range(n_frames)]

    ts = np.asarray(npz["unix_ts"])
    titles = []
    for i in range(n_frames):
        if i < len(ts):
            dt = datetime.fromtimestamp(int(ts[i]))
            titles.append(dt.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            titles.append(f"Frame {i}")
    return titles


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate raw and filtered spectral GIFs (30 Hz default) "
            "from scan_data_optic_filtered.npz."
        )
    )
    parser.add_argument("one_scam", help="ONE_SCAM_YYYYMMDD_HHMMSS folder name or full path")
    parser.add_argument("--freq", type=int, default=1, help="Frame subsampling step")
    parser.add_argument("--fr", type=int, default=30, help="Output gif fps")
    args = parser.parse_args()

    target_dir = resolve_one_scam_path(args.one_scam)
    npz_path = os.path.join(target_dir, "scan_data_optic_filtered.npz")
    if not os.path.exists(npz_path):
        raise FileNotFoundError(f"Missing file: {npz_path}")

    z = np.load(npz_path, allow_pickle=True)

    raw_key = "spectrum" if "spectrum" in z.files else "intensity"
    if raw_key not in z.files:
        raise KeyError("Expected raw spectrum key 'spectrum' or 'intensity' in npz")
    if "filtered_spectrum" not in z.files:
        raise KeyError("Expected key 'filtered_spectrum' in npz")

    raw = np.asarray(z[raw_key], dtype=np.float64)
    filtered = np.asarray(z["filtered_spectrum"], dtype=np.float64)

    if "wavelength" in z.files:
        raw_w = np.asarray(z["wavelength"], dtype=np.float64)
        raw_wavelengths = raw_w[0] if raw_w.ndim == 2 else raw_w
    else:
        raw_wavelengths = np.arange(raw.shape[1], dtype=np.float64)

    filtered_wavelengths = np.arange(300, 300 + filtered.shape[1], dtype=np.float64)
    titles = format_titles(z, raw.shape[0])

    out_raw = os.path.join(target_dir, "raw_spectrum.gif")
    out_filtered = os.path.join(target_dir, "filtered_spectrum.gif")

    generate_gif(
        data=raw,
        wavelengths=raw_wavelengths,
        output_path=out_raw,
        freq=args.freq,
        fr=args.fr,
        titles=titles,
    )
    generate_gif(
        data=filtered,
        wavelengths=filtered_wavelengths,
        output_path=out_filtered,
        freq=args.freq,
        fr=args.fr,
        titles=titles,
    )

    print("Done:")
    print(out_raw)
    print(out_filtered)


if __name__ == "__main__":
    main()
