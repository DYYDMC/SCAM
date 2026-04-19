# Spectra Timeseries Plot Changelog

## 2026-04-15: Switch AUC timeseries 5-tilt subplot y-axes to log scale

- **File**: `gif_utils.py`, function `generate_auc_timeseries_5tilt_gif`
- **Change**: Both left y-axis (S_auc, M_auc) and right y-axis (M/S ratio) now use `set_yscale("log")` instead of linear.
- **Reason**: Linear scale compressed low-value dynamics; log scale better reveals variation across orders of magnitude.
- **Lower y-limit** set to `None` (matplotlib auto) since `0` is invalid on a log scale.

## 2026-04-15: Fix drifting y-axis ticks on log-scale AUC subplot

- **File**: `gif_utils.py`, function `generate_auc_timeseries_5tilt_gif`
- **Change**: Compute `global_auc_min` across all tilts and pin the AUC y-axis to `(global_auc_min * 0.9, global_auc_max)` so the log-scale limits stay fixed across all frames.
- **Reason**: With `None` as lower limit, matplotlib auto-scaled per frame, causing tick labels to drift and get squeezed as the animation progressed.

## 2026-04-15: Apply log scale and fixed limits to M/S ratio axis (ax2)

- **File**: `gif_utils.py`, function `generate_auc_timeseries_5tilt_gif`
- **Change**: Enabled `ax2.set_yscale("log")` and pinned M/S ratio y-axis to `(global_ratio_min * 0.9, global_ratio_max)` using a precomputed global min across all tilts.
- **Reason**: Consistent with the AUC axis treatment; prevents the same tick-drifting issue on the ratio axis.
