#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import argparse
import os
from datetime import datetime

import argcomplete
import numpy as np

from gif_utils import (
    generate_auc_summary_gif,
    generate_auc_timeseries_5tilt_gif,
    generate_auc_timeseries_by_tilt_gifs,
    generate_gif,
    generate_weighted_area_gif,
)
from spec_data_utils import load_pr_kernels_300_599


def resolve_one_scam_path(target: str) -> str:
    t = os.path.expanduser(target)
    if os.path.isdir(t):
        return os.path.abspath(t)

    if target.startswith("ONE_SCAM_"):
        return os.path.abspath(os.path.expanduser(f"~/Github/SCAM/one_scam_data/{target}"))

    if target.startswith("~Github/"):
        return os.path.abspath(os.path.expanduser("~/" + target[len("~") :]))

    raise FileNotFoundError(f"Cannot resolve ONE_SCAM path from: {target}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate raw and filtered spectral GIFs from scan_data_optic_filtered.npz, "
            "with optional integration-time normalization/filtering."
        )
    )
    parser.add_argument("one_scam", help="ONE_SCAM_YYYYMMDD_HHMMSS folder name or full path")
    parser.add_argument("--freq", type=int, default=30, help="Frame subsampling step")
    parser.add_argument("--fr", type=int, default=15, help="Output gif fps")
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
    parser.add_argument(
        "--hide-intt-title",
        action="store_true",
        help="Hide integration time from frame titles (auto-enabled when normalization is on)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate GIFs even if output files already exist",
    )
    return parser


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
        return data * (float(max_int_t_ms) / it[:, None])
    if mode == "per_ms":
        return data / it[:, None]
    raise ValueError(f"Unknown normalization mode: {mode}")


def load_npz_inputs(npz_path: str) -> dict[str, np.ndarray]:
    z = np.load(npz_path, allow_pickle=True)

    raw_key = "spectrum" if "spectrum" in z.files else "intensity"
    if raw_key not in z.files:
        raise KeyError("Expected raw spectrum key 'spectrum' or 'intensity' in npz")
    if "filtered_spectrum" not in z.files:
        raise KeyError("Expected key 'filtered_spectrum' in npz")
    if "int_t" not in z.files:
        raise KeyError("Expected key 'int_t' in npz for integration-time handling")
    if "motor_tilt" not in z.files:
        raise KeyError("Expected key 'motor_tilt' in npz for tilt-wise timeseries GIFs")

    raw = np.asarray(z[raw_key], dtype=np.float64)
    filtered = np.asarray(z["filtered_spectrum"], dtype=np.float64)
    int_t = np.asarray(z["int_t"], dtype=np.float64)
    motor_tilt = np.asarray(z["motor_tilt"])
    unix_ts = np.asarray(z["unix_ts"]) if "unix_ts" in z.files else None

    if "wavelength" in z.files:
        raw_w = np.asarray(z["wavelength"], dtype=np.float64)
        raw_wavelengths = raw_w[0] if raw_w.ndim == 2 else raw_w
    else:
        raw_wavelengths = np.arange(raw.shape[1], dtype=np.float64)

    filtered_wavelengths = np.arange(300, 300 + filtered.shape[1], dtype=np.float64)

    return {
        "raw": raw,
        "filtered": filtered,
        "int_t": int_t,
        "motor_tilt": motor_tilt,
        "unix_ts": unix_ts,
        "raw_wavelengths": raw_wavelengths,
        "filtered_wavelengths": filtered_wavelengths,
    }


def apply_intt_filter(data: dict[str, np.ndarray], intt: int | None) -> dict[str, np.ndarray]:
    raw = data["raw"]
    keep = np.ones(raw.shape[0], dtype=bool)
    if intt is not None:
        keep &= data["int_t"].astype(int) == int(intt)

    out = {
        "raw": data["raw"][keep],
        "filtered": data["filtered"][keep],
        "int_t": data["int_t"][keep],
        "motor_tilt": data["motor_tilt"][keep],
        "unix_ts": data["unix_ts"][keep] if data["unix_ts"] is not None else None,
        "raw_wavelengths": data["raw_wavelengths"],
        "filtered_wavelengths": data["filtered_wavelengths"],
    }
    if out["raw"].shape[0] == 0:
        raise ValueError("No frames left after filtering; adjust --intt or input data.")
    return out


def apply_optional_normalization(
    data: dict[str, np.ndarray],
    normalize_by_intt: bool,
    norm_mode: str,
    max_intt: float,
) -> tuple[dict[str, np.ndarray], str]:
    out = dict(data)
    suffix = ""
    if normalize_by_intt:
        out["raw"] = normalize_by_integration_time(out["raw"], out["int_t"], mode=norm_mode, max_int_t_ms=max_intt)
        out["filtered"] = normalize_by_integration_time(
            out["filtered"], out["int_t"], mode=norm_mode, max_int_t_ms=max_intt
        )
        suffix += "_normedIntt"
    return out, suffix


def compute_auc_from_filtered(filtered: np.ndarray) -> dict[str, np.ndarray]:
    kernels = load_pr_kernels_300_599()
    x = kernels["wavelength"]
    if filtered.shape[1] != len(x):
        raise ValueError("filtered_spectrum width does not match 300-599 kernel range")

    auc_s = np.trapezoid(filtered * kernels["scone"], x=x, axis=1)
    auc_m = np.trapezoid(filtered * kernels["mcone"], x=x, axis=1)
    auc_r = np.trapezoid(filtered * kernels["rod"], x=x, axis=1)
    auc_m_over_s = auc_m / np.where(auc_s == 0, np.nan, auc_s)
    return {
        "kernels": kernels,
        "auc_s": auc_s,
        "auc_m": auc_m,
        "auc_r": auc_r,
        "auc_m_over_s": auc_m_over_s,
    }


def build_output_paths(target_dir: str, suffix: str) -> dict[str, str]:
    return {
        "raw": os.path.join(target_dir, f"raw_spectrum{suffix}.gif"),
        "filtered": os.path.join(target_dir, f"filtered_spectrum{suffix}.gif"),
        "weighted": os.path.join(target_dir, f"filtered_weighted_areas{suffix}.gif"),
        "auc_summary": os.path.join(target_dir, f"auc_summary_ratio{suffix}.gif"),
        "auc_5tilt": os.path.join(target_dir, f"auc_timeseries_5tilt{suffix}.gif"),
        "out_dir": target_dir,
    }


def maybe_generate(path: str, overwrite: bool, fn) -> None:
    if os.path.exists(path) and not overwrite:
        print(f"[skip] exists: {path}")
        return
    fn()


def generate_standard_gifs(
    data: dict[str, np.ndarray],
    auc: dict[str, np.ndarray],
    titles: list[str],
    outputs: dict[str, str],
    freq: int,
    fr: int,
    overwrite: bool,
) -> None:
    maybe_generate(
        outputs["raw"],
        overwrite,
        lambda: generate_gif(
            data=data["raw"],
            wavelengths=data["raw_wavelengths"],
            output_path=outputs["raw"],
            freq=freq,
            fr=fr,
            titles=titles,
        ),
    )
    maybe_generate(
        outputs["filtered"],
        overwrite,
        lambda: generate_gif(
            data=data["filtered"],
            wavelengths=data["filtered_wavelengths"],
            output_path=outputs["filtered"],
            freq=freq,
            fr=fr,
            titles=titles,
        ),
    )
    maybe_generate(
        outputs["weighted"],
        overwrite,
        lambda: generate_weighted_area_gif(
            filtered=data["filtered"],
            wavelengths=auc["kernels"]["wavelength"],
            scone=auc["kernels"]["scone"],
            mcone=auc["kernels"]["mcone"],
            rod=auc["kernels"]["rod"],
            output_path=outputs["weighted"],
            freq=freq,
            fr=fr,
            titles=titles,
        ),
    )
    maybe_generate(
        outputs["auc_summary"],
        overwrite,
        lambda: generate_auc_summary_gif(
            auc_s=auc["auc_s"],
            auc_m=auc["auc_m"],
            auc_r=auc["auc_r"],
            output_path=outputs["auc_summary"],
            freq=freq,
            fr=fr,
            titles=titles,
        ),
    )


def generate_tilt_timeseries_gifs(
    data: dict[str, np.ndarray],
    auc: dict[str, np.ndarray],
    out_dir: str,
    suffix: str,
    freq: int,
    fr: int,
    overwrite: bool,
) -> list[str]:
    if data["unix_ts"] is None:
        raise KeyError("unix_ts is required to generate tilt-wise auc_timeseries GIFs")

    expected = [
        os.path.join(out_dir, f"auc_timeseries_tilt_{int(tt)}{suffix}.gif")
        for tt in np.sort(np.unique(data["motor_tilt"]))[::-1]
    ]

    if (not overwrite) and expected and all(os.path.exists(p) for p in expected):
        for p in expected:
            print(f"[skip] exists: {p}")
        return expected

    generate_auc_timeseries_by_tilt_gifs(
        auc_s=auc["auc_s"],
        auc_m=auc["auc_m"],
        auc_m_over_s=auc["auc_m_over_s"],
        unix_ts=data["unix_ts"],
        motor_tilt=data["motor_tilt"],
        output_dir=out_dir,
        suffix=suffix,
        freq=freq,
        fr=fr,
    )
    return expected


def generate_5tilt_timeseries_gif(
    data: dict[str, np.ndarray],
    auc: dict[str, np.ndarray],
    output_path: str,
    freq: int,
    fr: int,
    overwrite: bool,
) -> str:
    if data["unix_ts"] is None:
        raise KeyError("unix_ts is required to generate 5-tilt auc_timeseries GIF")
    if os.path.exists(output_path) and not overwrite:
        print(f"[skip] exists: {output_path}")
        return output_path
    return generate_auc_timeseries_5tilt_gif(
        auc_s=auc["auc_s"],
        auc_m=auc["auc_m"],
        auc_m_over_s=auc["auc_m_over_s"],
        unix_ts=data["unix_ts"],
        motor_tilt=data["motor_tilt"],
        output_path=output_path,
        freq=freq,
        fr=fr,
    )


def main() -> None:
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    target_dir = resolve_one_scam_path(args.one_scam)
    npz_path = os.path.join(target_dir, "scan_data_optic_filtered.npz")
    if not os.path.exists(npz_path):
        raise FileNotFoundError(f"Missing file: {npz_path}")

    data = load_npz_inputs(npz_path)
    data = apply_intt_filter(data, args.intt)
    data, suffix = apply_optional_normalization(
        data,
        normalize_by_intt=args.normalize_by_intt,
        norm_mode=args.norm_mode,
        max_intt=args.max_intt,
    )
    if args.intt is not None:
        suffix += f"_intt-{int(args.intt)}"

    hide_intt_title = args.normalize_by_intt or args.hide_intt_title
    title_int_t = None if hide_intt_title else data["int_t"]
    titles = build_titles(unix_ts=data["unix_ts"], int_t=title_int_t, n_frames=data["raw"].shape[0])

    auc = compute_auc_from_filtered(data["filtered"])
    outputs = build_output_paths(target_dir, suffix)

    generate_standard_gifs(
        data=data,
        auc=auc,
        titles=titles,
        outputs=outputs,
        freq=args.freq,
        fr=args.fr,
        overwrite=args.overwrite,
    )
    tilt_outputs = generate_tilt_timeseries_gifs(
        data=data,
        auc=auc,
        out_dir=outputs["out_dir"],
        suffix=suffix,
        freq=args.freq,
        fr=args.fr,
        overwrite=args.overwrite,
    )
    out_5tilt = generate_5tilt_timeseries_gif(
        data=data,
        auc=auc,
        output_path=outputs["auc_5tilt"],
        freq=args.freq,
        fr=args.fr,
        overwrite=args.overwrite,
    )

    print("Done:")
    print(outputs["raw"])
    print(outputs["filtered"])
    print(outputs["weighted"])
    print(outputs["auc_summary"])
    print(out_5tilt)
    for p in tilt_outputs:
        print(p)


if __name__ == "__main__":
    main()
