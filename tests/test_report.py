import json

from loops.metrics import compute_metrics
from loops.report import criteria_table
from tests.test_metrics import _toy


def test_criteria_table_has_row_per_run_with_link(tmp_path):
    for name in ["20261107-140000-neutral", "20261107-141000-release"]:
        d = tmp_path / name
        d.mkdir()
        (d / "config.json").write_text(
            json.dumps({"variant": name.split("-")[-1], "split": "dev", "samples": 1})
        )
        (d / "metrics.json").write_text(json.dumps(compute_metrics(_toy())))
    table = criteria_table(sorted(tmp_path.iterdir()), link_prefix="../runs/")
    lines = [line for line in table.splitlines() if line.startswith("| [")]
    assert len(lines) == 2
    assert "](../runs/20261107-140000-neutral/)" in lines[0]
    assert "PASS" in table
