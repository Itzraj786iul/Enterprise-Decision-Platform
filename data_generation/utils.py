"""Shared utilities for synthetic data generation."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Iterator, Sequence

import numpy as np
import pandas as pd

from . import config


def ensure_dirs() -> None:
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)


def csv_path(table_name: str) -> Path:
    return config.OUTPUT_DIR / f"{table_name}.csv"


def write_csv(df: pd.DataFrame, table_name: str, mode: str = "w") -> Path:
    """Write a dataframe to data/generated/<table>.csv."""
    ensure_dirs()
    path = csv_path(table_name)
    header = mode == "w"
    df.to_csv(path, index=False, mode=mode, header=header)
    return path


def append_csv(df: pd.DataFrame, table_name: str) -> Path:
    path = csv_path(table_name)
    if path.exists():
        return write_csv(df, table_name, mode="a")
    return write_csv(df, table_name, mode="w")


def save_state(name: str, payload: dict) -> None:
    ensure_dirs()
    path = config.STATE_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def load_state(name: str) -> dict:
    path = config.STATE_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(table_name: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(csv_path(table_name), **kwargs)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def daterange(start: date, end: date) -> Iterator[date]:
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def date_to_id(d: date) -> int:
    return int(d.strftime("%Y%m%d"))


def season_name(d: date) -> str:
    """Retail season labels used for demand shaping."""
    md = (d.month, d.day)
    if md >= (11, 1) or md <= (1, 15):
        return "Holiday"
    if d.month in (2, 3):
        return "WinterClearance"
    if d.month in (4, 5):
        return "Spring"
    if d.month in (6, 7, 8):
        return "Summer"
    if d.month in (9, 10):
        return "BackToSchool"
    return "Regular"


def seasonal_multiplier(d: date, rng: np.random.Generator) -> float:
    """
    Demand multiplier with weekly seasonality + retail peaks.
    Noise keeps day-to-day realism without breaking trends.
    """
    base = {
        "Holiday": 1.55,
        "BackToSchool": 1.20,
        "Summer": 1.10,
        "Spring": 1.05,
        "WinterClearance": 0.95,
        "Regular": 1.00,
    }[season_name(d)]

    # Weekend lift
    if d.weekday() >= 5:
        base *= 1.18
    elif d.weekday() == 4:  # Friday
        base *= 1.08

    # Black Friday week / Christmas week style spikes
    if d.month == 11 and d.day >= 20:
        base *= 1.35
    if d.month == 12 and 15 <= d.day <= 24:
        base *= 1.40

    return float(base * rng.uniform(0.92, 1.08))


def zipf_weights(n: int, alpha: float = 1.15) -> np.ndarray:
    """Long-tail popularity weights (Zipf-like), normalized to sum=1."""
    ranks = np.arange(1, n + 1, dtype=np.float64)
    w = 1.0 / np.power(ranks, alpha)
    w /= w.sum()
    return w


def choice_ids(
    ids: Sequence[int],
    size: int,
    rng: np.random.Generator,
    weights: np.ndarray | None = None,
) -> np.ndarray:
    ids_arr = np.asarray(ids)
    if weights is None:
        return rng.choice(ids_arr, size=size, replace=True)
    return rng.choice(ids_arr, size=size, replace=True, p=weights)


def weighted_category(mapping: dict[str, float], rng: np.random.Generator, size: int = 1):
    keys = list(mapping.keys())
    probs = np.array(list(mapping.values()), dtype=float)
    probs /= probs.sum()
    return rng.choice(keys, size=size, p=probs)


def chunked_range(n: int, chunk_size: int) -> Iterable[tuple[int, int]]:
    start = 0
    while start < n:
        end = min(start + chunk_size, n)
        yield start, end
        start = end


def make_rng(seed: int | None = None) -> np.random.Generator:
    return np.random.default_rng(seed if seed is not None else config.RANDOM_SEED)


def ts_on_date(d: date, rng: np.random.Generator) -> datetime:
    """Random timestamp on a given date with business-hour bias."""
    # Bias toward 10am-8pm
    hour = int(rng.choice(np.arange(8, 22), p=_hour_probs()))
    minute = int(rng.integers(0, 60))
    second = int(rng.integers(0, 60))
    return datetime(d.year, d.month, d.day, hour, minute, second)


def _hour_probs() -> np.ndarray:
    hours = np.arange(8, 22)
    # Peaks around lunch and evening
    raw = np.array([0.6, 0.7, 0.9, 1.1, 1.3, 1.2, 1.0, 0.9, 1.1, 1.4, 1.5, 1.3, 1.0, 0.7])
    raw = raw / raw.sum()
    return raw


def progress(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)
