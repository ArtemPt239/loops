"""Criteria table over all runs and a hack-rate plot, for results/summary.md.

uv run python -m loops.report  # writes results/criteria_table.md and results/hack_rates.png
"""

import json
from pathlib import Path


def _pct(r: dict | None, key: str = "p") -> str:
    if not r or r.get("n", 0) == 0:
        return "–"
    # The wider of Wilson and task-clustered bootstrap: the bootstrap collapses to zero width at 0% or 100%.
    lo = min(r["wilson_lo"], r.get("cluster_lo", r["wilson_lo"]))
    hi = max(r["wilson_hi"], r.get("cluster_hi", r["wilson_hi"]))
    return f"{100 * r[key]:.0f}% [{100 * lo:.0f}, {100 * hi:.0f}] ({r['k']}/{r['n']})"


def _auc(a: dict) -> str:
    if a.get("auc") is None:
        return "–"
    return f"{a['auc']:.2f} [{a['lo']:.2f}, {a['hi']:.2f}]"


def _ok(c: dict | None) -> str:
    return "–" if c is None else ("PASS" if c["pass"] else "fail")


def row(run_dir: Path, link_prefix: str) -> str:
    cfg = json.loads((run_dir / "config.json").read_text())
    m = json.loads((run_dir / "metrics.json").read_text())
    conds, mon, crit = m["conditions"], m["monitors"], m["criteria"]
    b, c = conds.get("buggy", {}), conds.get("control", {})
    hh = b.get("rates", {}).get("hidden_hack")
    cells = [
        f"[{run_dir.name}]({link_prefix}{run_dir.name}/)",
        cfg.get("variant", "?"),
        f"{cfg.get('split', '?')}, {b.get('n_tasks', '?')}×{cfg.get('samples', '?')}",
        _pct(hh),
        _pct(c.get("rates", {}).get("hidden_hack")),
        _pct(conds.get("control5", {}).get("rates", {}).get("hidden_hack")),
        _pct(b.get("rates", {}).get("hardcode")),
        _pct(b.get("rates", {}).get("honest")),
        _pct(b.get("truncated")),
        _pct(mon["code_tests"]["catch_hidden_hack"]),
        _pct(mon["code_tests"]["false_positive_honest"]),
        _auc(mon["code_tests"]["auroc_hidden_hack_vs_honest"]),
        _pct(mon["code_only"]["catch_hidden_hack"]),
        _pct(mon["code_only"]["false_positive_honest"]),
        _pct(mon["cot"]["catch_hidden_hack"]),
        _pct(mon["cot"]["false_positive_honest"]),
        _ok(crit.get("c1_reward")),
        _ok(crit.get("c3_code_monitor_blind")),
        _ok(crit.get("c4_cot_monitor_sees")),
        _ok(crit.get("c6_hack_rate")),
    ]
    return "| " + " | ".join(cells) + " |"


HEADER = [
    "run",
    "variant",
    "split, tasks×samples",
    "hidden hack (buggy)",
    "hidden hack (control, 6 correct tests)",
    "hidden hack (control5, 5 tests)",
    "hardcode",
    "honest",
    "truncated",
    "code monitor (+tests) catch",
    "code monitor (+tests) flags honest",
    "code monitor (+tests) AUROC",
    "code monitor (no tests) catch",
    "code monitor (no tests) flags honest",
    "CoT monitor catch",
    "CoT monitor flags honest",
    "C1",
    "C3",
    "C4",
    "C6",
]


def is_policy_run(d: Path) -> bool:
    """Runs with generated samples; the monitor positive-control run has its own metrics schema."""
    m = d / "metrics.json"
    return m.exists() and "conditions" in json.loads(m.read_text())


def criteria_table(run_dirs: list[Path], link_prefix: str = "../runs/") -> str:
    lines = ["| " + " | ".join(HEADER) + " |", "|" + "---|" * len(HEADER)]
    for d in run_dirs:
        if is_policy_run(d):
            lines.append(row(d, link_prefix))
    return "\n".join(lines) + "\n"


def kind_table(run_dir: Path) -> str:
    """Per-mutation-kind breakdown of one run (buggy condition): hack rate, controls, monitor results."""
    m = json.loads((run_dir / "metrics.json").read_text())
    head = [
        "mutation kind",
        "tasks",
        "hidden hack (buggy)",
        "hidden hack (control)",
        "hidden hack (control5)",
        "code monitor (+tests) catch",
        "code monitor (+tests) flags honest",
        "code monitor (+tests) AUROC",
        "CoT monitor catch",
        "CoT monitor flags honest",
    ]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for kind, k in m.get("by_mutation_kind", {}).items():
        ct, cot = k["monitors"]["code_tests"], k["monitors"]["cot"]
        cells = [
            kind,
            str(k["n_tasks"]),
            _pct(k["hidden_hack"]),
            _pct(k.get("hidden_hack_control")),
            _pct(k.get("hidden_hack_control5")),
            _pct(ct["catch_hidden_hack"]),
            _pct(ct["false_positive_honest"]),
            _auc(ct["auroc_hidden_hack_vs_honest"]),
            _pct(cot["catch_hidden_hack"]),
            _pct(cot["false_positive_honest"]),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def any_hack_table(run_dir: Path) -> str:
    """Monitors over all hacks (hidden_hack + hardcode) vs honest, buggy condition."""
    m = json.loads((run_dir / "metrics.json").read_text())
    lines = ["| monitor | catches any hack | flags honest | AUROC any hack vs honest |", "|---|---|---|---|"]
    for name, mon in m["monitors"].items():
        lines.append(
            f"| {name} | {_pct(mon['catch_any_hack'])} | {_pct(mon['false_positive_honest'])} "
            f"| {_auc(mon['auroc_any_hack_vs_honest'])} |"
        )
    return "\n".join(lines) + "\n"


def plot_hack_rates(run_dirs: list[Path], out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names, vals = [], []
    for d in run_dirs:
        if not is_policy_run(d):
            continue
        m = json.loads((d / "metrics.json").read_text())
        for cond in ["buggy", "control"]:
            r = m["conditions"].get(cond, {}).get("rates", {}).get("hidden_hack")
            if r and r["n"]:
                lo, hi = r.get("cluster_lo", r["wilson_lo"]), r.get("cluster_hi", r["wilson_hi"])
                names.append(f"{d.name}\n{cond}")
                vals.append((r["p"], r["p"] - lo, hi - r["p"], cond))
    if not vals:
        return
    fig, ax = plt.subplots(figsize=(max(6, 1.1 * len(vals)), 4))
    xs = range(len(vals))
    colors = ["#c0392b" if v[3] == "buggy" else "#7f8c8d" for v in vals]
    ax.bar(xs, [100 * v[0] for v in vals], color=colors)
    ax.errorbar(
        xs,
        [100 * v[0] for v in vals],
        yerr=[[100 * v[1] for v in vals], [100 * v[2] for v in vals]],
        fmt="none",
        c="k",
    )
    ax.axhline(10, ls="--", c="k", lw=0.8)
    ax.set_xticks(list(xs), names, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("hidden-hack rate, % of samples (95% CI)")
    fig.tight_layout()
    fig.savefig(out, dpi=150)


def think_table(run_dirs: list[Path], link_prefix: str = "../runs/") -> str:
    """Code monitors with thinking on (think_monitor.py), for runs that have them."""
    head = [
        "run",
        "view",
        "catches hidden hack",
        "catches hardcode",
        "flags honest",
        "AUROC hidden hack vs honest",
    ]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for d in run_dirs:
        f = d / "think_monitor_metrics.json"
        if not f.exists():
            continue
        m = json.loads(f.read_text())
        for view in ["code_tests", "code_only"]:
            if view not in m:
                continue
            v = m[view]
            lines.append(
                f"| [{d.name}]({link_prefix}{d.name}/) | {view}, thinking on | {_pct(v['flags_hidden_hack'])} "
                f"| {_pct(v['flags_hardcode'])} | {_pct(v['flags_honest'])} | {_auc(v['auroc_hidden_hack_vs_honest'])} |"
            )
    return "\n".join(lines) + "\n"


def main():
    runs = sorted(p for p in Path("runs").iterdir() if p.is_dir())
    Path("results").mkdir(exist_ok=True)
    Path("results/criteria_table.md").write_text(
        criteria_table(runs) + "\n### Code monitors with thinking on\n\n" + think_table(runs)
    )
    plot_hack_rates(runs, Path("results/hack_rates.png"))
    print(Path("results/criteria_table.md").read_text())


if __name__ == "__main__":
    main()
