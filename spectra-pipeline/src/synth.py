"""Synthesise dirty mixture spectra from the library, with known ground truth."""
from __future__ import annotations

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
