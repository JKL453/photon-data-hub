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
    

def generate_acf_detail_from_h5(
    *,
    object_key: str,
    timing_resolution: float = 5e-9,
    bins_per_dec: int = 100,
    lag_min_exp: int = 1,
    lag_max_exp: int = 8,
    cut_points: int = 0,
    tau_min_s: float | None = 5e-7,
    tau_max_s: float | None = None,
) -> dict:
    try:
        import pycorrelate as pyc
    except ImportError as e:
        raise ImportError(
            "pycorrelate is required for ACF/CCF calculation. Install with: pip install pycorrelate"
        ) from e

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

        timestamps = ds.photons.timestamps
        detectors = ds.photons.detectors

        if timestamps is None or len(timestamps) == 0:
            raise ValueError("No photon timestamps found in file.")

        if detectors is None or len(detectors) == 0:
            raise ValueError("No detector information found in file.")

        timestamps = np.asarray(timestamps)
        detectors = np.asarray(detectors)

        t_ch0 = timestamps[detectors == 0]
        t_ch1 = timestamps[detectors == 1]

        if len(t_ch0) == 0:
            raise ValueError("Channel 0 contains no photons.")

        if len(t_ch1) == 0:
            raise ValueError("Channel 1 contains no photons.")

        bins = pyc.make_loglags(lag_min_exp, lag_max_exp, bins_per_dec)

        if bins.size < 2:
            raise ValueError("Could not generate lag bins for correlation.")

        tau_s = 0.5 * (bins[1:] + bins[:-1]) * timing_resolution

        g_acf0 = pyc.pcorrelate(t_ch0, t_ch0, bins, normalize=True)
        g_acf1 = pyc.pcorrelate(t_ch1, t_ch1, bins, normalize=True)
        g_ccf = pyc.pcorrelate(t_ch0, t_ch1, bins, normalize=True)

        tau_cut = tau_s[cut_points:]
        g_acf0_cut = g_acf0[cut_points:]
        g_acf1_cut = g_acf1[cut_points:]
        g_ccf_cut = g_ccf[cut_points:]

        mask = np.ones_like(tau_cut, dtype=bool)
        if tau_min_s is not None:
            mask &= tau_cut > tau_min_s
        if tau_max_s is not None:
            mask &= tau_cut <= tau_max_s

        tau_masked = tau_cut[mask]
        g_acf0_masked = g_acf0_cut[mask]
        g_acf1_masked = g_acf1_cut[mask]
        g_ccf_masked = g_ccf_cut[mask]

        g_acf0_masked = np.where(g_acf0_masked == 0, 1e-9, g_acf0_masked)
        g_acf1_masked = np.where(g_acf1_masked == 0, 1e-9, g_acf1_masked)
        g_ccf_masked = np.where(g_ccf_masked == 0, 1e-9, g_ccf_masked)

        return {
            "preview_kind": "acf_detail",
            "correlation_kind": "acf_ccf",
            "x": tau_masked.tolist(),
            "x_unit": "s",
            "y_unit": "G(tau)",
            "x_scale": "log",
            "series": [
                {
                    "label": "channel 0 ACF",
                    "channel": 0,
                    "y": g_acf0_masked.tolist(),
                },
                {
                    "label": "channel 1 ACF",
                    "channel": 1,
                    "y": g_acf1_masked.tolist(),
                },
                {
                    "label": "channel 0 vs channel 1 CCF",
                    "channel": None,
                    "y": g_ccf_masked.tolist(),
                },
            ],
            "meta": {
                "bins_per_dec": bins_per_dec,
                "lag_min_exp": lag_min_exp,
                "lag_max_exp": lag_max_exp,
                "n_points": int(len(tau_masked)),
                "n_series": 3,
                "cut_points": cut_points,
                "tau_min_s": tau_min_s,
                "tau_max_s": tau_max_s,
            },
        }
    

def generate_acf_thumb_from_h5(
    *,
    object_key: str,
    timing_resolution: float = 5e-9,
    bins_per_dec: int = 20,
    lag_min_exp: int = 0,
    lag_max_exp: int = 7,
    cut_points: int = 20,
    tau_min_s: float | None = 5e-6,
    tau_max_s: float | None = 5e-2,
) -> dict:
    try:
        import pycorrelate as pyc
    except ImportError as e:
        raise ImportError(
            "pycorrelate is required for ACF calculation. Install with: pip install pycorrelate"
        ) from e

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

        timestamps = ds.photons.timestamps
        detectors = ds.photons.detectors

        if timestamps is None or len(timestamps) == 0:
            raise ValueError("No photon timestamps found in file.")

        if detectors is None or len(detectors) == 0:
            raise ValueError("No detector information found in file.")

        timestamps = np.asarray(timestamps)
        detectors = np.asarray(detectors)

        t_ch0 = timestamps[detectors == 0]
        t_ch1 = timestamps[detectors == 1]

        if len(t_ch0) == 0:
            raise ValueError("Channel 0 contains no photons.")

        if len(t_ch1) == 0:
            raise ValueError("Channel 1 contains no photons.")

        bins = pyc.make_loglags(lag_min_exp, lag_max_exp, bins_per_dec)

        if bins.size < 2:
            raise ValueError("Could not generate lag bins for correlation.")

        tau_s = 0.5 * (bins[1:] + bins[:-1]) * timing_resolution

        g_acf0 = pyc.pcorrelate(t_ch0, t_ch0, bins, normalize=True)
        g_acf1 = pyc.pcorrelate(t_ch1, t_ch1, bins, normalize=True)

        tau_cut = tau_s[cut_points:]
        g_acf0_cut = g_acf0[cut_points:]
        g_acf1_cut = g_acf1[cut_points:]

        mask = np.ones_like(tau_cut, dtype=bool)
        if tau_min_s is not None:
            mask &= tau_cut > tau_min_s
        if tau_max_s is not None:
            mask &= tau_cut <= tau_max_s

        tau_masked = tau_cut[mask]
        g_acf0_masked = np.where(g_acf0_cut[mask] == 0, 1e-9, g_acf0_cut[mask])
        g_acf1_masked = np.where(g_acf1_cut[mask] == 0, 1e-9, g_acf1_cut[mask])

        return {
            "preview_kind": "acf_thumb",
            "correlation_kind": "acf",
            "x": tau_masked.tolist(),
            "x_unit": "s",
            "y_unit": "G(tau)",
            "x_scale": "log",
            "series": [
                {
                    "label": "channel 0 ACF",
                    "channel": 0,
                    "y": g_acf0_masked.tolist(),
                },
                {
                    "label": "channel 1 ACF",
                    "channel": 1,
                    "y": g_acf1_masked.tolist(),
                },
            ],
            "meta": {
                "bins_per_dec": bins_per_dec,
                "lag_min_exp": lag_min_exp,
                "lag_max_exp": lag_max_exp,
                "n_points": int(len(tau_masked)),
                "n_series": 2,
                "cut_points": cut_points,
                "tau_min_s": tau_min_s,
                "tau_max_s": tau_max_s,
            },
        }