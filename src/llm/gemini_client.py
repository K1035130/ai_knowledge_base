"""Thin Gemini wrapper for the small, cheap LLM tasks in this project: cluster naming, highlight scoring."""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

_client = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _generate_with_retry(model: str, prompt: str, max_retries: int = 3) -> str:
    """Gemini occasionally returns a transient 503 ("high demand") — retry a few times with
    backoff instead of letting one flaky call kill an entire report build that may have already
    spent a minute on embedding/clustering."""
    for attempt in range(max_retries):
        try:
            response = get_client().models.generate_content(model=model, contents=prompt)
            return response.text.strip()
        except genai_errors.ServerError:
            if attempt == max_retries - 1:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("unreachable")  # loop always returns or raises


def label_cluster(keywords: list[str], lang: str = "zh", model: str = "gemini-2.5-flash") -> str:
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


def summarize_highlight(conversation_text: str, lang: str = "zh", model: str = "gemini-2.5-flash") -> str:
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
