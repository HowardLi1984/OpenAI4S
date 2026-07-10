"""RRUFF data access: download/cache, tolerant parsing, library building.

ramanspy's built-in ``rp.datasets.rruff`` crashes on RRUFF files that contain
non ``axis,intensity`` lines, so we ship a tolerant parser here and load the
cached zip ourselves.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

import numpy as np

from .config import GRID_MAX, GRID_MIN, GRID_STEP

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
RRUFF_URL = "https://rruff.info/zipped_data_files/raman/{name}.zip"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def parse_rruff_text(txt: str):
    """Tolerant RRUFF parser. Returns (metadata dict, axis array, intensity array)."""
    meta, ax, iv = {}, [], []
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("##"):
            if "=" in line:
                k, v = line[2:].split("=", 1)
                meta[k.strip()] = v.strip()
            continue
        parts = line.split(",")
        if len(parts) != 2:
            continue
        try:
            a, i = float(parts[0]), float(parts[1])
        except ValueError:
            continue
        ax.append(a)
        iv.append(i)
    return meta, np.asarray(ax), np.asarray(iv)


def mineral_from_filename(fname: str) -> str:
    """Mineral name is the token before the first '__' (e.g. Annite__R0602...)."""
    base = os.path.basename(fname)
    return base.split("__", 1)[0]


# ---------------------------------------------------------------------------
# Download / cache
# ---------------------------------------------------------------------------
def ensure_dataset(name: str = "excellent_oriented") -> str:
    """Return path to the cached zip, downloading it once if missing."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{name}.zip")
    if not os.path.exists(path) or os.path.getsize(path) < 1000:
        url = RRUFF_URL.format(name=name)
        with urlopen(url) as resp:
            data = resp.read()
        with open(path, "wb") as f:
            f.write(data)
    return path


# ---------------------------------------------------------------------------
# Resampling onto the common grid
# ---------------------------------------------------------------------------
def common_grid() -> np.ndarray:
    return np.arange(GRID_MIN, GRID_MAX + GRID_STEP / 2, GRID_STEP)


def resample(ax: np.ndarray, iv: np.ndarray, grid: np.ndarray) -> np.ndarray:
    """Linear interpolation onto grid; regions outside coverage -> 0."""
    order = np.argsort(ax)
    ax, iv = ax[order], iv[order]
    out = np.interp(grid, ax, iv, left=0.0, right=0.0)
    return out


def _grid_coverage(ax: np.ndarray, grid: np.ndarray) -> float:
    """Fraction of the grid covered by this spectrum's measured range."""
    lo, hi = ax.min(), ax.max()
    inside = (grid >= lo) & (grid <= hi)
    return float(inside.mean())


# ---------------------------------------------------------------------------
# Library
# ---------------------------------------------------------------------------
@dataclass
class Library:
    grid: np.ndarray            # (n_grid,)
    names: list                 # (n_minerals,) mineral names
    A: np.ndarray               # (n_grid, n_minerals) normalised reference spectra

    def index(self, name: str) -> int:
        return self.names.index(name)


def build_library(name: str = "excellent_oriented", max_minerals: int | None = None) -> Library:
    """Build an aligned reference matrix: one representative spectrum per mineral.

    Preference per mineral: 'Processed' file with the widest grid coverage.
    Each column is resampled onto the common grid and area-normalised.
    """
    from .preprocess import normalise  # local import to avoid cycle

    zip_path = ensure_dataset(name)
    grid = common_grid()

    # group files by mineral
    per_mineral: dict[str, list] = {}
    with ZipFile(zip_path) as z:
        for fn in z.namelist():
            if not fn.endswith(".txt"):
                continue
            mineral = mineral_from_filename(fn)
            txt = z.read(fn).decode("utf-8", "ignore")
            meta, ax, iv = parse_rruff_text(txt)
            if ax.size < 100:
                continue
            per_mineral.setdefault(mineral, []).append((fn, ax, iv))

    names, cols = [], []
    for mineral in sorted(per_mineral):
        cands = per_mineral[mineral]

        def score(item):
            fn, ax, iv = item
            processed = 1 if "Processed" in fn else 0
            return (processed, _grid_coverage(ax, grid))

        fn, ax, iv = max(cands, key=score)
        col = resample(ax, iv, grid)
        col = np.clip(col, 0, None)
        if col.max() <= 0:
            continue
        col = normalise(col, method="area")
        names.append(mineral)
        cols.append(col)

    A = np.array(cols).T  # (n_grid, n_minerals)

    if max_minerals is not None and len(names) > max_minerals:
        # keep a deterministic subset (first max_minerals alphabetically)
        names = names[:max_minerals]
        A = A[:, :max_minerals]

    return Library(grid=grid, names=names, A=A)
