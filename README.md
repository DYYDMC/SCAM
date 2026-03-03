# SCAM

SCAM is a Raspberry Pi based dual-camera + spectrometer acquisition project for panoramic scene capture.

The system coordinates:
- `cam0` (green channel extraction from RAW)
- `cam1` (UV / blue channel extraction from RAW)
- stepper pan/tilt motion
- spectrometer scans

Primary operation is through the Qt GUI:
- `GUI/SCAM_main_gui.py`

## Repository Layout

- `GUI/`
  - `SCAM_main_gui.py`: main GUI entrypoint and orchestration.
  - `SCAM_gui.ui`: Qt Designer UI file.
  - `SCAM_icon.png`: app icon.
- `cali/`
  - `libcamera_raw_wrapper.sh`: camera capture wrapper used by GUI (`capture_raw`, `capture_raw_pair`).
- `energy/`
  - `green_raw_config.txt`, `uv_raw_config.txt`: per-camera libcamera configs.
- `raw/`
  - `raw_prepro.py`: RAW parsing, channel extraction, ROI mean, exposure helper functions.
- `spec_scan/`
  - `spectrometer_controller.py`: spectrometer connection and scan calls.
- `stepper/OS_end/`
  - `steppers.py`: serial motor controller.
- `matlab_roi_extraction/`
  - ROI generation scripts and saved masks (`*.mat`, `*.npy`).
- `matlab_img_processing/`
  - downstream preprocessing / registration scripts.

## Runtime Workflow (Current)

### Pano capture (`on_start_pano`)
At each pan/tilt position:
1. move stepper to target position.
2. capture a UV+green pair:
   - periodic recalibration path: sequential UV/green exposure matching, then simultaneous replacement capture.
   - fast path between checkpoints: direct simultaneous capture with previous shutter/gain values.
3. keep final per-position outputs only:
   - `.raw`
   - `.json`
   - `.jpg`

### Exposure behavior
- UV exposure uses ROI-based metrics (mean + clipping checks).
- Green exposure is matched to UV via bounded multiplicative updates.
- Previous successful shutter/gain values are reused to reduce per-position adaptation time.

### Simultaneous capture
- wrapper mode `capture_raw_pair` launches both cameras in parallel.
- capture reliability includes retry/backoff and output-file polling.

## Requirements

### Hardware
- Raspberry Pi with two camera modules.
- stepper motor + controller (serial).
- supported spectrometer (via `seabreeze`).

### Software (Pi)
- Python 3
- PySide6
- numpy, matplotlib, opencv-python
- `tifffile`
- `pyserial`
- `seabreeze` (pyseabreeze backend)
- libcamera tools (`libcamera-raw`)

## Configuration Notes

- GUI currently uses an absolute `.ui` path for the Pi environment.
- Camera orientation/flip is controlled by `energy/*_raw_config.txt`.
- ROI masks are loaded from `matlab_roi_extraction/*.npy`.
- `extract_masked_mean` applies horizontal flip to `cam0` ROI to match runtime orientation.

## Data Outputs

Typical capture outputs are under:
- `pano_data/`
- `point_scan_data/`
- `full_scan/`
- `one_scam_data/`
- `full_scam/`

Each session is timestamped and stores configuration JSON plus capture/scan artifacts.

## Development Notes

- `main` is stable hardware-testing branch.
- `dev` is used for refactor work (service/module extraction).
- Refactor direction:
  - capture logic -> `GUI/capture_service.py`
  - exposure logic -> `GUI/exposure_controller.py`
  - scan workflow logic -> `GUI/scan_workflows.py`

## Quick Start

1. Ensure hardware is connected (cameras, stepper, spectrometer).
2. Verify camera configs in `energy/`.
3. Launch GUI:

```bash
python3 GUI/SCAM_main_gui.py
```

4. Use GUI buttons for:
- single scan / move + scan
- camera shots
- pano / point / full SCAM sessions

## Known Practical Constraints

- Camera startup jitter can cause intermittent missing RAW files; retry/backoff is implemented.
- Some libcamera builds may write more than one frame unless constrained; wrapper is configured for single-frame intent.
- Motion settle timing is conservative for robustness; pano has a same-tilt faster wait path.
