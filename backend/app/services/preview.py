from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import photon_tools as pt

from app.services.storage import download_object_to_path


def _build_bin_edges(times_s: np.ndarray, bin_width_s: float) -> np.ndarray:
    if times_s.size == 0:
        return np.array([])

    t_min = times_s.min()
    t_max = times_s.max()

    n_bins = int(np.ceil((t_max - t_min) / bin_width_s))
    if n_bins <= 0:
        return np.array([])

    return t_min + np.arange(n_bins + 1) * bin_width_s


def _bin_with_edges(times_s: np.ndarray, edges: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if edges.size < 2:
        return np.array([]), np.array([])

    counts, _ = np.histogram(times_s, bins=edges)
    centers = edges[:-1] + 0.5 * (edges[1] - edges[0])

    return centers, counts


def _downsample_xy(
    x: np.ndarray,
    y: np.ndarray,
    max_points: int = 300,
) -> tuple[np.ndarray, np.ndarray]:
    if len(x) <= max_points:
        return x, y

    idx = np.linspace(0, len(x) - 1, max_points).astype(int)
    return x[idx], y[idx]


def generate_trace_thumb_from_h5(
    *,
    object_key: str,
    timing_resolution: float = 5e-9,
    bin_width_ms: float = 10.0,
    max_points: int = 300,
) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = Path(tmpdir) / "input.h5"

        download_object_to_path(
            object_key=object_key,
            target_path=str(local_path),
        )

        ds = pt.load(
            local_path,
            timing_resolution=timing_resolution,
        )

        times_s = ds.photons.times_s
        detectors = ds.photons.detectors

        if times_s is None or len(times_s) == 0:
            raise ValueError("No photon times found in file.")

        bin_width_s = bin_width_ms * 1e-3
        edges = _build_bin_edges(times_s, bin_width_s=bin_width_s)

        if edges.size < 2:
            raise ValueError("Could not build time bins for preview.")

        x, y_all = _bin_with_edges(times_s, edges)

        # Fallback: wenn keine Detektoren vorhanden sind, nur Gesamtkurve
        if detectors is None:
            x_ds, y_ds = _downsample_xy(x, y_all, max_points=max_points)

            return {
                "preview_kind": "trace_thumb",
                "x": x_ds.tolist(),
                "x_unit": "s",
                "y_unit": "counts_per_bin",
                "bin_width_ms": bin_width_ms,
                "downsampled_points": int(len(x_ds)),
                "n_photons": int(len(times_s)),
                "series": [
                    {
                        "label": "all photons",
                        "channel": None,
                        "y": y_ds.tolist(),
                    }
                ],
            }

        unique_channels = sorted(set(int(d) for d in detectors))
        series = []

        # Ein gemeinsames Downsampling-Index für alle Serien
        if len(x) <= max_points:
            idx = np.arange(len(x))
        else:
            idx = np.linspace(0, len(x) - 1, max_points).astype(int)

        x_ds = x[idx]

        for ch in unique_channels:
            ch_times = times_s[detectors == ch]
            _, y_ch = _bin_with_edges(ch_times, edges)
            y_ds = y_ch[idx]

            series.append(
                {
                    "label": f"channel {ch}",
                    "channel": ch,
                    "y": y_ds.tolist(),
                }
            )

        return {
            "preview_kind": "trace_thumb",
            "x": x_ds.tolist(),
            "x_unit": "s",
            "y_unit": "counts_per_bin",
            "bin_width_ms": bin_width_ms,
            "downsampled_points": int(len(x_ds)),
            "n_photons": int(len(times_s)),
            "series": series,
        }