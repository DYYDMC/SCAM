# Spectra Timeseries Plot Changelog

## 2026-04-15: Switch AUC timeseries 5-tilt subplot y-axes to log scale

- **File**: `gif_utils.py`, function `generate_auc_timeseries_5tilt_gif`
- **Change**: Both left y-axis (S_auc, M_auc) and right y-axis (M/S ratio) now use `set_yscale("log")` instead of linear.
- **Reason**: Linear scale compressed low-value dynamics; log scale better reveals variation across orders of magnitude.
- **Lower y-limit** set to `None` (matplotlib auto) since `0` is invalid on a log scale.
