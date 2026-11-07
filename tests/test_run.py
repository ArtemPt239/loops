import json

import loops.run as run
from loops.env import load_instances


def test_generate_appends_each_request_as_it_finishes(tmp_path, monkeypatch):
    insts = load_instances()[:2]
    out = tmp_path / "samples.jsonl"
    seen_lines = []

    async def fake_chat_many(requests, model, on_result):
        results = []
        for i, _ in enumerate(requests):
            choices = [{"text": "<think>hm</think>\n```python\ndef f(): pass\n```", "finish_reason": "stop"}]
            on_result(i, choices)
            seen_lines.append(sum(1 for _ in open(out)))
            results.append(choices)
        return results

    monkeypatch.setattr(run, "chat_many", fake_chat_many)
    rows = run.generate(insts, ["buggy", "control5"], "neutral", 1, 100, 0.6, out_path=out)
    assert seen_lines == [1, 2, 3, 4]  # written before the batch ends
    assert len(rows) == 4 and [json.loads(line)["condition"] for line in open(out)][:2] == [
        "buggy",
        "control5",
    ]
    assert rows[0]["reasoning"] == "hm" and not rows[0]["truncated"]
