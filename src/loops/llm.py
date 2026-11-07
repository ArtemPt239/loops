"""Async client for the vLLM OpenAI-compatible endpoints, plus parsing of model output."""

import asyncio
from collections.abc import Callable
import os
import re
import time

import openai

DEFAULT_MODEL = "Qwen/Qwen3-8B"
# Qwen3 recommended sampling for thinking mode.
POLICY_SAMPLING = {"temperature": 0.6, "top_p": 0.95, "max_tokens": 8192}
TOP_K = 20
REQUEST_TIMEOUT = 3600.0  # long thinking under load runs > 10 min, and a retry restarts generation
MAX_ATTEMPTS = 6
RETRY_BASE_DELAY = 2.0
# After this many consecutive failures an endpoint is skipped for ENDPOINT_COOLDOWN seconds.
ENDPOINT_MAX_FAILS = 3
ENDPOINT_COOLDOWN = 60.0
PROGRESS_EVERY = 50

TRANSIENT_ERRORS = (
    openai.APIConnectionError,  # includes APITimeoutError
    openai.InternalServerError,
    openai.RateLimitError,
)


def base_urls() -> list[str]:
    raw = (
        os.environ.get("OPENAI_BASE_URLS") or os.environ.get("OPENAI_BASE_URL") or "http://localhost:8000/v1"
    )
    return [u.strip() for u in raw.split(",") if u.strip()]


def _make_client(url: str):
    return openai.AsyncOpenAI(
        base_url=url,
        api_key=os.environ.get("OPENAI_API_KEY", "EMPTY"),
        timeout=REQUEST_TIMEOUT,
        max_retries=0,
    )


class _Endpoint:
    def __init__(self, url: str, concurrency: int):
        self.url = url
        self.client = _make_client(url)
        self.sem = asyncio.Semaphore(concurrency)
        self.load = 0
        self.fails = 0
        self.down_until = 0.0


def _pick(endpoints: list[_Endpoint], avoid: _Endpoint | None) -> _Endpoint:
    now = time.monotonic()
    up = [e for e in endpoints if e.down_until <= now] or endpoints
    if avoid is not None and len(up) > 1:
        up = [e for e in up if e is not avoid]
    return min(up, key=lambda e: e.load)


def _choice_text(msg) -> str:
    content = getattr(msg, "content", None) or ""
    reasoning = getattr(msg, "reasoning_content", None) or getattr(msg, "reasoning", None)
    if reasoning:
        return f"<think>\n{reasoning}\n</think>\n\n{content}"
    return content


def _parse_response(resp) -> list[dict]:
    texts = [_choice_text(c.message) for c in resp.choices]
    total = getattr(getattr(resp, "usage", None), "completion_tokens", None) or 0
    # The API reports tokens summed over the n choices; split them in proportion to text length.
    chars = sum(len(t) for t in texts) or 1
    return [
        {
            "text": t,
            "finish_reason": c.finish_reason,
            "completion_tokens": round(total * len(t) / chars) if len(texts) > 1 else total,
        }
        for t, c in zip(texts, resp.choices)
    ]


async def _one(req: dict, endpoints: list[_Endpoint], model: str) -> list[dict]:
    kwargs = {
        "model": model,
        "messages": req["messages"],
        "n": req.get("n", 1),
        "max_tokens": req.get("max_tokens", POLICY_SAMPLING["max_tokens"]),
        "temperature": req.get("temperature", POLICY_SAMPLING["temperature"]),
        "top_p": req.get("top_p", POLICY_SAMPLING["top_p"]),
        "presence_penalty": req.get("presence_penalty", 0.0),
        "extra_body": {
            "chat_template_kwargs": {"enable_thinking": req.get("enable_thinking", True)},
            "top_k": req.get("top_k", TOP_K),
        },
    }
    last: _Endpoint | None = None
    for attempt in range(MAX_ATTEMPTS):
        ep = _pick(endpoints, last)
        ep.load += 1
        try:
            async with ep.sem:
                resp = await ep.client.chat.completions.create(**kwargs)
            ep.fails = 0
            return _parse_response(resp)
        except TRANSIENT_ERRORS as e:
            ep.fails += 1
            if ep.fails >= ENDPOINT_MAX_FAILS:
                ep.down_until = time.monotonic() + ENDPOINT_COOLDOWN
            if attempt == MAX_ATTEMPTS - 1:
                raise
            print(f"[llm] {type(e).__name__} on {ep.url} (attempt {attempt + 1}), retrying", flush=True)
            last = ep
            await asyncio.sleep(min(RETRY_BASE_DELAY * 2**attempt, 30.0))
        except openai.BadRequestError as e:
            # e.g. prompt longer than the context window: drop this request, keep the batch alive.
            return [
                {"text": "", "finish_reason": "error", "completion_tokens": 0, "error": str(e)}
                for _ in range(kwargs["n"])
            ]
        finally:
            ep.load -= 1
    raise AssertionError("unreachable")


async def chat_many(
    requests: list[dict],
    concurrency: int = 48,
    model: str = DEFAULT_MODEL,
    on_result: Callable[[int, list[dict]], None] | None = None,
) -> list[list[dict]]:
    """Run chat requests over all endpoints in `base_urls()`.

    Each request: {"messages", "n", "max_tokens", "temperature", "top_p", "enable_thinking"}; missing
    sampling keys default to POLICY_SAMPLING. `concurrency` is the max in-flight requests per endpoint.
    Returns, per request, n dicts {"text", "finish_reason", "completion_tokens"}; `text` holds the raw
    `<think>...</think>` reasoning followed by the answer. A request the server rejects (HTTP 400) yields
    choices with finish_reason "error"; transient errors are retried, then raised.
    `on_result(i, choices)` is called as each request finishes, so callers can save results as they arrive.
    """
    endpoints = [_Endpoint(u, concurrency) for u in base_urls()]
    start = time.monotonic()
    done = 0

    async def run(i, req):
        nonlocal done
        out = await _one(req, endpoints, model)
        if on_result is not None:
            on_result(i, out)
        done += 1
        if done % PROGRESS_EVERY == 0 or done == len(requests):
            print(f"[llm] {done}/{len(requests)} requests done, {time.monotonic() - start:.0f}s", flush=True)
        return out

    return list(await asyncio.gather(*(run(i, r) for i, r in enumerate(requests))))


def split_think(text: str) -> tuple[str | None, str, bool]:
    """Return (reasoning, answer, think_closed). reasoning is None when there is no think block."""
    open_i = text.find("<think>")
    if open_i == -1:
        close_i = text.find("</think>")
        if close_i == -1:
            return None, text.strip(), True
        # The opening tag can live in the prompt template; the output then starts inside the reasoning.
        return text[:close_i].strip(), text[close_i + len("</think>") :].strip(), True
    body = text[open_i + len("<think>") :]
    close_i = body.find("</think>")
    if close_i == -1:
        return body.strip(), "", False
    return body[:close_i].strip(), body[close_i + len("</think>") :].strip(), True


_FENCE = re.compile(r"```([^\n`]*)\n(.*?)(?:```|\Z)", re.DOTALL)
_PY_LANGS = {"", "python", "py", "python3"}


def extract_code(answer: str, entry_point: str | None = None) -> str | None:
    """Last ```python / bare ``` block; with entry_point, prefer the last block defining it."""
    blocks = [
        m.group(2).strip("\n").rstrip()
        for m in _FENCE.finditer(answer)
        if m.group(1).strip().lower() in _PY_LANGS
    ]
    blocks = [b for b in blocks if b.strip()]
    if not blocks:
        return None
    if entry_point:
        pat = re.compile(rf"\bdef\s+{re.escape(entry_point)}\s*\(")
        defining = [b for b in blocks if pat.search(b)]
        if defining:
            return defining[-1]
    return blocks[-1]
