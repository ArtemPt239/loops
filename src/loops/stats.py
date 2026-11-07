"""Confidence intervals and tests for rates and monitor AUROC."""

import math

import numpy as np
from scipy.stats import fisher_exact
from sklearn.metrics import roc_auc_score

NAN3 = (math.nan, math.nan, math.nan)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return NAN3
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def cluster_bootstrap_rate(
    values: list[float], groups: list[str], n_boot: int = 2000, seed: int = 0
) -> tuple[float, float, float]:
    """Mean over samples with a 95% CI that resamples whole groups (samples of one task are correlated)."""
    if not values:
        return NAN3
    v = np.asarray(values, dtype=float)
    keys, inv = np.unique(np.asarray(groups), return_inverse=True)
    sums = np.bincount(inv, weights=v, minlength=len(keys))
    counts = np.bincount(inv, minlength=len(keys)).astype(float)
    idx = np.random.default_rng(seed).integers(0, len(keys), size=(n_boot, len(keys)))
    boot = sums[idx].sum(1) / counts[idx].sum(1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(v.mean()), float(lo), float(hi)


def auroc(
    pos: list[float],
    neg: list[float],
    groups_pos: list[str] | None = None,
    groups_neg: list[str] | None = None,
    n_boot: int = 2000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """AUROC of scores (positives should score higher) with a 95% bootstrap CI.

    With groups, whole groups are resampled; a group may hold both positives and negatives.
    """
    if len(pos) < 2 or len(neg) < 2:
        return NAN3
    y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]
    s = np.r_[np.asarray(pos, dtype=float), np.asarray(neg, dtype=float)]
    auc = float(roc_auc_score(y, s))
    rng = np.random.default_rng(seed)
    if groups_pos is None and groups_neg is None:
        g = np.arange(len(y))
    else:
        gp = list(groups_pos) if groups_pos is not None else [f"_pos{i}" for i in range(len(pos))]
        gn = list(groups_neg) if groups_neg is not None else [f"_neg{i}" for i in range(len(neg))]
        _, g = np.unique(np.asarray(gp + gn, dtype=str), return_inverse=True)
    n_groups = g.max() + 1
    boots = []
    for _ in range(n_boot):
        mult = np.bincount(rng.integers(0, n_groups, size=n_groups), minlength=n_groups)
        w = mult[g]
        if w[y == 1].sum() == 0 or w[y == 0].sum() == 0:
            continue
        boots.append(roc_auc_score(y, s, sample_weight=w))
    if not boots:
        return auc, math.nan, math.nan
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return auc, float(lo), float(hi)


def fisher_p(k1: int, n1: int, k2: int, n2: int) -> float:
    """One-sided Fisher exact p-value for rate1 = k1/n1 being greater than rate2 = k2/n2."""
    return float(fisher_exact([[k1, n1 - k1], [k2, n2 - k2]], alternative="greater").pvalue)
