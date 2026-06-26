"""Time-series EDA over the parsed conversation table: when, how often, how long."""

import pandas as pd


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["weekday"] = df["timestamp"].dt.day_name()
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)
    return df


def conversation_lengths(df: pd.DataFrame) -> pd.Series:
    return df.groupby("conversation_id")["turn"].max() + 1


def activity_by_hour(df: pd.DataFrame) -> pd.Series:
    return df.groupby("hour").size().sort_index()


def activity_by_weekday(df: pd.DataFrame) -> pd.Series:
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return df.groupby("weekday").size().reindex(order)


def monthly_trend(df: pd.DataFrame) -> pd.Series:
    return df.groupby("month").size().sort_index()
