"""Theme loading: ``assets/themes/*.json``, the ``brand`` theme from ``brand/tokens.json``,
the Vega-Lite ``config`` block and the CSS tokens the frame writes.

A theme is data: colour tokens (every one of them validated by
``palette.check_theme``), font roles, and a few frame knobs.  ``brand`` is not a
file — it is ``clean`` or ``midnight`` with the brand kit's values swapped in
*only where they pass*; anything that fails stays on the base value and is
reported on stderr, because a chart in an unreadable brand colour is worse than a
chart in the default blue.
"""
from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import palette
from .fonts import FontSet, build_fontset, resolve_font_file

THEMES_DIR = Path(__file__).resolve().parents[2] / "assets" / "themes"
BUILTIN = ("clean", "midnight", "editorial")
ALL_THEME_NAMES = BUILTIN + ("brand",)


@dataclass
class Theme:
    name: str
    mode: str
    label: str
    tokens: dict
    fonts: dict
    frame: dict
    vegalite: dict = field(default_factory=dict)
    fontset: FontSet | None = None
    notes: list[str] = field(default_factory=list)  # brand-override decisions worth telling the user

    # -- fonts -------------------------------------------------------------
    def font(self, role: str) -> dict:
        """Font role dict (``family``/``weight``/``style``/``generic``), falling back to body."""
        return self.fonts.get(role) or self.fonts["body"]

    def family(self, role: str) -> str:
        return self.font(role).get("family", "")

    def stack(self, role: str) -> str:
        assert self.fontset is not None
        return self.fontset.css_stack(role if role in self.fonts else "body")

    def weight(self, role: str) -> int:
        return int(self.font(role).get("weight", 400))

    def style(self, role: str) -> str:
        return self.font(role).get("style", "normal")

    def generic_by_family(self) -> dict[str, str]:
        return {f.get("family", ""): f.get("generic", "sans") for f in self.fonts.values()}

    # -- colours -----------------------------------------------------------
    @property
    def t(self) -> dict:
        return self.tokens

    def series_colors(self, n: int) -> list[str]:
        if n > 8:
            raise ValueError("more than 8 series cannot be told apart — fold the tail into 'Other' or facet")
        return list(self.tokens["categorical"][:n])

    def context_colors(self, n: int) -> list[str]:
        ramp = self.tokens.get("deemphasis_ramp") or [self.tokens["deemphasis"]]
        return [ramp[i % len(ramp)] for i in range(n)]

    # -- Vega-Lite config --------------------------------------------------
    def vega_config(self, scale) -> dict:
        """The ``config`` block for one card size (fonts sizes come from the type scale)."""
        t = self.tokens
        body = self.stack("body")
        numeric = self.stack("numeric")
        legend_symbol = max(64, round((scale.legend * 0.62) ** 2))
        cfg = {
            "background": t["surface"],
            "font": body,
            "padding": 0,
            "view": {"stroke": None, "fill": None},
            "axis": {
                "domain": False, "ticks": False, "grid": False,
                "gridColor": t["grid"], "gridWidth": 1, "gridDash": [],
                "domainColor": t["baseline"], "domainWidth": 1,
                "tickColor": t["grid"],
                "labelColor": t["muted"], "labelFont": body, "labelFontSize": scale.tick,
                "labelPadding": round(scale.tick * 0.55), "labelOverlap": True,
                "labelLimit": scale.tick * 18,
                "titleColor": t["secondary"], "titleFont": body, "titleFontSize": scale.tick,
                "titleFontWeight": 400, "titlePadding": round(scale.tick * 0.9),
            },
            "legend": {
                "orient": "top", "direction": "horizontal", "title": None,
                "labelColor": t["secondary"], "labelFont": body, "labelFontSize": scale.legend,
                "labelOffset": round(scale.legend * 0.45), "labelLimit": scale.legend * 16,
                "symbolType": "circle", "symbolSize": legend_symbol, "symbolStrokeWidth": 0,
                "columnPadding": round(scale.legend * 1.3), "rowPadding": round(scale.legend * 0.45),
                "offset": round(scale.legend * 1.0), "padding": 0,
                "gradientLength": round(scale.legend * 14), "gradientThickness": round(scale.legend * 0.6),
                "gradientLabelOffset": round(scale.legend * 0.4),
                "titleColor": t["secondary"], "titleFont": body, "titleFontSize": scale.legend,
                "titleFontWeight": 400, "titlePadding": round(scale.legend * 0.5), "titleLimit": scale.legend * 30,
            },
            "bar": {"cornerRadiusEnd": 4},
            "line": {"strokeWidth": 2, "strokeJoin": "round", "strokeCap": "round"},
            "point": {"filled": True, "stroke": t["surface"], "strokeWidth": 2},
            "arc": {"stroke": t["surface"], "strokeWidth": 2},
            "rect": {"stroke": t["surface"], "strokeWidth": 2},
            "text": {"font": numeric, "fontSize": scale.label, "color": t["ink"]},
            "range": {
                "category": list(t["categorical"]),
                "ordinal": list(t.get("ordinal", [])),
                "ramp": list(t.get("sequential", [])),
                "heatmap": list(t.get("sequential", [])),
            },
        }
        return deep_merge(cfg, self.vegalite or {})

    def css_tokens(self) -> str:
        t = self.tokens
        lines = [f"--{k.replace('_', '-')}: {v};" for k, v in t.items() if isinstance(v, str) and not k.startswith("_")]
        lines.append(f"--font-display: {self.stack('display')};")
        lines.append(f"--font-body: {self.stack('body')};")
        lines.append(f"--font-numeric: {self.stack('numeric')};")
        lines.append(f"--font-annotation: {self.stack('annotation')};")
        return "\n  ".join(lines)


def deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _from_dict(d: dict) -> Theme:
    theme = Theme(
        name=d["name"], mode=d["mode"], label=d.get("label", ""), tokens=dict(d["tokens"]),
        fonts=copy.deepcopy(d["fonts"]), frame=dict(d.get("frame", {})), vegalite=copy.deepcopy(d.get("vegalite", {})),
    )
    theme.fontset = build_fontset(theme.fonts)
    return theme


def load_builtin(name: str) -> Theme:
    path = THEMES_DIR / f"{name}.json"
    if not path.is_file():
        raise ValueError(f"unknown theme '{name}' — choose one of {', '.join(ALL_THEME_NAMES)}")
    return _from_dict(json.loads(path.read_text(encoding="utf-8")))


def load_theme(name: str, cwd: Path | None = None) -> Theme:
    """``clean`` / ``midnight`` / ``editorial`` / ``brand`` (``brand:dark`` forces the dark block)."""
    name = (name or "clean").strip().lower()
    if name.startswith("brand"):
        want = "dark" if name.endswith(("dark", ":dark", "-dark")) else ("light" if name.endswith(("light", ":light", "-light")) else None)
        return load_brand(cwd or Path.cwd(), want)
    return load_builtin(name)


# ---------------------------------------------------------------------------
# brand/tokens.json  (schema: the brand-kit skill's tokens-schema.md)
# ---------------------------------------------------------------------------
def load_brand(cwd: Path, want_mode: str | None = None) -> Theme:
    path = cwd / "brand" / "tokens.json"
    if not path.is_file():
        raise ValueError(
            f"theme 'brand' needs {path} (the brand-kit skill writes it: palette.light|dark, typography.display|body). "
            "Run with --theme clean or midnight, or create the brand kit first."
        )
    try:
        kit = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc
    pal = kit.get("palette") or {}
    mode = want_mode or ("light" if pal.get("light") else "dark" if pal.get("dark") else "light")
    block = pal.get(mode) or {}
    base = load_builtin("clean" if mode == "light" else "midnight")
    theme = _from_dict({
        "name": f"brand-{mode}", "mode": mode, "label": f"Brand kit ({kit.get('brand', 'brand')}, {mode}) over {base.name}",
        "tokens": base.tokens, "fonts": base.fonts, "frame": base.frame, "vegalite": base.vegalite,
    })
    notes = theme.notes

    def hexval(key: str) -> str | None:
        v = block.get(key)
        if not v:
            return None
        try:
            return palette.norm_hex(v)
        except ValueError:
            notes.append(f"brand palette.{mode}.{key}='{v}' is not #rrggbb — ignored")
            return None

    surface = hexval("background")
    text = hexval("text")
    muted = hexval("muted")
    accent = hexval("accent")

    # Surfaces + text only travel together and only when text clears 4.5:1.
    if surface and text:
        if palette.text_ok(text, surface):
            theme.tokens["surface"] = surface
            theme.tokens["ink"] = text
            theme.tokens["secondary"] = palette.mix(text, surface, 0.28) if palette.text_ok(palette.mix(text, surface, 0.28), surface) else text
            theme.tokens["grid"] = palette.mix(surface, text, 0.10)
            theme.tokens["baseline"] = palette.mix(surface, text, 0.22)
            theme.tokens["rule"] = theme.tokens["grid"]
            theme.tokens["deemphasis"] = palette.mix(surface, text, 0.20)
            theme.tokens["deemphasis_ramp"] = [palette.mix(surface, text, f) for f in (0.20, 0.30, 0.40)]
            if muted and palette.text_ok(muted, surface, large=True):
                theme.tokens["muted"] = muted
            else:
                theme.tokens["muted"] = palette.mix(text, surface, 0.45)
                if muted:
                    notes.append(f"brand muted {muted} is below 3:1 on {surface} — using a derived gray instead")
        else:
            notes.append(
                f"brand text {text} on background {surface} is {palette.contrast(text, surface):.2f}:1 (< 4.5:1) — "
                f"keeping {base.name}'s surface and ink"
            )
    elif surface or text:
        notes.append("brand palette needs both 'background' and 'text' to override the surface — keeping the base surface")

    # Accent -> slot 1 + emphasis, only if it passes on its own AND a passing order exists around it.
    if accent:
        ok, reasons = palette.check_single(accent, mode, theme.tokens["surface"])
        if not ok:
            notes.append(f"brand accent {accent} fails as a chart colour ({'; '.join(reasons)}) — keeping the default slot-1 hue")
        else:
            rest = [c for c in theme.tokens["categorical"] if c != accent]
            order = palette.best_order(accent, rest[:7], mode, theme.tokens["surface"])
            if order is None:
                notes.append(f"brand accent {accent} passes alone but no 8-slot order around it passes the CVD gates — used for emphasis only")
                theme.tokens["emphasis"] = accent
            else:
                theme.tokens["categorical"] = order
                theme.tokens["emphasis"] = accent
                theme.tokens["ordinal"] = _ordinal_from(accent, mode, theme.tokens["surface"])
                theme.tokens["sequential"] = _sequential_from(accent, mode, theme.tokens["surface"])
                theme.tokens["diverging"] = {**theme.tokens.get("diverging", {}), "positive": accent}

    # Fonts: only when the file exists on this box.
    typo = kit.get("typography") or {}
    for role, target_roles in (("display", ("display",)), ("body", ("body", "annotation", "numeric"))):
        spec = typo.get(role) or {}
        fam, file = spec.get("family"), spec.get("file")
        if not fam:
            continue
        path_ = resolve_font_file(file) if file else None
        if path_ is None:
            notes.append(f"brand {role} font '{fam}' has no readable file ({file or 'none given'}) — keeping {base.family(role)}")
            continue
        weight = int(spec.get("weight", 700 if role == "display" else 400))
        generic = "serif" if "serif" in fam.lower() and "sans" not in fam.lower() else ("mono" if "mono" in fam.lower() else "sans")
        for r in target_roles:
            theme.fonts[r] = {"family": fam, "generic": generic, "weight": weight if r != "annotation" else 400,
                              "style": "italic" if r == "annotation" else "normal",
                              "faces": [{"file": str(path_), "weight": weight}]}
        if role == "body":
            theme.fonts["annotation"]["style"] = "normal"  # a single brand file has no italic face
    theme.fontset = build_fontset(theme.fonts)
    theme.tokens.pop("_categorical_note", None)
    theme.tokens.pop("_emphasis_note", None)
    theme.tokens["_brand_source"] = str(path)
    return theme


def _sequential_from(accent: str, mode: str, surface: str) -> list[str]:
    tints = [palette.mix(surface, accent, f) for f in (0.12, 0.28, 0.48, 0.70)]
    shades = [accent, palette.mix(accent, "#000000" if mode == "light" else "#ffffff", 0.25), palette.mix(accent, "#000000" if mode == "light" else "#ffffff", 0.45)]
    return tints + shades


def _ordinal_from(accent: str, mode: str, surface: str) -> list[str]:
    dark_end = palette.mix(accent, "#000000" if mode == "light" else "#ffffff", 0.35)
    steps = [palette.mix(surface, accent, 0.42), palette.mix(surface, accent, 0.68), accent, palette.mix(accent, dark_end, 0.5), dark_end]
    if mode == "dark":
        steps = steps[::-1]
    _, ok = palette.validate_ordinal(steps, mode, surface)
    return steps if ok else [accent] * 5


def report_notes(theme: Theme) -> None:
    for n in theme.notes:
        print(f"note: {n}", file=sys.stderr)


def themes_summary() -> str:
    out = []
    for name in BUILTIN:
        th = load_builtin(name)
        out.append(f"{th.name}  ({th.mode})  — {th.label}")
        for k, v in th.tokens.items():
            if k.startswith("_"):
                continue
            out.append(f"  {k:18} {json.dumps(v) if not isinstance(v, str) else v}")
        for role, f in th.fonts.items():
            out.append(f"  font.{role:12} {f.get('family')} {f.get('weight', 400)} {f.get('style', 'normal')}")
        out.append("")
    return "\n".join(out)
