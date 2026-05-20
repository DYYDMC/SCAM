"""Compatibility wrappers for optic filtering helpers."""
from spec_data_utils import (
    UNIVERSAL_WAVELENGTHS as universal_wavelengths,
    add_interpolated_and_filtered_spectrum,
    load_mouse_eye_filter,
)

filter_intensities_relevant = load_mouse_eye_filter()


def interpolate_to_range(row, spectrum="adjusted_corrected_spectrum"):
    df = row.to_frame().T
    out = add_interpolated_and_filtered_spectrum(df, spectrum_col=spectrum)
    return out.iloc[0]["interpolated_spectrum"]


def apply_mouse_filter(row, spectrum="interpolated_spectrum", mouse_filter=filter_intensities_relevant):
    return row[spectrum] * mouse_filter / 100


def add_interpolated_spectrum(df):
    return add_interpolated_and_filtered_spectrum(df, spectrum_col="adjusted_corrected_spectrum")
