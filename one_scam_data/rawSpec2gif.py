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


def build_titles(unix_ts: np.ndarray | None, int_t: np.ndarray | None, n_frames: int) -> list[str]:
    titles: list[str] = []
    for i in range(n_frames):
        parts = [f"Frame {i}"]
        if unix_ts is not None and i < len(unix_ts):
            dt = datetime.fromtimestamp(int(unix_ts[i]))
            parts = [dt.strftime("%Y-%m-%d %H:%M:%S")]
        if int_t is not None and i < len(int_t):
            parts.append(f"int_t={int(int_t[i])} ms")
        titles.append(" | ".join(parts))
    return titles


def normalize_by_integration_time(
    data: np.ndarray,
    int_t_ms: np.ndarray,
    mode: str,
    max_int_t_ms: float,
) -> np.ndarray:
    it = np.asarray(int_t_ms, dtype=np.float64)
    if np.any(it <= 0):
        raise ValueError("Integration time contains non-positive values.")

    if mode == "to_max":
        # Equivalent intensity if all frames had max_int_t_ms integration time.
        return data * (float(max_int_t_ms) / it[:, None])
    if mode == "per_ms":
        # Counts per ms.
        return data / it[:, None]
    raise ValueError(f"Unknown normalization mode: {mode}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate raw and filtered spectral GIFs from scan_data_optic_filtered.npz, "
            "with optional integration-time normalization/filtering."
        )
    )
    parser.add_argument("one_scam", help="ONE_SCAM_YYYYMMDD_HHMMSS folder name or full path")
    parser.add_argument("--freq", type=int, default=1, help="Frame subsampling step")
    parser.add_argument("--fr", type=int, default=30, help="Output gif fps")
    parser.add_argument("--intt", type=int, default=None, help="Only keep frames with this integration time (ms)")
    parser.add_argument(
        "--normalize-by-intt",
        action="store_true",
        help="Normalize spectra using integration time before GIF generation",
    )
    parser.add_argument(
        "--norm-mode",
        choices=["to_max", "per_ms"],
        default="per_ms",
        help="Normalization mode when --normalize-by-intt is set",
    )
    parser.add_argument(
        "--max-intt",
        type=float,
        default=5999.0,
        help="Max integration time in ms used by --norm-mode to_max",
    )
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
    if "int_t" not in z.files:
        raise KeyError("Expected key 'int_t' in npz for integration-time handling")

    raw = np.asarray(z[raw_key], dtype=np.float64)
    filtered = np.asarray(z["filtered_spectrum"], dtype=np.float64)
    int_t = np.asarray(z["int_t"], dtype=np.float64)
    unix_ts = np.asarray(z["unix_ts"]) if "unix_ts" in z.files else None

    if "wavelength" in z.files:
        raw_w = np.asarray(z["wavelength"], dtype=np.float64)
        raw_wavelengths = raw_w[0] if raw_w.ndim == 2 else raw_w
    else:
        raw_wavelengths = np.arange(raw.shape[1], dtype=np.float64)

    filtered_wavelengths = np.arange(300, 300 + filtered.shape[1], dtype=np.float64)

    keep = np.ones(raw.shape[0], dtype=bool)
    if args.intt is not None:
        keep &= int_t.astype(int) == int(args.intt)

    raw = raw[keep]
    filtered = filtered[keep]
    int_t = int_t[keep]
    if unix_ts is not None:
        unix_ts = unix_ts[keep]

    if raw.shape[0] == 0:
        raise ValueError("No frames left after filtering; adjust --intt or input data.")

    suffix = ""
    if args.normalize_by_intt:
        raw = normalize_by_integration_time(raw, int_t, mode=args.norm_mode, max_int_t_ms=args.max_intt)
        filtered = normalize_by_integration_time(filtered, int_t, mode=args.norm_mode, max_int_t_ms=args.max_intt)
        suffix += f"_norm-{args.norm_mode}"

    if args.intt is not None:
        suffix += f"_intt-{int(args.intt)}"

    titles = build_titles(unix_ts=unix_ts, int_t=int_t, n_frames=raw.shape[0])

    out_raw = os.path.join(target_dir, f"raw_spectrum{suffix}.gif")
    out_filtered = os.path.join(target_dir, f"filtered_spectrum{suffix}.gif")

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
