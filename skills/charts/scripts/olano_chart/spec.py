"""Recipe JSON → validated dataclasses.  Every error says what to do instead.

The recipe is deliberately small: categories × series, a story (kicker, title,
subtitle, hero, annotations, notes) and a handful of switches.  Type-specific
inputs (``values`` for a histogram, ``rows``/``columns``/``matrix`` for a heatmap,
``points`` for a scatter) live beside them.  ``references/recipes.md`` documents
every field with an example.
"""
from __future__ import annotations

import difflib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TYPES = ("bar", "column", "stacked_bar", "grouped_bar", "line", "area", "dumbbell", "donut",
         "stat", "histogram", "heatmap", "scatter")
CATEGORY_TYPES = ("bar", "column", "stacked_bar", "grouped_bar", "line", "area", "dumbbell", "donut")
LABEL_MODES = ("auto", "none", "extremes", "ends", "all")
SORTS = ("none", "desc", "asc")
ROLES = ("emphasis", "context")
FORMAT_KINDS = ("number", "currency", "percent")

COMMON_KEYS = {"type", "kicker", "title", "subtitle", "categories", "series", "value_format", "value_axis",
               "category_axis", "labels", "percent_of_total", "sort", "ordinal", "highlight", "annotations",
               "hero", "notes", "theme", "size", "logo", "orientation"}
TYPE_KEYS = {"histogram": {"values", "bins", "x_axis"}, "heatmap": {"rows", "columns", "matrix"},
             "scatter": {"points", "x_axis"}}

CURRENCY_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "¥", "INR": "₹", "KRW": "₩",
                    "BRL": "R$", "CAD": "CA$", "AUD": "A$", "MXN": "MX$", "NZD": "NZ$", "HKD": "HK$",
                    "SGD": "S$", "CHF": "CHF ", "SEK": "kr ", "NOK": "kr ", "DKK": "kr ", "PLN": "zł ",
                    "CZK": "Kč ", "ILS": "₪", "TRY": "₺", "ZAR": "R", "CRC": "₡", "PHP": "₱", "NGN": "₦"}


class SpecError(ValueError):
    """A recipe problem the caller can fix; the message says how."""


def _err(msg: str) -> SpecError:
    return SpecError(msg)


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _num(v: Any, where: str, allow_none: bool = True) -> float | None:
    if v is None:
        if allow_none:
            return None
        raise _err(f"{where} must be a number, not null")
    if not _is_num(v):
        raise _err(f"{where} must be a number (got {json.dumps(v)}); strip units and thousands separators")
    if not math.isfinite(v):
        raise _err(f"{where} must be finite (got {v}); use null for a missing value")
    return float(v)


def _str(v: Any, where: str, required: bool = False) -> str:
    if v is None:
        if required:
            raise _err(f"{where} is required")
        return ""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    if not isinstance(v, str):
        raise _err(f"{where} must be a string")
    if required and not v.strip():
        raise _err(f"{where} must not be empty")
    return v


def _enum(v: Any, where: str, allowed: tuple, default: str) -> str:
    if v is None:
        return default
    s = str(v).strip().lower()
    if s not in allowed:
        raise _err(f"{where} must be one of {', '.join(allowed)} (got '{v}')")
    return s


@dataclass
class ValueFormat:
    kind: str = "number"
    currency: str = "USD"
    decimals: int = 0
    compact: bool = True

    @property
    def symbol(self) -> str:
        if self.kind != "currency":
            return ""
        return CURRENCY_SYMBOLS.get(self.currency.upper(), f"{self.currency.upper()} ")

    def format(self, v: float | None, decimals: int | None = None) -> str:
        """Human label: thousands commas, compact 12.9K / $4.2M, percent with a sign."""
        if v is None:
            return "—"
        d = self.decimals if decimals is None else decimals
        sign = "−" if v < 0 else ""
        a = abs(v)
        if self.kind == "percent":
            return f"{sign}{a:,.{d}f}%"
        body = None
        if self.compact and a >= 1000:
            for div, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
                if a >= div:
                    x = a / div
                    s = f"{x:.1f}" if x < 100 else f"{x:.0f}"
                    if s.endswith(".0"):
                        s = s[:-2]
                    body = s + suffix
                    break
        if body is None:
            body = f"{a:,.{d}f}"
        return f"{sign}{self.symbol}{body}"

    def axis_expr(self) -> str:
        """A Vega ``labelExpr`` that formats axis ticks the same way as :meth:`format`."""
        d = self.decimals
        if self.kind == "percent":
            return f"(datum.value < 0 ? '−' : '') + format(abs(datum.value), ',.{d}~f') + '%'"
        prefix = json.dumps(self.symbol)
        plain = f"format(abs(datum.value), ',.{max(d, 2)}~f')"
        if not self.compact:
            return f"(datum.value < 0 ? '−' : '') + {prefix} + {plain}"
        return (
            f"(datum.value < 0 ? '−' : '') + {prefix} + ("
            f"abs(datum.value) >= 1e12 ? format(abs(datum.value)/1e12, ',.1~f') + 'T' : "
            f"abs(datum.value) >= 1e9 ? format(abs(datum.value)/1e9, ',.1~f') + 'B' : "
            f"abs(datum.value) >= 1e6 ? format(abs(datum.value)/1e6, ',.1~f') + 'M' : "
            f"abs(datum.value) >= 1e3 ? format(abs(datum.value)/1e3, ',.1~f') + 'K' : {plain})"
        )


@dataclass
class Series:
    name: str
    values: list[float | None]
    role: str | None = None

    @property
    def total(self) -> float:
        return sum(v for v in self.values if v is not None)


@dataclass
class AxisSpec:
    label: str = ""
    min: float | None = None
    max: float | None = None


@dataclass
class Annotation:
    target: str
    text: str


@dataclass
class Hero:
    value: str
    label: str = ""
    delta: str = ""


@dataclass
class Notes:
    source: str = ""
    as_of: str = ""
    note: str = ""

    @property
    def source_line(self) -> str:
        parts = []
        if self.source:
            parts.append(f"Source: {self.source}")
        if self.as_of:
            parts.append(f"as of {self.as_of}")
        return " · ".join(parts)


@dataclass
class Point:
    x: float
    y: float
    label: str = ""
    group: str = ""


@dataclass
class ChartSpec:
    type: str
    title: str
    kicker: str = ""
    subtitle: str = ""
    categories: list[str] = field(default_factory=list)
    series: list[Series] = field(default_factory=list)
    value_format: ValueFormat = field(default_factory=ValueFormat)
    value_axis: AxisSpec = field(default_factory=AxisSpec)
    category_axis: AxisSpec = field(default_factory=AxisSpec)
    x_axis: AxisSpec = field(default_factory=AxisSpec)
    labels: str = "auto"
    percent_of_total: bool = False
    sort: str = "desc"
    ordinal: bool = False
    orientation: str = "horizontal"
    highlight: list[str] = field(default_factory=list)
    annotations: list[Annotation] = field(default_factory=list)
    hero: Hero | None = None
    notes: Notes = field(default_factory=Notes)
    theme: str = "clean"
    size: str = "square"
    logo: str = ""
    # type-specific
    values: list[float] = field(default_factory=list)      # histogram
    bins: int = 20                                          # histogram
    rows: list[str] = field(default_factory=list)          # heatmap
    columns: list[str] = field(default_factory=list)       # heatmap
    matrix: list[list[float | None]] = field(default_factory=list)  # heatmap
    points: list[Point] = field(default_factory=list)      # scatter
    raw: dict = field(default_factory=dict)
    layout: Any = None  # set by chart.py before build(): a layout.Layout

    # -- convenience -------------------------------------------------------
    @property
    def n_series(self) -> int:
        return len(self.series)

    @property
    def multi(self) -> bool:
        return len(self.series) > 1

    def emphasis_series(self) -> list[str]:
        return [s.name for s in self.series if s.role == "emphasis"]

    def is_emphasized_category(self, cat: str) -> bool:
        return cat in self.highlight

    def order(self) -> list[int]:
        """Category indices in display order (by value/total unless ordinal or sort none)."""
        n = len(self.categories)
        idx = list(range(n))
        if self.sort == "none" or self.ordinal or not self.series:
            return idx
        emph = self.emphasis_series()
        if self.multi and self.type == "dumbbell":
            key = [self.series[1].values[i] if self.series[1].values[i] is not None else -math.inf for i in idx]
        elif self.multi and emph:
            s = next(s for s in self.series if s.name == emph[0])
            key = [s.values[i] if s.values[i] is not None else -math.inf for i in idx]
        elif self.multi:
            key = [sum((s.values[i] or 0) for s in self.series) for i in idx]
        else:
            key = [self.series[0].values[i] if self.series[0].values[i] is not None else -math.inf for i in idx]
        idx.sort(key=lambda i: key[i], reverse=(self.sort == "desc"))
        return idx

    def share(self, v: float | None) -> str:
        total = sum(s.total for s in self.series)
        if v is None or total <= 0:
            return ""
        return f"{100 * v / total:.0f}%"

    def label_for(self, v: float | None) -> str:
        s = self.value_format.format(v)
        if self.percent_of_total and v is not None:
            s = f"{s} ({self.share(v)})"
        return s


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------
def load_spec(source: str | Path | dict, *, theme: str | None = None, size: str | None = None) -> ChartSpec:
    """Read a recipe (path or dict) and validate it.  CLI ``theme``/``size`` override the file."""
    if isinstance(source, dict):
        raw = source
    else:
        p = Path(source)
        if not p.is_file():
            raise _err(f"recipe file not found: {p}")
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise _err(f"{p} is not valid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(raw, dict):
        raise _err("the recipe must be a JSON object with at least \"type\" and \"title\"")
    spec = parse_spec(raw)
    if theme:
        spec.theme = theme
    if size:
        spec.size = size
    return spec


def parse_spec(raw: dict) -> ChartSpec:
    t = _str(raw.get("type"), "type", required=True).strip().lower()
    if t not in TYPES:
        close = difflib.get_close_matches(t, TYPES, n=1)
        hint = f" — did you mean '{close[0]}'?" if close else ""
        raise _err(f"unknown type '{t}'{hint}. Types: {', '.join(TYPES)}")
    allowed = COMMON_KEYS | TYPE_KEYS.get(t, set())
    unknown = [k for k in raw if k not in allowed]
    if unknown:
        hints = []
        for k in unknown:
            close = difflib.get_close_matches(k, sorted(allowed), n=1)
            hints.append(f"'{k}'" + (f" (did you mean '{close[0]}'?)" if close else ""))
        raise _err(f"unknown field(s) for type '{t}': {', '.join(hints)}. See references/recipes.md")

    title = _str(raw.get("title"), "title", required=True).strip()
    spec = ChartSpec(type=t, title=title, raw=raw)
    spec.kicker = _str(raw.get("kicker"), "kicker").strip()
    spec.subtitle = _str(raw.get("subtitle"), "subtitle").strip()
    spec.theme = _str(raw.get("theme"), "theme") or "clean"
    spec.size = _str(raw.get("size"), "size") or "square"
    spec.logo = _str(raw.get("logo"), "logo")
    spec.labels = _enum(raw.get("labels"), "labels", LABEL_MODES, "auto")
    spec.ordinal = bool(raw.get("ordinal", False))
    spec.percent_of_total = bool(raw.get("percent_of_total", False))
    spec.orientation = _enum(raw.get("orientation"), "orientation", ("horizontal", "vertical"), "horizontal")
    if "orientation" in raw and t not in ("stacked_bar", "grouped_bar"):
        raise _err("orientation applies to stacked_bar and grouped_bar only (use 'bar' for horizontal, 'column' for vertical)")

    # value_format / axes
    vf = raw.get("value_format") or {}
    if not isinstance(vf, dict):
        raise _err("value_format must be an object like {\"kind\": \"currency\", \"currency\": \"USD\", \"decimals\": 0, \"compact\": true}")
    spec.value_format = ValueFormat(
        kind=_enum(vf.get("kind"), "value_format.kind", FORMAT_KINDS, "number"),
        currency=_str(vf.get("currency"), "value_format.currency") or "USD",
        decimals=int(vf.get("decimals", 0) or 0),
        compact=bool(vf.get("compact", True)),
    )
    if not 0 <= spec.value_format.decimals <= 4:
        raise _err("value_format.decimals must be between 0 and 4")
    spec.value_axis = _axis(raw.get("value_axis"), "value_axis")
    spec.category_axis = _axis(raw.get("category_axis"), "category_axis")
    spec.x_axis = _axis(raw.get("x_axis"), "x_axis")

    # story
    notes = raw.get("notes") or {}
    if not isinstance(notes, dict):
        raise _err("notes must be an object: {\"source\": \"…\", \"as_of\": \"YYYY-MM-DD\", \"note\": \"…\"}")
    spec.notes = Notes(_str(notes.get("source"), "notes.source").strip(), _str(notes.get("as_of"), "notes.as_of").strip(),
                       _str(notes.get("note"), "notes.note").strip())
    hero = raw.get("hero")
    if hero is not None:
        if not isinstance(hero, dict) or "value" not in hero:
            raise _err("hero must be an object: {\"value\": \"63\", \"label\": \"customer accounts\"}")
        spec.hero = Hero(_str(hero.get("value"), "hero.value", required=True), _str(hero.get("label"), "hero.label").strip(),
                         _str(hero.get("delta"), "hero.delta").strip())
    if t == "stat" and spec.hero is None:
        raise _err("stat needs a hero: {\"value\": \"$4.2M\", \"label\": \"ARR\"} — the number is the chart")

    # data
    if t == "histogram":
        _parse_histogram(spec, raw)
    elif t == "heatmap":
        _parse_heatmap(spec, raw)
    elif t == "scatter":
        _parse_scatter(spec, raw)
    else:
        _parse_categories(spec, raw, t)

    # sort
    default_sort = "none" if (spec.ordinal or t in ("line", "area", "stat", "heatmap", "histogram", "scatter")) else "desc"
    spec.sort = _enum(raw.get("sort"), "sort", SORTS, default_sort)
    if "sort" in raw and t in ("line", "area") and spec.sort != "none":
        raise _err(f"sort does not apply to {t}: categories are a sequence (dates, steps) and keep their order — remove it")

    # highlight + annotations
    targets = _targets(spec)
    hl = raw.get("highlight") or []
    if isinstance(hl, str):
        hl = [hl]
    if not isinstance(hl, list):
        raise _err("highlight must be a list of category names (or series names for several series)")
    for h in hl:
        h = _str(h, "highlight")
        if h not in targets:
            raise _err(f"highlight '{h}' is not in the chart — targets: {', '.join(list(targets)[:12])}")
    spec.highlight = [_str(h, "highlight") for h in hl]
    ann = raw.get("annotations") or []
    if not isinstance(ann, list):
        raise _err("annotations must be a list of {\"target\": \"<category or series>\", \"text\": \"…\"}")
    for a in ann:
        if not isinstance(a, dict) or "target" not in a or "text" not in a:
            raise _err("each annotation needs \"target\" and \"text\"")
        tgt = _str(a["target"], "annotations.target", required=True)
        if tgt not in targets:
            raise _err(f"annotation target '{tgt}' is not in the chart — targets: {', '.join(list(targets)[:12])}")
        spec.annotations.append(Annotation(tgt, _str(a["text"], "annotations.text", required=True).strip()))
    if len(spec.annotations) > 3:
        raise _err("more than 3 annotations stop reading as emphasis — keep the one or two that carry the story")
    return spec


def _axis(v: Any, where: str) -> AxisSpec:
    if v is None:
        return AxisSpec()
    if not isinstance(v, dict):
        raise _err(f"{where} must be an object like {{\"label\": \"Accounts\", \"min\": 0, \"max\": null}}")
    ax = AxisSpec(_str(v.get("label"), f"{where}.label").strip(), _num(v.get("min"), f"{where}.min"), _num(v.get("max"), f"{where}.max"))
    if ax.min is not None and ax.max is not None and ax.min >= ax.max:
        raise _err(f"{where}.min must be below {where}.max")
    return ax


def _parse_categories(spec: ChartSpec, raw: dict, t: str) -> None:
    cats = raw.get("categories")
    series = raw.get("series")
    if t == "stat" and not series:
        return
    if not isinstance(cats, list) or not cats:
        raise _err(f"{t} needs \"categories\": a list of names (the x positions / rows)")
    spec.categories = [_str(c, "categories[]").strip() for c in cats]
    dup = {c for c in spec.categories if spec.categories.count(c) > 1}
    if dup:
        raise _err(f"duplicate categories: {', '.join(sorted(dup))} — merge them (e.g. 'US' and 'USA') or make the names distinct")
    if not isinstance(series, list) or not series:
        raise _err("series must be a non-empty list: [{\"name\": \"Accounts\", \"values\": [22, 13, 12]}]")
    if len(series) > 8:
        raise _err(f"{len(series)} series cannot be told apart by colour — fold the tail into 'Other' (≤ 8 total) or facet into several charts")
    n = len(spec.categories)
    names: list[str] = []
    for i, s in enumerate(series):
        if not isinstance(s, dict):
            raise _err(f"series[{i}] must be an object with name and values")
        name = _str(s.get("name"), f"series[{i}].name", required=True).strip()
        if name in names:
            raise _err(f"duplicate series name '{name}'")
        names.append(name)
        vals = s.get("values")
        if not isinstance(vals, list):
            raise _err(f"series '{name}' needs \"values\": a list of {n} numbers (null for missing)")
        if len(vals) != n:
            raise _err(f"series '{name}' has {len(vals)} values but there are {n} categories — one value per category, null where missing")
        role = s.get("role")
        if role is not None and role not in ROLES:
            raise _err(f"series '{name}' role must be 'emphasis', 'context' or null")
        spec.series.append(Series(name, [_num(v, f"series '{name}' values[{j}]") for j, v in enumerate(vals)], role))
    if t in ("stacked_bar", "grouped_bar") and len(spec.series) < 2:
        raise _err(f"{t} needs at least 2 series — for one series use 'bar' (or 'column')")
    if t in ("line", "area") and n < 2:
        raise _err(f"{t} needs at least 2 categories (points in the sequence) — for one value use 'stat'")
    if t == "area" and len(spec.series) > 1:
        raise _err("area is for a single series — several series overlap and hide each other; use 'line' (or 'stacked_bar' for part-to-whole)")
    if t == "dumbbell" and len(spec.series) != 2:
        raise _err("dumbbell needs exactly 2 series: before and after (in that order)")
    if t == "donut":
        if len(spec.series) != 1:
            raise _err("donut takes one series (the parts of one whole) — for several series use 'stacked_bar'")
        if n > 6:
            raise _err(f"{n} slices cannot be compared by angle — use 'bar' (sorted, labelled) or fold to ≤ 6 with 'Other'")
        if any((v or 0) < 0 for v in spec.series[0].values):
            raise _err("donut values must be ≥ 0 (parts of a whole)")
    if t == "stat" and len(spec.series) > 1:
        raise _err("stat takes at most one series (a sparkline of the hero number over time)")
    if spec.ordinal and len(spec.series) > 1:
        raise _err("ordinal (one-hue ramp) applies to a single series; with several series the hue carries identity")


def _parse_histogram(spec: ChartSpec, raw: dict) -> None:
    vals = raw.get("values")
    if not isinstance(vals, list) or len(vals) < 2:
        raise _err("histogram needs \"values\": a list of at least 2 numbers (the raw observations, not counts)")
    spec.values = [float(_num(v, f"values[{i}]", allow_none=False)) for i, v in enumerate(vals)]
    bins = raw.get("bins", 20)
    if not isinstance(bins, int) or isinstance(bins, bool) or not 2 <= bins <= 200:
        raise _err("bins must be an integer between 2 and 200 (default 20)")
    spec.bins = bins
    if raw.get("categories") or raw.get("series"):
        raise _err("histogram takes raw \"values\", not categories/series — for pre-counted buckets use 'column' with ordinal: true")


def _parse_heatmap(spec: ChartSpec, raw: dict) -> None:
    rows, cols, matrix = raw.get("rows"), raw.get("columns"), raw.get("matrix")
    if not isinstance(rows, list) or not rows or not isinstance(cols, list) or not cols:
        raise _err("heatmap needs \"rows\" and \"columns\": lists of names")
    spec.rows = [_str(r, "rows[]").strip() for r in rows]
    spec.columns = [_str(c, "columns[]").strip() for c in cols]
    if not isinstance(matrix, list) or len(matrix) != len(spec.rows):
        raise _err(f"matrix must have one list per row ({len(spec.rows)} rows)")
    for i, r in enumerate(matrix):
        if not isinstance(r, list) or len(r) != len(spec.columns):
            raise _err(f"matrix[{i}] must have {len(spec.columns)} values (one per column)")
        spec.matrix.append([_num(v, f"matrix[{i}][{j}]") for j, v in enumerate(r)])
    if len(spec.rows) * len(spec.columns) > 400:
        raise _err("a heatmap past ~400 cells stops being readable — aggregate, or split into several")


def _parse_scatter(spec: ChartSpec, raw: dict) -> None:
    pts = raw.get("points")
    if not isinstance(pts, list) or len(pts) < 2:
        raise _err("scatter needs \"points\": [{\"x\": 1, \"y\": 2, \"label\": \"optional\", \"group\": \"optional\"}, …]")
    for i, p in enumerate(pts):
        if not isinstance(p, dict):
            raise _err(f"points[{i}] must be an object with x and y")
        spec.points.append(Point(_num(p.get("x"), f"points[{i}].x", allow_none=False), _num(p.get("y"), f"points[{i}].y", allow_none=False),
                                 _str(p.get("label"), f"points[{i}].label").strip(), _str(p.get("group"), f"points[{i}].group").strip()))
    groups = sorted({p.group for p in spec.points if p.group})
    if len(groups) > 3:
        raise _err(f"{len(groups)} groups in a scatter: any two dots can sit side by side, and only 3 hues stay distinct under that test — fold to 3 groups or facet")
    labels = [p.label for p in spec.points if p.label]
    if len(labels) != len(set(labels)):
        raise _err("point labels must be unique (they are the annotation and highlight targets)")


def _targets(spec: ChartSpec) -> list[str]:
    if spec.type == "scatter":
        return [p.label for p in spec.points if p.label] + sorted({p.group for p in spec.points if p.group})
    if spec.type == "heatmap":
        return spec.rows + spec.columns
    if spec.type == "histogram":
        return []
    return spec.categories + [s.name for s in spec.series]
