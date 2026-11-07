import math

from loops.stats import auroc, cluster_bootstrap_rate, fisher_p, wilson


def test_wilson():
    p, lo, hi = wilson(5, 10)
    assert p == 0.5 and 0.18 < lo < 0.24 and 0.76 < hi < 0.82
    p, lo, hi = wilson(0, 0)
    assert math.isnan(p)
    p, lo, hi = wilson(0, 20)
    assert p == 0 and lo == 0 and 0.15 < hi < 0.17


def test_cluster_bootstrap_rate():
    values = [1, 1, 1, 0, 0, 0, 1, 0]
    groups = ["a", "a", "a", "b", "b", "b", "c", "c"]
    m, lo, hi = cluster_bootstrap_rate(values, groups, n_boot=500)
    assert m == 0.5 and 0 <= lo <= m <= hi <= 1
    assert lo < 0.4 and hi > 0.6


def test_auroc():
    auc, lo, hi = auroc([0.9, 0.8, 0.7, 0.95], [0.1, 0.2, 0.3, 0.85], n_boot=300)
    assert abs(auc - 14 / 16) < 1e-9 and lo <= auc <= hi
    auc, lo, hi = auroc([1.0], [0.0, 0.5])
    assert math.isnan(auc) and math.isnan(lo)
    auc, lo, hi = auroc(
        [0.9, 0.8, 0.7], [0.1, 0.2, 0.3], groups_pos=["a", "a", "b"], groups_neg=["a", "c", "c"], n_boot=200
    )
    assert auc == 1.0 and lo == 1.0


def test_fisher_p():
    assert fisher_p(9, 10, 1, 10) < 0.01
    assert fisher_p(1, 10, 9, 10) > 0.99
