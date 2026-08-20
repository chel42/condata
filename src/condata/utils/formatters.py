"""Formatage des octets, pourcentages et nombres."""

from __future__ import annotations


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} o"
    units = ["Ko", "Mo", "Go", "To"]
    value = float(size)
    for unit in units:
        value /= 1024.0
        if value < 1024.0:
            return f"{value:.1f} {unit}"
    return f"{value:.1f} Po"


def format_pct(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f} %"


def format_number(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "-"
    if float(value).is_integer() and abs(value) < 1e12:
        return f"{int(value):,}".replace(",", " ")
    return f"{value:,.{digits}f}".replace(",", " ")


def score_level(score: int) -> str:
    if score >= 80:
        return "good"
    if score >= 50:
        return "mid"
    return "bad"
