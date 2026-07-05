"""Time-series EDA over the parsed conversation table: when, how often, how long."""

import pandas as pd
import tiktoken
from langdetect import LangDetectException, detect

_TOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")


def add_time_features(df: pd.DataFrame, timezone: str = "UTC") -> pd.DataFrame:
    df = df.copy()
    ts = df["timestamp"].dt.tz_localize("UTC").dt.tz_convert(timezone)
    df["timestamp"] = ts
    df["date"] = ts.dt.date
    df["hour"] = ts.dt.hour
    df["weekday"] = ts.dt.day_name()
    df["month"] = ts.dt.strftime("%Y-%m")
    return df


def conversation_lengths(df: pd.DataFrame) -> pd.Series:
    return df.groupby("conversation_id")["turn"].max() + 1


def activity_by_hour(df: pd.DataFrame) -> pd.Series:
    return df.groupby("hour").size().reindex(range(24), fill_value=0)


def activity_by_weekday(df: pd.DataFrame) -> pd.Series:
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return df.groupby("weekday").size().reindex(order, fill_value=0)


def monthly_trend(df: pd.DataFrame) -> pd.Series:
    return df.groupby("month").size().sort_index()


def clean_timestamps(df: pd.DataFrame, isolation_gap: pd.Timedelta = pd.Timedelta(days=1)) -> pd.DataFrame:
    """Drop messages whose `create_time` is wildly inconsistent with their position in the
    conversation (ChatGPT preserves a message's original edit time even though the conversation
    continued normally around it). Must sort by `turn`, not timestamp value — sorting by value
    pushes the outlier to a sequence boundary where it only has one neighbor, which defeats a
    "far from both neighbors" check.
    """

    def _flag(group: pd.DataFrame) -> pd.Series:
        g = group.sort_values("turn")
        ts = g["timestamp"]
        if len(ts) < 3:
            return pd.Series(False, index=g.index)
        prev_gap = ts.diff()
        next_gap = ts.diff(-1).abs()
        isolated = (prev_gap.abs() > isolation_gap) & (next_gap > isolation_gap)
        return isolated.reindex(g.index)

    is_outlier = df.groupby("conversation_id", group_keys=False).apply(_flag, include_groups=False)
    return df[~is_outlier.reindex(df.index, fill_value=False)].copy()


def thread_span(df: pd.DataFrame) -> pd.Series:
    """First-to-last message gap per conversation_id. Can span days since ChatGPT lets users
    return to old threads — distinct from session_duration (one actual sitting)."""
    return df.groupby("conversation_id")["timestamp"].agg(lambda x: x.max() - x.min())


def session_duration(df: pd.DataFrame, gap: pd.Timedelta = pd.Timedelta(minutes=30)) -> pd.Series:
    """Split each conversation into sessions wherever the inter-message gap exceeds `gap`,
    then return the duration of each session (one actual sitting)."""
    df_sorted = df.sort_values(["conversation_id", "timestamp"]).reset_index(drop=True)
    time_gap = df_sorted.groupby("conversation_id")["timestamp"].diff()
    new_session = time_gap.isna() | (time_gap > gap)
    df_sorted["session_id"] = (
        df_sorted["conversation_id"].astype(str)
        + "_"
        + new_session.groupby(df_sorted["conversation_id"]).cumsum().astype(str)
    )
    return df_sorted.groupby("session_id")["timestamp"].agg(lambda x: x.max() - x.min())


def response_times(df: pd.DataFrame) -> pd.Series:
    """Gap between each user message and the next assistant message, sorted by real timestamp
    (not `turn`, which isn't always a reliable chronological key at full data scale)."""
    df_sorted = df.sort_values(["conversation_id", "timestamp"]).reset_index(drop=True)
    df_sorted["next_role"] = df_sorted.groupby("conversation_id")["role"].shift(-1)
    df_sorted["next_timestamp"] = df_sorted.groupby("conversation_id")["timestamp"].shift(-1)
    rt = df_sorted[(df_sorted["role"] == "user") & (df_sorted["next_role"] == "assistant")]
    rt = rt["next_timestamp"] - rt["timestamp"]
    return rt[rt >= pd.Timedelta(0)]


def _safe_detect_lang(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


def language_ratio(df: pd.DataFrame) -> pd.Series:
    """zh-cn/en/other breakdown. Only those two get their own bucket because langdetect produces
    long-tail noise (ko/vi/ca/etc at <5% each) on short strings — that noise shouldn't be
    presented as real language diversity."""
    langs = df["text"].apply(_safe_detect_lang)
    bucketed = langs.map(lambda lang: lang if lang in ("zh-cn", "en") else "other")
    return bucketed.value_counts(normalize=True)


def token_estimate(df: pd.DataFrame) -> pd.DataFrame:
    """Approximate token counts via the GPT-3.5/4 tokenizer — ChatGPT exports carry no real
    token/usage data at all, so this is a labeled estimate, not ground truth."""
    df = df.copy()
    df["token_estimate"] = df["text"].apply(lambda t: len(_TOKEN_ENCODING.encode(t)))
    return df


def rewrite_rate_stats(df: pd.DataFrame, top_n: int = 5) -> dict:
    """Summarize edit/regenerate behavior from the parser's `edit_count` column (abandoned
    sibling-branch count per message — no LLM needed)."""
    edited = df[df["edit_count"] > 0]
    user_edits = edited[edited["role"] == "user"]
    assistant_regens = edited[edited["role"] == "assistant"]
    most_edited = df.sort_values("edit_count", ascending=False).head(top_n)
    return {
        "total_conversations": int(df["conversation_id"].nunique()),
        "conversations_with_edits": int(edited["conversation_id"].nunique()),
        "user_edit_turns": int(len(user_edits)),
        "user_abandoned_versions": int(user_edits["edit_count"].sum()),
        "assistant_regen_turns": int(len(assistant_regens)),
        "assistant_abandoned_versions": int(assistant_regens["edit_count"].sum()),
        "most_edited": most_edited[["conversation_id", "role", "edit_count", "text"]].to_dict("records"),
    }
