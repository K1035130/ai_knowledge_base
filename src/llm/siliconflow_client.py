"""Thin SiliconFlow wrapper for the small, cheap LLM tasks in this project: cluster naming,
highlight scoring, and conversation embedding.

Replaces the previous Gemini client. SiliconFlow speaks the OpenAI-compatible protocol, so the
official `openai` SDK talks to it unchanged as long as `base_url` points at their endpoint --
that also keeps the door open to any other OpenAI-compatible provider by swapping two env vars.
"""

import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

sys.path.append(str(Path(__file__).resolve().parents[2]))
from config import CHAT_MODEL, EMBEDDING_MODEL, SILICONFLOW_BASE_URL  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

_client = None
# Qwen3 emits its chain of thought inside <think>...</think> when thinking mode is on. We turn it
# off per request, but strip the block anyway so a provider-side default can't leak into a label.
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.environ["SILICONFLOW_API_KEY"],
            base_url=os.environ.get("SILICONFLOW_BASE_URL", SILICONFLOW_BASE_URL),
        )
    return _client


def _call_with_retry(fn, max_retries: int = 3):
    """The provider occasionally returns a transient 5xx or drops the connection -- retry a few
    times with backoff instead of letting one flaky call kill an entire report build that may have
    already spent a minute on embedding/clustering. Also retries 429s (rate/quota limit) with a
    longer wait, since RPM/TPM limits reset on a rolling ~60s window rather than clearing in a few
    seconds."""
    for attempt in range(max_retries):
        try:
            return fn()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            time.sleep(30 * (attempt + 1))
        except (InternalServerError, APIConnectionError, APITimeoutError):
            if attempt == max_retries - 1:
                raise
            time.sleep(2**attempt)
        except APIStatusError:
            raise  # 4xx other than 429 (bad key, bad model name, over-long input): retrying won't help
    raise RuntimeError("unreachable")  # loop always returns or raises


def _generate_with_retry(model: str, prompt: str, max_retries: int = 3) -> str:
    response = _call_with_retry(
        lambda: get_client().chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            # SiliconFlow-specific switch for hybrid-reasoning models like Qwen3: these are
            # one-line naming/summary tasks, so thinking only costs tokens and latency.
            extra_body={"enable_thinking": False},
        ),
        max_retries=max_retries,
    )
    return _THINK_BLOCK.sub("", response.choices[0].message.content).strip()


def label_cluster(keywords: list[str], lang: str = "zh", model: str = CHAT_MODEL) -> str:
    if lang == "en":
        prompt = (
            "The following keywords are the representative terms of one topic cluster, produced by "
            "clustering a user's AI conversation history. Give this cluster a short name in 2-4 English "
            "words that points to a concrete topic or domain (e.g. 'Programming', 'Math', 'Biology Research', "
            "'Visa Application') — avoid vague, abstract, or poetic phrasing. If the keywords are too mixed "
            "to point to anything specific, just output 'Other'. Output only the name itself — no quotes, no "
            "explanation, no more than 4 words.\n"
            f"Keywords: { ', '.join(keywords) }"
        )
    else:
        prompt = (
            "以下关键词来自对用户AI对话历史做聚类后，某一个话题簇的代表词。"
            "用2到4个字的中文词语给这个话题簇起一个名字，必须指向具体的事务或领域"
            "（比如「编程」「数学计算」「生物研究」「签证申请」），可以包含有意义的代表词，不要用空洞抽象、文艺化的措辞。"
            "如果关键词杂乱、看不出具体指向什么领域，就直接输出「其他」。"
            "只输出词语本身，不要解释、不要加引号、不要超过4个字。\n"
            f"关键词：{ '、'.join(keywords) }"
        )
    return _generate_with_retry(model, prompt)


def embed_texts(
    texts: list[str],
    model: str = EMBEDDING_MODEL,
    max_retries: int = 3,
) -> list[list[float]]:
    """Batch-embeds texts (one HTTP call per batch, already-batched by the caller).

    Unlike gemini-embedding-001 there is no output_dimensionality knob here: bge-m3 returns a fixed
    1024-d vector, so the caller takes whatever the model's native width is.
    """
    response = _call_with_retry(
        lambda: get_client().embeddings.create(model=model, input=texts),
        max_retries=max_retries,
    )
    # The API is documented to return results in input order, but it also carries an explicit index
    # on each item -- sort by it so a reordered response can never silently mismatch text to vector.
    return [item.embedding for item in sorted(response.data, key=lambda e: e.index)]


def summarize_highlight(conversation_text: str, lang: str = "zh", model: str = CHAT_MODEL) -> str:
    """One-line, narrative-style summary of a single real conversation, for the annual-report highlight reel."""
    if lang == "en":
        prompt = (
            "Below is a real conversation between a user and an AI (user/assistant turns, possibly "
            "truncated). In one sentence (no more than 25 words), summarize what the user did or asked "
            "about in this conversation. Address the user as 'you', in a natural tone like a one-line "
            "callout in an annual usage report. Don't quote the text verbatim, no quotation marks.\n\n"
            f"{conversation_text}"
        )
    else:
        prompt = (
            "以下是用户和AI之间的一段真实对话（user/assistant交替发言，可能被截断）。"
            "用一句话（不超过30个字）总结用户在这段对话里做了什么或问了什么，将用户称为‘你’"
            "语气自然、像年度报告里的一句小故事，不要逐字复述原文，不要加引号。\n\n"
            f"{conversation_text}"
        )
    return _generate_with_retry(model, prompt)
