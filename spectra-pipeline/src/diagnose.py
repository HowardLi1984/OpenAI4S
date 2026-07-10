"""Residual analysis, supporting-peak extraction, reliability diagnosis, and
config-mutation hints that drive the outer loop."""
from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks

from . import metrics
from .data import Library


def find_significant_peaks(y: np.ndarray, grid: np.ndarray, prominence_sigma: float = 4.0,
                           abs_floor: float = 0.0):
    """Peaks whose prominence exceeds max(prominence_sigma * noise std, abs_floor)."""
    noise = np.median(np.abs(np.diff(y))) * 1.4826 or 1e-9
    prom = max(prominence_sigma * noise, abs_floor)
    peaks, props = find_peaks(y, prominence=prom)
    return grid[peaks], peaks, props.get("prominences", np.array([]))


def supporting_peaks(processed_target: np.ndarray, lib: Library, name: str,
                     grid: np.ndarray, tol_cm: float = 10.0, max_peaks: int = 8):
    """For an identified component, the reference peaks that coincide with a
    peak in the observed spectrum (within tol_cm)."""
    col = lib.A[:, lib.index(name)]
    ref_pos, _, ref_prom = find_significant_peaks(col, grid, prominence_sigma=3.0)
    tgt_pos, _, _ = find_significant_peaks(processed_target, grid, prominence_sigma=3.0)
    if len(ref_pos) == 0 or len(tgt_pos) == 0:
        return []
    order = np.argsort(ref_prom)[::-1]
    matched = []
    for k in order:
        p = ref_pos[k]
        if np.min(np.abs(tgt_pos - p)) <= tol_cm:
            matched.append(round(float(p), 1))
        if len(matched) >= max_peaks:
            break
    return sorted(matched)


def diagnose(processed_target: np.ndarray, recon: np.ndarray, grid: np.ndarray, config: dict):
    """Compute reconstruction quality, detect unexplained residual peaks, and
    emit config-mutation hints. Returns a dict."""
    residual = processed_target - recon
    res_rmse = metrics.rmse(processed_target, recon)
    fit_corr = metrics.pearson(processed_target, recon)
    # scale-invariant residual so different normalisations are comparable
    tgt_norm = np.linalg.norm(processed_target) or 1e-12
    rel_residual = float(np.linalg.norm(residual) / tgt_norm)

    # unexplained peaks = positive residual peaks -> possible missing component.
    # Floor at 10% of the tallest peak so only substantial unexplained bands
    # count; smaller residuals are dominated by preprocessing artifacts near
    # sharp peaks and are NOT a reliable missing-component signal on their own.
    pos_res = np.clip(residual, 0, None)
    abs_floor = 0.10 * float(processed_target.max())
    res_peak_pos, _, res_prom = find_significant_peaks(
        pos_res, grid, prominence_sigma=5.0, abs_floor=abs_floor)
    n_res_peaks = len(res_peak_pos)

    # explained energy fraction
    denom = np.sum(processed_target ** 2) or 1e-12
    explained = 1.0 - np.sum(residual ** 2) / denom

    # reliability: driven by the robust continuous signals (correlation +
    # explained energy); residual peaks only demote when there are several.
    if fit_corr >= 0.98 and explained >= 0.95 and n_res_peaks <= 1:
        reliability = "high"
    elif fit_corr >= 0.93 and explained >= 0.88 and n_res_peaks <= 3:
        reliability = "moderate"
    else:
        reliability = "low"

    # decision hints (guide next config in the loop)
    hints = []
    if n_res_peaks >= 1 and fit_corr < 0.97:
        hints.append("possible_missing_component")   # -> raise top_k / lower corr_threshold
    if fit_corr < 0.85:
        hints.append("poor_baseline_or_denoise")     # -> try other baseline/denoise
    if explained < 0.7:
        hints.append("low_explained_energy")

    return {
        "residual_rmse": res_rmse,
        "rel_residual": rel_residual,
        "fit_corr": fit_corr,
        "explained_energy": float(explained),
        "n_residual_peaks": int(n_res_peaks),
        "residual_peak_positions": [round(float(p), 1) for p in res_peak_pos[:10]],
        "reliability": reliability,
        "hints": hints,
    }
