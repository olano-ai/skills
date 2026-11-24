"""area — a single series as a line over a 10%-opacity wash.  Everything else follows ``line``."""
from __future__ import annotations

from . import line

SUPPORTS_ANNOTATIONS = True


def preferred_height(spec, sc, chart_w):
    return chart_w * 0.58


def build(spec, theme) -> dict:
    return line.build_lines(spec, theme, area=True)
