"""Synthesise dirty mixture spectra from the library, with known ground truth.

A ``SynthCase`` bundles the observable dirty spectrum together with the hidden
ground truth. On disk we deliberately split the two: ``spectrum.csv`` holds the
observable (the only thing the analysis loop may read) and ``truth.json`` holds
the answer key (used once, after the loop, for evaluation).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import numpy as np

from .data import Library


@dataclass
class SynthCase:
    grid: np.ndarray
    spectrum: np.ndarray                 # dirty observed spectrum
    true_names: list                     # ground-truth component names
    true_fractions: dict = field(default_factory=dict)  # name -> fraction (sums to 1)
    meta: dict = field(default_factory=dict)


def synth_mixture(lib: Library, rng: np.random.Generator, n_components: int = None,
                  noise_level: float = 0.02, n_spikes: int = 3,
                  baseline_strength: float = 0.5, min_fraction: float = 0.15) -> SynthCase:
    """Build a dirty synthetic mixture.

    Steps: pick n components + random fractions -> weighted sum of clean
    references -> add polynomial+broad-Gaussian baseline, Gaussian noise,
    cosmic-ray spikes, random overall intensity scale.

    ``min_fraction`` enforces that every component is genuinely present
    (rejection sampling), so the task stays a real multi-component problem
    instead of collapsing to a single dominant phase.
    """
    grid = lib.grid
    n_min = len(lib.names)
    if n_components is None:
        n_components = int(rng.integers(2, 4))  # 2 or 3

    idx = rng.choice(n_min, size=n_components, replace=False)
    names = [lib.names[i] for i in idx]
    # balanced-ish fractions with a floor on the smallest component
    for _ in range(1000):
        fracs = rng.dirichlet(np.ones(n_components) * 2.0)
        if fracs.min() >= min_fraction:
            break
    true_fractions = {names[i]: float(fracs[i]) for i in range(n_components)}

    # clean mixture (references are area-normalised columns of lib.A)
    clean = lib.A[:, idx] @ fracs
    clean = clean / (clean.max() or 1.0)  # scale to ~1 for interpretable noise

    y = clean.copy()

    # --- polynomial + broad Gaussian baseline drift ---
    x = np.linspace(0, 1, len(grid))
    poly = (baseline_strength * (0.3 + 0.7 * rng.random())) * (
        rng.uniform(-1, 1) * x + rng.uniform(-1, 1) * x ** 2 + 0.5)
    center = rng.uniform(0.2, 0.8)
    gauss = baseline_strength * 0.4 * np.exp(-((x - center) ** 2) / (2 * 0.15 ** 2))
    y = y + np.clip(poly, 0, None) + gauss

    # --- Gaussian noise ---
    y = y + rng.normal(0, noise_level, size=len(grid))

    # --- cosmic-ray spikes ---
    for _ in range(n_spikes):
        pos = int(rng.integers(0, len(grid)))
        y[pos] += rng.uniform(0.3, 1.0) * (y.max())

    # --- random overall intensity scale ---
    y = y * rng.uniform(500, 2000)
    y = np.clip(y, 0, None)

    return SynthCase(
        grid=grid, spectrum=y, true_names=names, true_fractions=true_fractions,
        meta={"n_components": n_components, "noise_level": noise_level,
              "n_spikes": n_spikes, "baseline_strength": baseline_strength},
    )


# ---------------------------------------------------------------------------
# Persistence: split observable spectrum from hidden ground truth on disk
# ---------------------------------------------------------------------------
SPECTRUM_FILE = "spectrum.csv"
TRUTH_FILE = "truth.json"


def save_case(case: SynthCase, case_dir: str) -> None:
    """Persist a case to ``case_dir``.

    Writes ``spectrum.csv`` (the observable, blind input) and ``truth.json``
    (the answer key). The analysis pipeline must only ever read the former.
    """
    os.makedirs(case_dir, exist_ok=True)

    arr = np.column_stack([case.grid, case.spectrum])
    np.savetxt(
        os.path.join(case_dir, SPECTRUM_FILE), arr,
        delimiter=",", header="raman_shift,intensity", comments="",
        fmt="%.6g",
    )

    truth = {
        "true_names": list(case.true_names),
        "true_fractions": {k: float(v) for k, v in case.true_fractions.items()},
        "meta": case.meta,
    }
    with open(os.path.join(case_dir, TRUTH_FILE), "w", encoding="utf-8") as f:
        json.dump(truth, f, ensure_ascii=False, indent=2)


def load_spectrum(case_dir: str):
    """Blind loader: return ``(grid, spectrum)`` from ``spectrum.csv``.

    This is all the analysis loop is allowed to see — no ground truth.
    """
    path = os.path.join(case_dir, SPECTRUM_FILE)
    arr = np.loadtxt(path, delimiter=",", skiprows=1)
    grid, spectrum = arr[:, 0], arr[:, 1]
    return grid, spectrum


def load_truth(case_dir: str) -> dict:
    """Load the hidden answer key. Use ONLY for the final post-loop evaluation."""
    with open(os.path.join(case_dir, TRUTH_FILE), encoding="utf-8") as f:
        return json.load(f)
