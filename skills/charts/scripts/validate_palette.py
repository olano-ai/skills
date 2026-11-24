#!/usr/bin/env python3
"""Check a categorical (or ordinal) chart palette before it ships.

Olano's own palette checker for the ``charts`` skill. Standard library only, so
it runs anywhere the skill does. The colour science comes from public sources:

* sRGB transfer function and relative luminance, WCAG 2.x contrast ratio
  (https://www.w3.org/TR/WCAG21/#dfn-contrast-ratio);
* OKLab / OKLCH, Björn Ottosson, 2020 (https://bottosson.github.io/posts/oklab/);
* colour-vision-deficiency simulation with the severity-1.0 matrices published
  in Machado, Oliveira & Fernandes, "A Physiologically-based Model for
  Simulation of Color Vision Deficiency", IEEE TVCG 15(6), 2009.

Categorical checks, each reported as one row:

1. lightness: every colour's OKLCH L sits inside the mode's band, so no series
   vanishes into the surface or shouts over the others;
2. chroma: every colour is saturated enough to read as a colour, not a gray;
3. contrast: every colour clears WCAG 3:1 against the surface (non-text
   graphics). A colour between ``CONTRAST_RELIEF`` and 3:1 is reported as
   ``relief``: usable only when the marks also carry a non-colour cue (direct
   labels, an outline or a pattern), which is how pale ambers and pinks earn a
   place on a near-white surface. Below ``CONTRAST_RELIEF`` it fails;
4. separation: the closest pair on the pair list is far enough apart in OKLab
   for normal vision;
5. colour-blind separation: the same pairs, simulated for protanopia and
   deuteranopia, stay apart (target, or a lower floor reported as ``floor``).

Ordinal ramps (``--ordinal``) are checked for monotone lightness, a minimum
step between neighbours and a visible lightest step instead.

Usage::

  python validate_palette.py "#2a78d6,#eb6834,#1baf7a" --mode light
  python validate_palette.py "#86b6ef,#5598e7,#2a78d6" --ordinal --surface "#fcfcfb"

Exit status 0 when every check passes, 1 otherwise, 2 on bad input.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys

# --- thresholds -------------------------------------------------------------
# OKLCH lightness band per surface mode.
BAND = {"light": (0.43, 0.77), "dark": (0.48, 0.67)}
# Minimum OKLCH chroma for a categorical colour.
CHROMA_FLOOR = 0.10
# Colour-blind separation: OKLab distance x100 of the closest pair, worst of
# protan and deutan. Meeting the target passes; between floor and target is
# reported as "floor" (usable, tight); below the floor fails.
CVD_TARGET = 8.0
CVD_FLOOR = 6.0
# Normal-vision separation: OKLab distance x100 of the closest pair.
NORMAL_FLOOR = 15.0
# WCAG contrast of each colour against the surface (non-text graphics), and
# the lower bound a colour may sit at when its marks carry labels or outlines.
CONTRAST_MIN = 3.0
CONTRAST_RELIEF = 2.0
# Ordinal ramps.
ORDINAL_MIN_DL = 0.06
ORDINAL_LIGHT_FLOOR = 2.0

DEFAULT_SURFACE = {"light": "#fcfcfb", "dark": "#1a1a19"}

# Machado, Oliveira & Fernandes (2009), severity 1.0, applied to linear RGB.
CVD_MATRICES = {
    "protan": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deutan": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
    "tritan": (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
}

_HEX = re.compile(r"^#?[0-9a-fA-F]{6}$")


# --- colour conversions -----------------------------------------------------
def is_hex_color(value: str) -> bool:
    """True for ``#rrggbb`` (the ``#`` is optional, surrounding space ignored)."""
    return isinstance(value, str) and bool(_HEX.match(value.strip()))


def hex2srgb(value: str) -> tuple[float, float, float]:
    """``#rrggbb`` to gamma-encoded sRGB components in 0..1."""
    h = value.strip().lstrip("#")
    if not _HEX.match(h):
        raise ValueError(f"not a #rrggbb colour: {value!r}")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def s2lin(c: float) -> float:
    """sRGB transfer function, encoded to linear light."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin2s(c: float) -> float:
    """Inverse sRGB transfer function, linear light to encoded (clamped to 0..1)."""
    c = min(1.0, max(0.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def lin(value: str) -> tuple[float, float, float]:
    """``#rrggbb`` to linear-light RGB."""
    r, g, b = hex2srgb(value)
    return s2lin(r), s2lin(g), s2lin(b)


def relative_luminance(value: str) -> float:
    """WCAG relative luminance of a colour."""
    r, g, b = lin(value)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio between two colours (1.0 to 21.0)."""
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def lin2oklab(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Linear-light RGB to OKLab (Ottosson 2020)."""
    l_ = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m_ = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s_ = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l3, m3, s3 = (math.copysign(abs(v) ** (1 / 3), v) for v in (l_, m_, s_))
    return (
        0.2104542553 * l3 + 0.7936177850 * m3 - 0.0040720468 * s3,
        1.9779984951 * l3 - 2.4285922050 * m3 + 0.4505937099 * s3,
        0.0259040371 * l3 + 0.7827717662 * m3 - 0.8086757660 * s3,
    )


def oklch(value: str) -> tuple[float, float]:
    """OKLCH lightness and chroma of a colour (hue is not needed by the checks)."""
    L, a, b = lin2oklab(*lin(value))
    return L, math.hypot(a, b)


def simulate(rgb_linear: tuple[float, float, float], kind: str) -> tuple[float, float, float]:
    """Apply a Machado 2009 CVD matrix to a linear-light colour, clamped to 0..1."""
    m = CVD_MATRICES[kind]
    return tuple(  # type: ignore[return-value]
        min(1.0, max(0.0, row[0] * rgb_linear[0] + row[1] * rgb_linear[1] + row[2] * rgb_linear[2]))
        for row in m
    )


def deltaE(a: str, b: str, sim: str | None = None) -> float:
    """OKLab distance x100 between two colours, optionally as seen under ``sim``."""
    la, lb = lin(a), lin(b)
    if sim:
        la, lb = simulate(la, sim), simulate(lb, sim)
    pa, pb = lin2oklab(*la), lin2oklab(*lb)
    return 100.0 * math.dist(pa, pb)


# --- checks -----------------------------------------------------------------
Row = tuple[str, object, str]


def _pairs(n: int, how: str) -> list[tuple[int, int]]:
    if how == "all":
        return [(i, j) for i in range(n) for j in range(i + 1, n)]
    return [(i, i + 1) for i in range(n - 1)]


def validate(colors: list[str], mode: str = "light", surface: str | None = None,
             pairs: str = "adjacent") -> tuple[list[Row], bool]:
    """Run the categorical checks. Returns ``(rows, ok)``.

    Each row is ``(check, state, detail)``; ``state`` is ``True``/``False``,
    ``"relief"`` on the contrast row, or ``"pass"``/``"floor"``/``"fail"`` on
    the colour-blind row. ``relief`` and ``floor`` still count as passing.
    """
    if mode not in BAND:
        raise ValueError(f"mode must be one of {sorted(BAND)}")
    surface = surface or DEFAULT_SURFACE[mode]
    lo, hi = BAND[mode]
    rows: list[Row] = []

    lch = [oklch(c) for c in colors]
    out_band = [f"{c} (L={L:.3f})" for c, (L, _) in zip(colors, lch) if not lo <= L <= hi]
    rows.append(("lightness band", not out_band,
                 f"all within {lo}-{hi}" if not out_band else "outside: " + ", ".join(out_band)))

    grayish = [f"{c} (C={C:.3f})" for c, (_, C) in zip(colors, lch) if C < CHROMA_FLOOR]
    rows.append(("chroma floor", not grayish,
                 f"all at or above {CHROMA_FLOOR}" if not grayish else "too gray: " + ", ".join(grayish)))

    ratios = [(c, contrast(c, surface)) for c in colors]
    failing = [f"{c} ({r:.2f}:1)" for c, r in ratios if r < CONTRAST_RELIEF]
    relieved = [f"{c} ({r:.2f}:1)" for c, r in ratios if CONTRAST_RELIEF <= r < CONTRAST_MIN]
    if failing:
        rows.append(("contrast vs surface", False,
                     f"below {CONTRAST_RELIEF:g}:1 on {surface}: " + ", ".join(failing)))
    elif relieved:
        rows.append(("contrast vs surface", "relief",
                     f"under {CONTRAST_MIN:g}:1 on {surface}, so label or outline these marks: "
                     + ", ".join(relieved)))
    else:
        rows.append(("contrast vs surface", True, f"all at or above {CONTRAST_MIN:g}:1 on {surface}"))

    plist = _pairs(len(colors), pairs)
    if plist:
        normal = min((deltaE(colors[i], colors[j]), i, j) for i, j in plist)
        rows.append(("normal-vision separation", normal[0] >= NORMAL_FLOOR,
                     f"closest pair {colors[normal[1]]}/{colors[normal[2]]} dE={normal[0]:.1f} "
                     f"(floor {NORMAL_FLOOR:g}, {pairs} pairs)"))
        worst = min(
            (min(deltaE(colors[i], colors[j], "protan"), deltaE(colors[i], colors[j], "deutan")), i, j)
            for i, j in plist
        )
        state = "pass" if worst[0] >= CVD_TARGET else ("floor" if worst[0] >= CVD_FLOOR else "fail")
        rows.append(("colour-blind separation", state,
                     f"closest pair {colors[worst[1]]}/{colors[worst[2]]} dE={worst[0]:.1f} under "
                     f"protan/deutan (target {CVD_TARGET:g}, floor {CVD_FLOOR:g})"))
    ok = all(state in (True, "pass", "floor", "relief") for _, state, _ in rows)
    return rows, ok


def validate_ordinal(colors: list[str], mode: str = "light",
                     surface: str | None = None) -> tuple[list[Row], bool]:
    """Checks for a light-to-dark (or dark-to-light) ordinal ramp. Returns ``(rows, ok)``."""
    surface = surface or DEFAULT_SURFACE.get(mode, DEFAULT_SURFACE["light"])
    Ls = [oklch(c)[0] for c in colors]
    rows: list[Row] = []
    steps = [b - a for a, b in zip(Ls, Ls[1:])]
    monotone = all(s > 0 for s in steps) or all(s < 0 for s in steps)
    rows.append(("monotone lightness", monotone, "L " + " -> ".join(f"{L:.2f}" for L in Ls)))
    smallest = min((abs(s) for s in steps), default=0.0)
    rows.append(("step size", bool(steps) and smallest >= ORDINAL_MIN_DL,
                 f"smallest step dL={smallest:.3f} (minimum {ORDINAL_MIN_DL})"))
    # The step closest to the surface in luminance is the one at risk of vanishing.
    faintest = min(colors, key=lambda c: contrast(c, surface)) if colors else surface
    cr = contrast(faintest, surface)
    rows.append(("faintest step visible", cr >= ORDINAL_LIGHT_FLOOR,
                 f"{faintest} {cr:.2f}:1 on {surface} (minimum {ORDINAL_LIGHT_FLOOR:g}:1)"))
    return rows, all(state is True for _, state, _ in rows)


# --- CLI ----------------------------------------------------------------------
def _label(state: object) -> str:
    if state is True or state == "pass":
        return "PASS"
    if state in ("floor", "relief"):
        return str(state).upper()
    return "FAIL"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Check a chart palette (Olano charts skill).")
    parser.add_argument("palette", help='comma-separated hex colours, e.g. "#2a78d6,#eb6834"')
    parser.add_argument("--mode", choices=sorted(BAND), default="light")
    parser.add_argument("--surface", help="background colour (default depends on --mode)")
    parser.add_argument("--pairs", choices=["adjacent", "all"], default="adjacent",
                        help="which pairs must stay apart: neighbours in order (default) or every pair")
    parser.add_argument("--ordinal", action="store_true", help="check an ordinal ramp instead")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    colors = [c.strip() for c in args.palette.split(",") if c.strip()]
    bad = [c for c in colors + ([args.surface] if args.surface else []) if not is_hex_color(c)]
    if bad or len(colors) < 2:
        print("error: give at least two #rrggbb colours" + (f"; not colours: {', '.join(bad)}" if bad else ""))
        sys.exit(2)
    colors = ["#" + c.lstrip("#").lower() for c in colors]
    surface = "#" + args.surface.lstrip("#").lower() if args.surface else None

    if args.ordinal:
        rows, ok = validate_ordinal(colors, args.mode, surface)
    else:
        rows, ok = validate(colors, args.mode, surface, args.pairs)

    if args.json:
        print(json.dumps({"ok": ok, "checks": [
            {"check": name, "result": _label(state).lower(), "detail": detail} for name, state, detail in rows
        ]}, indent=2))
    else:
        for name, state, detail in rows:
            print(f"[{_label(state)}] {name}: {detail}")
        print("ALL CHECKS PASS" if ok else "SOME CHECKS FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
