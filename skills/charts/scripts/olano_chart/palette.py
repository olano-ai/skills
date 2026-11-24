"""The palette math, shared with the standalone validator.

Everything measurable lives in ``scripts/validate_palette.py`` (Olano's own
checker: the OKLCH lightness band, the chroma floor, colour-blind simulation
with OKLab distance, the normal-vision floor and WCAG contrast).  This module
loads that file by path and re-exports its functions, then adds what a *theme*
needs on top: single-colour checks for an emphasis accent, text-contrast gates,
ramp stepping, and a whole theme report so ``selftest.py`` can prove every
shipped theme passes.
"""
from __future__ import annotations

import importlib.util
import itertools
import math
from pathlib import Path

_VALIDATOR = Path(__file__).resolve().parents[1] / "validate_palette.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("olano_validate_palette", _VALIDATOR)
    if spec is None or spec.loader is None:  # pragma: no cover - the file ships with the skill
        raise ImportError(f"palette validator missing at {_VALIDATOR}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vp = _load_validator()

# Re-exports — one implementation of the math, never a second copy.
validate = vp.validate
validate_ordinal = vp.validate_ordinal
contrast = vp.contrast
oklch = vp.oklch
deltaE = vp.deltaE
relative_luminance = vp.relative_luminance
lin2oklab = vp.lin2oklab
lin = vp.lin
hex2srgb = vp.hex2srgb
lin2s = vp.lin2s
is_hex_color = vp.is_hex_color
BAND = vp.BAND
CHROMA_FLOOR = vp.CHROMA_FLOOR
CVD_TARGET = vp.CVD_TARGET
CVD_FLOOR = vp.CVD_FLOOR
NORMAL_FLOOR = vp.NORMAL_FLOOR
CONTRAST_MIN = vp.CONTRAST_MIN

TEXT_CONTRAST_MIN = 4.5   # body/ink text on the surface
LARGE_TEXT_CONTRAST_MIN = 3.0  # muted/large text on the surface
DEEMPHASIS_MIN = 1.35     # a de-emphasis gray must still be visible against the surface


def norm_hex(value: str) -> str:
    """``#RRGGBB`` lower-case, or raise ``ValueError`` with the offending value."""
    v = (value or "").strip()
    if not is_hex_color(v):
        raise ValueError(f"'{value}' is not a #rrggbb colour")
    return "#" + v.lstrip("#").lower()


def check_single(color: str, mode: str, surface: str) -> tuple[bool, list[str]]:
    """Band + chroma + contrast for one colour (what an emphasis accent must clear)."""
    lo, hi = BAND[mode]
    L, C = oklch(color)
    cr = contrast(color, surface)
    reasons = []
    if not (lo <= L <= hi):
        reasons.append(f"lightness L={L:.3f} outside the {mode} band {lo}–{hi}")
    if C < CHROMA_FLOOR:
        reasons.append(f"chroma C={C:.3f} below the {CHROMA_FLOOR} floor (reads as gray)")
    if cr < CONTRAST_MIN:
        reasons.append(f"contrast {cr:.2f}:1 against {surface} below {CONTRAST_MIN:g}:1")
    return (not reasons), reasons


def text_ok(text: str, surface: str, large: bool = False) -> bool:
    return contrast(text, surface) >= (LARGE_TEXT_CONTRAST_MIN if large else TEXT_CONTRAST_MIN)


def label_ink(fill: str, ink: str, light: str = "#ffffff") -> str:
    """Ink for a label *inside* a filled mark: whichever of ink/white clears the fill better."""
    return ink if contrast(ink, fill) >= contrast(light, fill) else light


def hue_deg(color: str) -> float:
    _, a, b = lin2oklab(*lin(color))
    return math.degrees(math.atan2(b, a)) % 360


def mix(c1: str, c2: str, t: float) -> str:
    """sRGB-linear interpolation between two hex colours (what Vega's ``rgb`` interpolate does, roughly)."""
    a, b = hex2srgb(c1), hex2srgb(c2)
    out = tuple(lin2s(vp.s2lin(x) * (1 - t) + vp.s2lin(y) * t) for x, y in zip(a, b))
    return "#%02x%02x%02x" % tuple(int(round(v * 255)) for v in out)


def ramp_color(ramp: list[str], t: float) -> str:
    """Colour at position ``t`` (0..1) along a multi-stop ramp, piecewise sRGB-linear."""
    if not ramp:
        return "#000000"
    if len(ramp) == 1 or t <= 0:
        return ramp[0]
    if t >= 1:
        return ramp[-1]
    seg = t * (len(ramp) - 1)
    i = min(int(seg), len(ramp) - 2)
    return mix(ramp[i], ramp[i + 1], seg - i)


def steps(ramp: list[str], n: int) -> list[str]:
    """``n`` evenly spaced entries from ``ramp`` (ends included)."""
    if n <= 0:
        return []
    if n == 1:
        return [ramp[-1]]
    if n >= len(ramp):
        return list(ramp)[:n] if n == len(ramp) else [ramp_color(ramp, i / (n - 1)) for i in range(n)]
    return [ramp[round(i * (len(ramp) - 1) / (n - 1))] for i in range(n)]


def best_order(first: str, rest: list[str], mode: str, surface: str) -> list[str] | None:
    """Best passing categorical order that keeps ``first`` in slot 1 (for brand accents).

    Scores every arrangement of ``rest`` by its worst adjacent pair (min of the
    CVD ΔE and half the normal-vision ΔE) using precomputed pair distances, then
    confirms the winner with the full validator.  ``None`` when nothing passes.
    """
    colors = [first] + list(rest)
    n = len(colors)
    cvd = [[0.0] * n for _ in range(n)]
    nor = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                cvd[i][j] = min(deltaE(colors[i], colors[j], "protan"), deltaE(colors[i], colors[j], "deutan"))
                nor[i][j] = deltaE(colors[i], colors[j])
    best_score, best_perm = -1.0, None
    for perm in itertools.permutations(range(1, n)):
        order = (0,) + perm
        worst = min(min(cvd[a][b], nor[a][b] / 2.0) for a, b in zip(order, order[1:]))
        if worst > best_score:
            best_score, best_perm = worst, order
    if best_perm is None:
        return None
    candidate = [colors[i] for i in best_perm]
    _, ok = validate(candidate, mode, surface)
    return candidate if ok else None


def check_theme(tokens: dict, mode: str) -> list[tuple[str, bool, str]]:
    """Every gate a shipped theme must clear.  Returns ``(check, passed, detail)`` rows."""
    surface = tokens["surface"]
    rows: list[tuple[str, bool, str]] = []
    rep, ok = validate(tokens["categorical"], mode, surface)
    for name, state, detail in rep:
        passed = state in (True, "pass", "floor", "relief")
        rows.append((f"categorical · {name}", passed, f"{state if isinstance(state, str) else ('pass' if state else 'fail')} — {detail}"))
    rows.append(("categorical · verdict", ok, "validator exit 0" if ok else "validator exit 1"))
    e_ok, reasons = check_single(tokens["emphasis"], mode, surface)
    rows.append(("emphasis · band+chroma+contrast", e_ok, tokens["emphasis"] + ("" if e_ok else ": " + "; ".join(reasons))))
    if tokens.get("ordinal"):
        orep, ook = validate_ordinal(tokens["ordinal"], mode, surface)
        rows.append(("ordinal ramp", ook, "; ".join(f"{n}: {d}" for n, _, d in orep)))
    for role, floor in (("ink", TEXT_CONTRAST_MIN), ("secondary", TEXT_CONTRAST_MIN), ("muted", LARGE_TEXT_CONTRAST_MIN)):
        cr = contrast(tokens[role], surface)
        rows.append((f"text · {role} vs surface", cr >= floor, f"{tokens[role]} {cr:.2f}:1 (floor {floor:g}:1)"))
    cr = contrast(tokens["deemphasis"], surface)
    rows.append(("de-emphasis visible", cr >= DEEMPHASIS_MIN, f"{tokens['deemphasis']} {cr:.2f}:1 (floor {DEEMPHASIS_MIN:g}:1)"))
    if tokens.get("sequential"):
        Ls = [oklch(c)[0] for c in tokens["sequential"]]
        mono = all(b < a for a, b in zip(Ls, Ls[1:])) or all(b > a for a, b in zip(Ls, Ls[1:]))
        rows.append(("sequential ramp monotone", mono, "L " + " → ".join(f"{L:.2f}" for L in Ls)))
    return rows


def format_rows(rows: list[tuple[str, bool, str]]) -> str:
    return "\n".join(f"  [{'PASS' if ok else 'FAIL'}] {name:34} {detail}" for name, ok, detail in rows)
