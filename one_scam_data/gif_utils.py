import os
from typing import Iterable

import imageio.v2 as imageio
import matplotlib
import numpy as np

os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
matplotlib.use("Agg")
import matplotlib.pyplot as plt


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
