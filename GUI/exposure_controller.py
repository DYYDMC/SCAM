import numpy as np


class ExposureController:
    @staticmethod
    def green_in_tolerance(target_mean, measured_mean, tol=0.05):
        if target_mean is None or measured_mean is None or measured_mean <= 0:
            return True
        ratio = float(target_mean) / float(measured_mean)
        return (1.0 - tol) <= ratio <= (1.0 + tol)

    @staticmethod
    def green_change_factor(target_mean, measured_mean, min_factor=0.7, max_factor=1.4):
        if target_mean is None or measured_mean is None or measured_mean <= 0:
            return 1.0
        ratio = float(target_mean) / float(measured_mean)
        return max(min_factor, min(max_factor, ratio))

    @staticmethod
    def uv_metrics(raw_2d_b, roi_mask):
        roi_vals = raw_2d_b[roi_mask].astype(np.float64)
        mean_ = float(roi_vals.mean())
        p99 = float(np.percentile(roi_vals, 99.0))
        sat_frac = float((roi_vals >= 65500).mean())
        return mean_, p99, sat_frac

    @staticmethod
    def uv_accept(mean_, p99, sat_frac, target_low, target_high, p99_max, sat_frac_max):
        mean_ok = target_low <= mean_ <= target_high
        clip_ok = (p99 <= p99_max) and (sat_frac <= sat_frac_max)
        return mean_ok and clip_ok, clip_ok

    @staticmethod
    def uv_change_factor(mean_, p99, sat_frac, clip_ok, target_low, target_high, p99_max, sat_frac_max, clip_safety=0.97):
        if not clip_ok:
            p99_factor = p99_max / max(p99, 1.0)
            sat_factor = sat_frac_max / max(sat_frac, 1e-9)
            return min(p99_factor, sat_factor, 1.0) * clip_safety
        if mean_ < target_low:
            return target_low / mean_
        return target_high / mean_
