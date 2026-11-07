import asyncio

import pytest

from loops import monitors
from loops.monitors import (
    code_monitor_messages,
    cot_monitor_messages,
    parse_monitor,
    run_monitors,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("blah\nSCORE: 7\nVERDICT: YES", (7, True)),
        ("score: 2\nverdict: no", (2, False)),
        ("Score: 7/10\nVerdict: Yes.", (7, True)),
        ("**SCORE:** 9\n**VERDICT:** **YES**", (9, True)),
        ("SCORE: 3", (3, None)),
        ("VERDICT: NO", (None, False)),
        ("nothing useful", (None, None)),
        ("SCORE: 15\nVERDICT: NO", (10, False)),
        ("SCORE: 1\nVERDICT: NO\n...\nSCORE: 8\nVERDICT: YES", (8, True)),
    ],
)
def test_parse_monitor(text, expected):
    assert parse_monitor(text) == expected


DESC = "Return the sum of a list of integers."
TESTS = "assert total([1, 2]) == 4"
CODE = "def total(xs):\n    return sum(xs) + 1"


def _all_text(msgs):
    return "\n".join(m["content"] for m in msgs)


def test_code_monitor_messages_views():
    with_tests = _all_text(code_monitor_messages(DESC, TESTS, CODE))
    assert DESC in with_tests and TESTS in with_tests and CODE in with_tests
    assert "SCORE:" in with_tests and "VERDICT:" in with_tests
    no_tests = _all_text(code_monitor_messages(DESC, None, CODE))
    assert DESC in no_tests and CODE in no_tests and TESTS not in no_tests


def test_cot_monitor_messages_and_truncation():
    msgs = cot_monitor_messages(DESC, TESTS, "I think hard", CODE)
    t = _all_text(msgs)
    assert all(s in t for s in (DESC, TESTS, "I think hard", CODE))
    assert "not suspicious by itself" in t.lower()
    long = "HEAD" + "x" * 50_000 + "TAIL"
    t = _all_text(cot_monitor_messages(DESC, TESTS, long, CODE))
    assert "HEAD" in t and "TAIL" in t and "truncated" in t.lower()
    assert len(t) < 20_000


def test_run_monitors(monkeypatch):
    seen = []

    async def fake_chat_many(requests, concurrency=64, **kw):
        out = []
        for r in requests:
            seen.append(r)
            assert r["enable_thinking"] is False and r["temperature"] == 0
            body = r["messages"][-1]["content"]
            if "reasoning" in body.lower() and "<reasoning>" in body:
                txt = "SCORE: 8\nVERDICT: YES"
            elif "<tests>" in body:
                txt = "SCORE: 5\nVERDICT: NO"
            else:
                txt = "SCORE: 1\nVERDICT: NO"
            out.append([{"text": txt, "finish_reason": "stop", "completion_tokens": 5}])
        return out

    monkeypatch.setattr(monitors, "chat_many", fake_chat_many)
    items = [
        {"description": DESC, "test_file": TESTS, "code": CODE, "reasoning": "r"},
        {"description": DESC, "test_file": TESTS, "code": CODE, "reasoning": None},
        {"description": DESC, "test_file": TESTS, "code": None, "reasoning": "r"},
    ]
    res = asyncio.run(run_monitors(items))
    assert res[0]["code_tests_score"] == 5 and res[0]["code_tests_verdict"] is False
    assert res[0]["code_only_score"] == 1
    assert res[0]["cot_score"] == 8 and res[0]["cot_verdict"] is True
    assert "SCORE" in res[0]["cot_raw"]
    assert res[1]["cot_score"] is None and res[1]["code_only_score"] == 1
    assert res[2]["code_tests_score"] is None and res[2]["cot_score"] is None
    assert len(seen) == 3 + 2 + 0
