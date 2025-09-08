import numpy as np
'''
Example usage:

sched = IntTimeScheduler(
    target_counts=45_000,
    accept_max=65_535,
    min_int_ms=0.001,
    max_int_ms=1000.0,
    alpha0=0.8,         # start assertive
    min_factor=1/3,
    max_factor=3.0,
    ema_beta=0.6,
    percentile=99.9
)

current_int = 0.01  # ms
iter_counter = 0
while True:
    spec.integration_time_micros(current_int * 1e3)  # ms -> µs
    _, raw_value = spec.spectrum()

    # use your domain criteria to stop; example keeps your nm checks
    ints_clean = raw_value - dark_1ms
    target_nm1_mean = float(np.mean(ints_clean[capped_target_nm1_idx]))
    target_nm2_mean = float(np.mean(ints_clean[capped_target_nm2_idx]))

    if np.max(raw_value) >= 65_535 and current_int <= sched.min_int + 1e-9:
        break  # irrecoverable overexposure at min integration time

    if target_nm1_mean > 1000 and target_nm2_mean > 1000:
        break

    next_int, info = sched.propose(current_int, raw_value)
    current_int = next_int
    iter_counter += 1
    
'''
class IntTimeScheduler:
    def __init__(self,
        target_counts=45_000,
        accept_max=65_535,
        min_int_ms=0.001,
        max_int_ms=1000.0,
        # ↑ direction
        alpha0=0.8,
        min_factor=1/3, max_factor=3.0,
        # ↓ direction (new)
        alpha0_dec=1.0,                 # stronger than ↑
        min_factor_dec=0.05,            # allow big cuts
        # common
        ema_beta=0.6, percentile=99.9,
        cooldown_iters=1,
        deadband_rel=0.02               # ±2% no-op band
    ):
        self.target = float(target_counts)
        self.accept_max = float(accept_max)
        self.min_int = float(min_int_ms)
        self.max_int = float(max_int_ms)
        self.alpha0 = float(alpha0)
        self.alpha0_dec = float(alpha0_dec)
        self.min_factor = float(min_factor)
        self.max_factor = float(max_factor)
        self.min_factor_dec = float(min_factor_dec)
        self.beta = float(ema_beta)
        self.perc = float(percentile)
        self.cooldown_iters = int(cooldown_iters)
        self.deadband_rel = float(deadband_rel)
        self.t = 1
        self.ema_measure = None
        self.prev = None  # (int_ms, meas)
        self.direction_hist = deque(maxlen=6)
        self.cooldown = 0

    def _alpha_inc(self):  # ↑ anneal
        return self.alpha0 / np.sqrt(self.t)

    def _alpha_dec(self):  # ↓ anneal, separate track
        return self.alpha0_dec / np.sqrt(self.t)

    def _robust_measure(self, raw):
        return float(np.percentile(raw, self.perc))

    def _update_ema(self, m):
        self.ema_measure = m if self.ema_measure is None else self.beta*m + (1-self.beta)*self.ema_measure
        return self.ema_measure

    def _headroom_backoff(self, headroom):
        # Stronger cuts as we approach saturation
        if headroom < 200:   return 0.10
        if headroom < 1000:  return 0.25
        if headroom < 3000:  return 0.50
        return None  # no forced cut

    def _predictive_factor(self, current_int_ms, meas):
        # Estimate slope d(meas)/d(int_ms) using last point; fall back if unavailable or flat
        if not self.prev:
            return None
        prev_int_ms, prev_meas = self.prev
        dI = current_int_ms - prev_int_ms
        dM = meas - prev_meas
        if abs(dI) < 1e-12 or abs(dM) < 1e-6:
            return None
        slope = dM / dI
        # desired Δint to reach target (linearized)
        delta_int = (self.target - meas) / slope
        pred_int = np.clip(current_int_ms + delta_int, self.min_int, self.max_int)
        if pred_int <= 0:
            return None
        return float(pred_int / current_int_ms)

    def propose(self, current_int_ms, raw_counts):
        # 0) saturation guard
        max_val = float(np.max(raw_counts))
        if max_val >= 0.995 * self.accept_max:
            next_int = max(current_int_ms * 0.25, self.min_int)
            self.cooldown = self.cooldown_iters
            self.direction_hist.append(-1)
            self.t += 1
            self.prev = (current_int_ms, self.ema_measure if self.ema_measure is not None else 0.0)
            return next_int, {"reason": "saturation_backoff", "max": max_val}

        # 1) robust measure + smoothing
        meas = self._update_ema(self._robust_measure(raw_counts))

        # 2) deadband
        rel_err = abs(meas / self.target - 1.0)
        if rel_err < self.deadband_rel:
            self.t += 1
            self.prev = (current_int_ms, meas)
            self.direction_hist.append(0)
            return current_int_ms, {"reason": "deadband_hold", "measure": meas}

        # 3) compute ratio factor and optional prediction
        ratio = self.target / max(meas, 1.0)
        if meas < self.target:
            alpha = self._alpha_inc()
            factor_r = float(np.clip(ratio**alpha, self.min_factor, self.max_factor))
            factor_p = self._predictive_factor(current_int_ms, meas)
            # blend prediction gently on ↑ to avoid overshoot
            if factor_p is not None and factor_p > 1.0:
                factor = 0.5*factor_r + 0.5*float(np.clip(factor_p, 1.0, self.max_factor))
            else:
                factor = factor_r
        else:
            # ↓ direction
            alpha = self._alpha_dec()
            # headroom-based override near saturation
            headroom = self.accept_max - max_val
            forced = self._headroom_backoff(headroom)
            if forced is not None:
                factor = forced
            else:
                # ratio-based decay
                # ratio < 1 → reduce; clamp to [min_factor_dec, 1]
                factor_r = float(np.clip(ratio**alpha, self.min_factor_dec, 1.0))
                factor_p = self._predictive_factor(current_int_ms, meas)
                # prefer prediction when reducing; it’s safer to cut deeper
                if factor_p is not None and factor_p < 1.0:
                    factor = float(np.clip(factor_p, self.min_factor_dec, 1.0))
                    # blend toward stronger of the two cuts
                    factor = min(factor, factor_r)
                else:
                    factor = factor_r

        # 4) cooldown behavior: block increases right after forced backoff
        if self.cooldown > 0 and factor > 1.0:
            factor = 1.0
            self.cooldown -= 1

        next_int = float(np.clip(current_int_ms * factor, self.min_int, self.max_int))

        # 5) record, advance
        self.direction_hist.append(1 if factor > 1.0 else -1 if factor < 1.0 else 0)
        self.t += 1
        self.prev = (current_int_ms, meas)
        return next_int, {
            "reason": "ratio_dec" if meas > self.target else "ratio_inc",
            "measure": meas, "ratio": ratio, "alpha": alpha, "factor": factor
        }
