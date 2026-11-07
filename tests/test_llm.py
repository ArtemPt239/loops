import asyncio
from types import SimpleNamespace

import httpx2 as httpx
import openai
import pytest

from loops import llm
from loops.llm import base_urls, chat_many, extract_code, split_think


def test_base_urls(monkeypatch):
    monkeypatch.delenv("OPENAI_BASE_URLS", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    assert base_urls() == ["http://localhost:8000/v1"]
    monkeypatch.setenv("OPENAI_BASE_URL", "http://x:1/v1")
    assert base_urls() == ["http://x:1/v1"]
    monkeypatch.setenv("OPENAI_BASE_URLS", "http://a/v1, http://b/v1,")
    assert base_urls() == ["http://a/v1", "http://b/v1"]


def test_split_think_closed():
    assert split_think("<think>\nhmm\n</think>\n\nanswer") == ("hmm", "answer", True)


def test_split_think_truncated():
    assert split_think("<think>\nstill thinking") == ("still thinking", "", False)


def test_split_think_none():
    assert split_think("just answer") == (None, "just answer", True)


def test_split_think_empty_think():
    assert split_think("<think>\n\n</think>\n\nans") == ("", "ans", True)


CODE = """Here:
```python
def helper(x):
    return x
```
and
```python
def f(a):
    return a + 1
```
then
```
print(1)
```
"""


def test_extract_code_last_block():
    assert extract_code(CODE) == "print(1)"


def test_extract_code_entry_point():
    assert extract_code(CODE, "f") == "def f(a):\n    return a + 1"
    assert extract_code(CODE, "helper").startswith("def helper")


def test_extract_code_entry_point_missing_falls_back_to_last():
    assert extract_code(CODE, "nothere") == "print(1)"


def test_extract_code_none():
    assert extract_code("no code here") is None


def test_extract_code_unclosed_block():
    assert extract_code("```python\ndef f():\n    return 1\n", "f") == "def f():\n    return 1"


class FakeCompletions:
    def __init__(self, url, calls, fail_urls):
        self.url, self.calls, self.fail_urls = url, calls, fail_urls

    async def create(self, **kw):
        self.calls.append((self.url, kw))
        await asyncio.sleep(0.01)
        if self.url in self.fail_urls:
            raise openai.APIConnectionError(request=httpx.Request("POST", self.url))
        n = kw["n"]
        choices = [
            SimpleNamespace(
                message=SimpleNamespace(content=f"<think>r</think>\n\nans{i}", reasoning_content=None),
                finish_reason="stop",
            )
            for i in range(n)
        ]
        return SimpleNamespace(choices=choices, usage=SimpleNamespace(completion_tokens=7 * n))


def test_chat_many_with_failing_endpoint(monkeypatch):
    calls = []
    urls = ["http://good1/v1", "http://bad/v1", "http://good2/v1"]
    monkeypatch.setenv("OPENAI_BASE_URLS", ",".join(urls))
    monkeypatch.setattr(llm, "RETRY_BASE_DELAY", 0.0)

    def fake_client(url):
        return SimpleNamespace(
            chat=SimpleNamespace(completions=FakeCompletions(url, calls, {"http://bad/v1"}))
        )

    monkeypatch.setattr(llm, "_make_client", fake_client)
    reqs = [
        {"messages": [{"role": "user", "content": f"q{i}"}], "n": 2, "enable_thinking": True}
        for i in range(9)
    ]
    out = asyncio.run(chat_many(reqs, concurrency=4))
    assert len(out) == 9
    for r in out:
        assert [c["text"] for c in r] == ["<think>r</think>\n\nans0", "<think>r</think>\n\nans1"]
        assert r[0]["finish_reason"] == "stop"
        assert r[0]["completion_tokens"] == 7
    kw = calls[0][1]
    assert kw["extra_body"]["chat_template_kwargs"] == {"enable_thinking": True}
    assert kw["extra_body"]["top_k"] == 20
    assert kw["temperature"] == 0.6 and kw["top_p"] == 0.95 and kw["max_tokens"] == 8192
    good = {u for u, _ in calls if u != "http://bad/v1"}
    assert good == {"http://good1/v1", "http://good2/v1"}


def test_chat_many_reasoning_field(monkeypatch):
    class C:
        async def create(self, **kw):
            msg = SimpleNamespace(content="ans", reasoning_content="why")
            return SimpleNamespace(
                choices=[SimpleNamespace(message=msg, finish_reason="length")],
                usage=SimpleNamespace(completion_tokens=3),
            )

    monkeypatch.setenv("OPENAI_BASE_URLS", "http://a/v1")
    monkeypatch.setattr(
        llm, "_make_client", lambda url: SimpleNamespace(chat=SimpleNamespace(completions=C()))
    )
    out = asyncio.run(chat_many([{"messages": [], "n": 1}]))
    assert out[0][0]["text"] == "<think>\nwhy\n</think>\n\nans"
    assert split_think(out[0][0]["text"]) == ("why", "ans", True)


def test_chat_many_all_endpoints_fail(monkeypatch):
    calls = []
    monkeypatch.setenv("OPENAI_BASE_URLS", "http://bad/v1")
    monkeypatch.setattr(llm, "RETRY_BASE_DELAY", 0.0)
    monkeypatch.setattr(
        llm,
        "_make_client",
        lambda url: SimpleNamespace(
            chat=SimpleNamespace(completions=FakeCompletions(url, calls, {"http://bad/v1"}))
        ),
    )
    with pytest.raises(openai.APIConnectionError):
        asyncio.run(chat_many([{"messages": [], "n": 1}]))
