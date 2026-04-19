import os
from typing import Iterable
from datetime import datetime

import imageio.v2 as imageio
import numpy as np

os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def generate_gif(
    data: np.ndarray,
    wavelengths: np.ndarray,
    output_path: str = "output.gif",
    freq: int = 1,
    fr: int = 30,
    titles: Iterable[str] | None = None,
    y_limits: tuple[float, float] | None = None,
) -> None:
    """Create a GIF from spectra without writing temporary PNG files.

    Args:
        data: Spectral array of shape (N, D).
        wavelengths: Wavelength axis of shape (D,).
        output_path: Path to output gif.
        freq: Frame subsampling step. 1 keeps every frame.
        fr: Output frame-rate (fps).
        titles: Optional per-frame titles (length N).
        y_limits: Optional y-axis limits (min, max). If None, inferred from data.
    """
    data = np.asarray(data, dtype=np.float64)
    wavelengths = np.asarray(wavelengths, dtype=np.float64)

    if data.ndim != 2:
        raise ValueError(f"data must be 2D (N, D), got shape {data.shape}")
    if wavelengths.ndim != 1:
        raise ValueError(f"wavelengths must be 1D, got shape {wavelengths.shape}")
    if data.shape[1] != wavelengths.shape[0]:
        raise ValueError(
            f"wavelength length ({wavelengths.shape[0]}) does not match data width ({data.shape[1]})"
        )
    if freq <= 0:
        raise ValueError("freq must be > 0")
    if fr <= 0:
        raise ValueError("fr must be > 0")

    frame_indices = np.arange(0, data.shape[0], freq)
    titles_list = list(titles) if titles is not None else None

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4), dpi=120)
    line, = ax.plot(wavelengths, data[0], color="black", lw=1.5)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Intensity [AU]")
    ax.grid(alpha=0.2)

    if y_limits is None:
        y_min = float(np.nanmin(data))
        y_max = float(np.nanmax(data))
        if np.isfinite(y_min) and np.isfinite(y_max):
            pad = 0.05 * (y_max - y_min if y_max > y_min else max(1.0, abs(y_max)))
            ax.set_ylim(y_min - pad, y_max + pad)
    else:
        ax.set_ylim(y_limits)

    with imageio.get_writer(output_path, mode="I", fps=fr) as writer:
        for idx in frame_indices:
            line.set_ydata(data[idx])
            if titles_list is not None and idx < len(titles_list):
                ax.set_title(titles_list[idx])
            else:
                ax.set_title(f"Frame {idx}")

            fig.canvas.draw()
            frame = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
            writer.append_data(frame)

    plt.close(fig)
    print(f"GIF saved to {output_path}")


def generate_weighted_area_gif(
    filtered: np.ndarray,
    wavelengths: np.ndarray,
    scone: np.ndarray,
    mcone: np.ndarray,
    rod: np.ndarray,
    output_path: str,
    freq: int = 1,
    fr: int = 30,
    titles: Iterable[str] | None = None,
) -> None:
    """Generate GIF for filtered spectrum + filled weighted areas."""
    filtered = np.asarray(filtered, dtype=np.float64)
    wavelengths = np.asarray(wavelengths, dtype=np.float64)
    scone = np.asarray(scone, dtype=np.float64)
    mcone = np.asarray(mcone, dtype=np.float64)
    rod = np.asarray(rod, dtype=np.float64)

    if filtered.ndim != 2:
        raise ValueError(f"filtered must be 2D, got {filtered.shape}")
    if wavelengths.ndim != 1:
        raise ValueError(f"wavelengths must be 1D, got {wavelengths.shape}")
    if filtered.shape[1] != wavelengths.shape[0]:
        raise ValueError("filtered width and wavelength length mismatch")
    if not (len(scone) == len(mcone) == len(rod) == len(wavelengths)):
        raise ValueError("Opsin kernel lengths must match wavelengths")

    frame_indices = np.arange(0, filtered.shape[0], freq)
    titles_list = list(titles) if titles is not None else None
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    y_top = float(np.nanmax(filtered) * 1.05) if np.isfinite(np.nanmax(filtered)) else None
    s_area_all = filtered * scone[None, :]
    m_area_all = filtered * mcone[None, :]
    r_area_all = filtered * rod[None, :]
    y2_top = float(np.nanmax(np.stack([s_area_all, m_area_all, r_area_all])) * 1.05)

    fig, ax1 = plt.subplots(figsize=(11, 6), dpi=120)
    line_filtered, = ax1.plot(wavelengths, filtered[0], color="black", linestyle="-", lw=2.0, label="Filtered spectrum")
    ax1.set_xlabel("Wavelength (nm)")
    ax1.set_ylabel("Filtered intensity", color="black")
    ax1.tick_params(axis="y", labelcolor="black")
    ax1.grid(alpha=0.2)
    if y_top is not None:
        ax1.set_ylim(0, y_top)

    ax2 = ax1.twinx()
    ax2.set_ylabel("Weighted area")
    # Keep y=0 at identical screen location on both axes.
    ax2.set_ylim(0, y2_top if np.isfinite(y2_top) and y2_top > 0 else 1.0)

    s_fill = ax2.fill_between(wavelengths, 0, filtered[0] * scone, color="purple", alpha=0.22, label="Area: filtered × S-cone")
    m_fill = ax2.fill_between(wavelengths, 0, filtered[0] * mcone, color="lime", alpha=0.22, label="Area: filtered × M-cone")
    r_fill = ax2.fill_between(wavelengths, 0, filtered[0] * rod, color="green", alpha=0.18, label="Area: filtered × Rod")

    l1, lb1 = ax1.get_legend_handles_labels()
    l2, lb2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, lb1 + lb2, loc="upper right")

    with imageio.get_writer(output_path, mode="I", fps=fr) as writer:
        for idx in frame_indices:
            line_filtered.set_ydata(filtered[idx])
            for coll in (s_fill, m_fill, r_fill):
                coll.remove()
            s_fill = ax2.fill_between(wavelengths, 0, filtered[idx] * scone, color="purple", alpha=0.22)
            m_fill = ax2.fill_between(wavelengths, 0, filtered[idx] * mcone, color="lime", alpha=0.22)
            r_fill = ax2.fill_between(wavelengths, 0, filtered[idx] * rod, color="green", alpha=0.18)

            if titles_list is not None and idx < len(titles_list):
                ax1.set_title(f"Filtered Spectrum with Filled Weighted Areas | {titles_list[idx]}")
            else:
                ax1.set_title(f"Filtered Spectrum with Filled Weighted Areas | Frame {idx}")

            fig.canvas.draw()
            frame = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
            writer.append_data(frame)

    plt.close(fig)
    print(f"GIF saved to {output_path}")


def generate_auc_summary_gif(
    auc_s: np.ndarray,
    auc_m: np.ndarray,
    auc_r: np.ndarray,
    output_path: str,
    freq: int = 1,
    fr: int = 30,
    titles: Iterable[str] | None = None,
) -> None:
    """Generate GIF for standalone AUC summary + M/S ratio bars."""
    auc_s = np.asarray(auc_s, dtype=np.float64)
    auc_m = np.asarray(auc_m, dtype=np.float64)
    auc_r = np.asarray(auc_r, dtype=np.float64)
    if not (len(auc_s) == len(auc_m) == len(auc_r)):
        raise ValueError("AUC arrays must have same length")

    frame_indices = np.arange(0, len(auc_s), freq)
    titles_list = list(titles) if titles is not None else None
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    y_max = float(np.nanmax(np.vstack([auc_s, auc_m, auc_r])) * 1.1)
    labels = ["Scone", "Mcone", "Rod"]
    colors = ["purple", "lime", "green"]

    fig, ax = plt.subplots(figsize=(7, 5), dpi=120)

    with imageio.get_writer(output_path, mode="I", fps=fr) as writer:
        for idx in frame_indices:
            ax.clear()
            vals = [auc_s[idx], auc_m[idx], auc_r[idx]]
            ratio = auc_m[idx] / auc_s[idx] if auc_s[idx] != 0 else np.nan
            bars = ax.bar(labels, vals, color=colors)
            ax.set_ylabel("AUC")
            ax.grid(axis="y", alpha=0.2)
            ax.set_ylim(0, y_max)
            if titles_list is not None and idx < len(titles_list):
                ax.set_title(f"AUC Summary | M/S={ratio:.4f} | {titles_list[idx]}")
            else:
                ax.set_title(f"AUC Summary | M/S={ratio:.4f} | Frame {idx}")

            for b in bars:
                h = b.get_height()
                ax.text(b.get_x() + b.get_width() / 2, h, f"{h:.1f}", ha="center", va="bottom", fontsize=9)

            fig.canvas.draw()
            frame = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
            writer.append_data(frame)

    plt.close(fig)
    print(f"GIF saved to {output_path}")


def generate_auc_timeseries_gif(
    auc_s: np.ndarray,
    auc_m: np.ndarray,
    auc_m_over_s: np.ndarray,
    unix_ts: np.ndarray,
    output_path: str,
    freq: int = 1,
    fr: int = 30,
) -> None:
    """Generate cumulative time-series GIF for M_auc, S_auc and M_auc/S_auc."""
    auc_s = np.asarray(auc_s, dtype=np.float64)
    auc_m = np.asarray(auc_m, dtype=np.float64)
    auc_m_over_s = np.asarray(auc_m_over_s, dtype=np.float64)
    unix_ts = np.asarray(unix_ts, dtype=np.int64)

    n = len(auc_s)
    if not (len(auc_m) == len(auc_m_over_s) == len(unix_ts) == n):
        raise ValueError("All time-series arrays must have the same length")

    frame_indices = np.arange(0, n, freq)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    dt = mdates.date2num([datetime.fromtimestamp(int(t)) for t in unix_ts])
    y_auc_max = float(np.nanmax(np.vstack([auc_s, auc_m])) * 1.1)
    y_ratio_max = float(np.nanmax(auc_m_over_s) * 1.1) if np.isfinite(np.nanmax(auc_m_over_s)) else 1.0
    if y_auc_max <= 0 or not np.isfinite(y_auc_max):
        y_auc_max = 1.0
    if y_ratio_max <= 0 or not np.isfinite(y_ratio_max):
        y_ratio_max = 1.0

    fig, ax1 = plt.subplots(figsize=(11, 5), dpi=120)
    ax2 = ax1.twinx()

    with imageio.get_writer(output_path, mode="I", fps=fr) as writer:
        for idx in frame_indices:
            j = idx + 1
            ax1.clear()
            ax2.clear()

            ax1.plot(dt[:j], auc_s[:j], color="purple", linestyle="-", lw=1.8, label="S_auc")
            ax1.plot(dt[:j], auc_m[:j], color="lime", linestyle="-", lw=1.8, label="M_auc")
            ax2.plot(dt[:j], auc_m_over_s[:j], color="black", linestyle="-", lw=1.6, label="M_auc/S_auc")

            ax1.set_ylabel("AUC")
            ax2.set_ylabel("M_auc / S_auc")
            ax1.set_ylim(0, y_auc_max)
            ax2.set_ylim(0, y_ratio_max)
            ax1.grid(alpha=0.2)

            ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M:%S"))
            ax1.set_xlabel("Timestamp")
            fig.autofmt_xdate(rotation=20)
            ax1.set_title("Time-series Build-up: M_auc, S_auc, and M_auc/S_auc")

            l1, lb1 = ax1.get_legend_handles_labels()
            l2, lb2 = ax2.get_legend_handles_labels()
            ax1.legend(l1 + l2, lb1 + lb2, loc="upper left")

            fig.canvas.draw()
            frame = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
            writer.append_data(frame)

    plt.close(fig)
    print(f"GIF saved to {output_path}")


def generate_auc_timeseries_by_tilt_gifs(
    auc_s: np.ndarray,
    auc_m: np.ndarray,
    auc_m_over_s: np.ndarray,
    unix_ts: np.ndarray,
    motor_tilt: np.ndarray,
    output_dir: str,
    suffix: str = "",
    freq: int = 1,
    fr: int = 30,
) -> list[str]:
    """Generate one cumulative (growing-line) AUC time-series GIF per tilt."""
    auc_s = np.asarray(auc_s, dtype=np.float64)
    auc_m = np.asarray(auc_m, dtype=np.float64)
    auc_m_over_s = np.asarray(auc_m_over_s, dtype=np.float64)
    unix_ts = np.asarray(unix_ts, dtype=np.int64)
    motor_tilt = np.asarray(motor_tilt)

    n = len(auc_s)
    if not (len(auc_m) == len(auc_m_over_s) == len(unix_ts) == len(motor_tilt) == n):
        raise ValueError("All arrays must have the same length")

    os.makedirs(output_dir, exist_ok=True)
    outputs: list[str] = []

    all_tilts = np.unique(motor_tilt)
    all_tilts = np.sort(all_tilts)[::-1]

    for tt in all_tilts:
        mask = motor_tilt == tt
        if not np.any(mask):
            continue

        ts = unix_ts[mask]
        s = auc_s[mask]
        m = auc_m[mask]
        r = auc_m_over_s[mask]

        order = np.argsort(ts)
        ts = ts[order]
        s = s[order]
        m = m[order]
        r = r[order]

        if len(ts) < 2:
            continue

        dt = mdates.date2num([datetime.fromtimestamp(int(t)) for t in ts])
        x_min, x_max = dt[0], dt[-1]
        y_auc_max = float(np.nanmax(np.vstack([s, m])) * 1.1)
        y_ratio_max = float(np.nanmax(r) * 1.1) if np.isfinite(np.nanmax(r)) else 1.0
        if y_auc_max <= 0 or not np.isfinite(y_auc_max):
            y_auc_max = 1.0
        if y_ratio_max <= 0 or not np.isfinite(y_ratio_max):
            y_ratio_max = 1.0

        frame_indices = np.arange(0, len(ts), freq)
        out = os.path.join(output_dir, f"auc_timeseries_tilt_{int(tt)}{suffix}.gif")

        fig, ax1 = plt.subplots(figsize=(11, 5), dpi=120)
        ax2 = ax1.twinx()
        fig.subplots_adjust(right=0.72)

        with imageio.get_writer(out, mode="I", fps=fr) as writer:
            for idx in frame_indices:
                j = idx + 1
                ax1.clear()
                ax2.clear()

                # Growing lines on fixed full-length axes.
                ax1.plot(dt[:j], s[:j], color="purple", linestyle="-", lw=1.8, label="S_auc")
                ax1.plot(dt[:j], m[:j], color="lime", linestyle="-", lw=1.8, label="M_auc")
                ax2.plot(dt[:j], r[:j], color="black", linestyle="-", lw=1.6, label="M_auc/S_auc")

                ax1.set_xlim(x_min, x_max)
                ax1.set_ylim(0, y_auc_max)
                ax2.set_ylim(0, y_ratio_max)
                ax1.set_ylabel("AUC")
                ax2.set_ylabel("M_auc / S_auc")
                ax2.yaxis.set_label_position("right")
                ax2.yaxis.tick_right()
                ax1.set_xlabel("Timestamp")
                ax1.grid(alpha=0.2)
                ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M:%S"))
                fig.autofmt_xdate(rotation=20)
                ax1.set_title(f"Tilt {int(tt)} | Time-series Build-up")

                l1, lb1 = ax1.get_legend_handles_labels()
                l2, lb2 = ax2.get_legend_handles_labels()
                ax1.legend(l1 + l2, lb1 + lb2, loc="upper left", bbox_to_anchor=(1.14, 1.0), borderaxespad=0.0)

                fig.canvas.draw()
                frame = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
                writer.append_data(frame)

        plt.close(fig)
        print(f"GIF saved to {out}")
        outputs.append(out)

    return outputs


def generate_auc_timeseries_5tilt_gif(
    auc_s: np.ndarray,
    auc_m: np.ndarray,
    auc_m_over_s: np.ndarray,
    unix_ts: np.ndarray,
    motor_tilt: np.ndarray,
    output_path: str,
    freq: int = 1,
    fr: int = 30,
) -> str:
    """Generate one GIF with up to 5 tilt subplots (growing lines, fixed axes)."""
    auc_s = np.asarray(auc_s, dtype=np.float64)
    auc_m = np.asarray(auc_m, dtype=np.float64)
    auc_m_over_s = np.asarray(auc_m_over_s, dtype=np.float64)
    unix_ts = np.asarray(unix_ts, dtype=np.int64)
    motor_tilt = np.asarray(motor_tilt)

    n = len(auc_s)
    if not (len(auc_m) == len(auc_m_over_s) == len(unix_ts) == len(motor_tilt) == n):
        raise ValueError("All arrays must have the same length")

    all_tilts = np.sort(np.unique(motor_tilt))[::-1][:5]
    if len(all_tilts) == 0:
        raise ValueError("No tilt data found")

    per_tilt = []
    max_frames = 0
    global_auc_max = 0.0
    global_auc_min = np.inf
    global_ratio_max = 0.0
    global_ratio_min = np.inf
    for tt in all_tilts:
        mask = motor_tilt == tt
        ts = unix_ts[mask]
        s = auc_s[mask]
        m = auc_m[mask]
        r = auc_m_over_s[mask]
        order = np.argsort(ts)
        ts, s, m, r = ts[order], s[order], m[order], r[order]
        if len(ts) < 2:
            continue
        dt = mdates.date2num([datetime.fromtimestamp(int(t)) for t in ts])
        y_auc_max = float(np.nanmax(np.vstack([s, m])) * 1.1)
        y_ratio_max = float(np.nanmax(r) * 1.1) if np.isfinite(np.nanmax(r)) else 1.0
        if y_auc_max <= 0 or not np.isfinite(y_auc_max):
            y_auc_max = 1.0
        if y_ratio_max <= 0 or not np.isfinite(y_ratio_max):
            y_ratio_max = 1.0
        y_auc_min = float(np.nanmin(np.vstack([s, m])))
        if y_auc_min <= 0 or not np.isfinite(y_auc_min):
            y_auc_min = 1e-3
        y_ratio_min = float(np.nanmin(r))
        if y_ratio_min <= 0 or not np.isfinite(y_ratio_min):
            y_ratio_min = 1e-3
        global_auc_min = min(global_auc_min, y_auc_min)
        global_auc_max = max(global_auc_max, y_auc_max)
        global_ratio_min = min(global_ratio_min, y_ratio_min)
        global_ratio_max = max(global_ratio_max, y_ratio_max)
        per_tilt.append(
            {
                "tilt": int(tt),
                "dt": dt,
                "auc_s": s,
                "auc_m": m,
                "ratio": r,
                "x_min": dt[0],
                "x_max": dt[-1],
            }
        )
        max_frames = max(max_frames, len(ts))

    if not per_tilt:
        raise ValueError("No tilt groups had at least 2 samples")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    frame_indices = np.arange(0, max_frames, freq)

    fig, axes = plt.subplots(len(per_tilt), 1, figsize=(12, 2.6 * len(per_tilt)), dpi=120, sharex=False)
    if len(per_tilt) == 1:
        axes = [axes]
    fig.subplots_adjust(right=0.88, hspace=0.5)

    with imageio.get_writer(output_path, mode="I", fps=fr) as writer:
        for idx in frame_indices:
            for ax in axes:
                ax.clear()

            for ax, d in zip(axes, per_tilt):
                j = min(idx + 1, len(d["dt"]))
                ax2 = ax.twinx()
                ax.plot(d["dt"][:j], d["auc_s"][:j], color="purple", lw=1.6, label="S_auc")
                ax.plot(d["dt"][:j], d["auc_m"][:j], color="lime", lw=1.6, label="M_auc")
                ax2.plot(d["dt"][:j], d["ratio"][:j], color="black", lw=1.4, label="M_auc/S_auc")

                ax.set_xlim(d["x_min"], d["x_max"])
                ax.set_yscale("log")
                ax.set_ylim(global_auc_min * 0.9, global_auc_max)
                ax2.set_ylim(global_ratio_min * 0.9, global_ratio_max)
                ax.set_ylabel("AUC")
                ax2.set_ylabel("M/S")
                ax2.yaxis.set_label_position("right")
                ax2.yaxis.tick_right()
                ax.grid(alpha=0.2)
                ax.set_title(f"Tilt {d['tilt']}")
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M:%S"))
                ax.tick_params(axis="x", rotation=20)

            axes[-1].set_xlabel("Timestamp")
            fig.suptitle("Time-series Build-up Across 5 Tilts", y=0.995)
            fig.canvas.draw()
            frame = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
            writer.append_data(frame)

    plt.close(fig)
    print(f"GIF saved to {output_path}")
    return output_path
    if global_auc_max <= 0 or not np.isfinite(global_auc_max):
        global_auc_max = 1.0
    if global_ratio_max <= 0 or not np.isfinite(global_ratio_max):
        global_ratio_max = 1.0
