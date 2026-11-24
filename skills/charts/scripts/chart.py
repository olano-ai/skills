#!/usr/bin/env python3
"""chart.py — recipe JSON (or any Vega-Lite spec) → a themed, self-contained HTML chart card.

    python3 chart.py render spec.json [--theme clean|midnight|editorial|brand] [--size square|…|WxH]
                                      [--out reports/name.html] [--recipe my_recipe.py] [--emit-vl]
                                      [--svg-card] [--embed-fonts]
    python3 chart.py vl spec.vl.json [--title …] [--subtitle …] [--kicker …] [--source …] [--as-of …] [--note …] …
    python3 chart.py frame --body figure.svg|figure.html [--title …] …
    python3 chart.py gallery --out DIR [--themes all]
    python3 chart.py validate-palette "#hex,#hex,…" --mode light|dark [--surface #hex] [--pairs all] [--ordinal]
    python3 chart.py themes [--check]

Exit codes: 0 ok · 1 validation error (message on stderr) · 2 usage.
Standard library only (Python 3.11+).  Rasterise the HTML with Olano's
render_html_image(html=<path>, width=W, height=H, save_path=…, wait_for=".render-done").
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from olano_chart import frame, layout as layout_mod, recipes, themes  # noqa: E402
from olano_chart.fonts import Measurer  # noqa: E402
from olano_chart.spec import ChartSpec, Hero, Notes, SpecError, load_spec  # noqa: E402

SKILL_DIR = HERE.parent
EXAMPLES_DIR = SKILL_DIR / "assets" / "examples"


def kebab(text: str, limit: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "chart").lower()).strip("-")
    return (s[:limit].rstrip("-") or "chart")


def resolve_out(out: str | None, title: str, ext: str = ".html") -> Path:
    if out:
        p = Path(out)
        if p.is_dir() or str(out).endswith(("/", os.sep)):
            return p / (kebab(title) + ext)
        return p
    return Path("reports") / (kebab(title) + ext)


def _measurer(theme) -> Measurer:
    return Measurer(theme.fontset, theme.generic_by_family())


def _render_hint(out: Path, lay) -> str:
    stem = out.with_suffix("")
    return (f'render_html_image(html="{out}", width={lay.width}, height={lay.height}, '
            f'save_path="{stem}.png", wait_for=".render-done")')


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------
def build_from_recipe(spec: ChartSpec, theme, recipe_path: str | None):
    recipe = recipes.load_recipe(spec.type, recipe_path)
    measurer = _measurer(theme)
    spec.measurer = measurer
    has_chart_fn = getattr(recipe, "has_chart", None)
    has_chart = bool(has_chart_fn(spec)) if callable(has_chart_fn) else True
    lay = layout_mod.compute_layout(
        spec, theme, spec.size, measurer,
        supports_annotations=bool(getattr(recipe, "SUPPORTS_ANNOTATIONS", False)),
        preferred_height=getattr(recipe, "preferred_height", None),
        has_chart=has_chart,
        places_hero=bool(getattr(recipe, "PLACES_HERO", False)),
    )
    spec.layout = lay
    vl = recipe.build(spec, theme) if has_chart else None
    if vl is not None:
        if not isinstance(vl, dict):
            raise SpecError("the recipe's build() must return a Vega-Lite spec as a dict")
        vl = frame.finalize_vl(vl, theme, lay)
    return lay, vl


def cmd_render(args) -> int:
    spec = load_spec(args.spec, theme=args.theme, size=args.size)
    theme = themes.load_theme(spec.theme)
    themes.report_notes(theme)
    lay, vl = build_from_recipe(spec, theme, args.recipe)
    if args.emit_vl:
        print(json.dumps(vl if vl is not None else {"note": "this recipe draws no Vega chart (stat without a series)"}, indent=2, ensure_ascii=False))
        return 0
    page = frame.build_page(lay, theme, vl, svg_card=args.svg_card, embed_fonts=args.embed_fonts, page_title=spec.title,
                            meta={"type": spec.type, "theme": theme.name, "size": spec.size})
    out = resolve_out(args.out, spec.title)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out}  ({lay.width}x{lay.height}, {theme.name}, {lay.preset}, {spec.type})")
    print(f"next: {_render_hint(out, lay)}")
    return 0


# ---------------------------------------------------------------------------
# vl — wrap any Vega-Lite spec
# ---------------------------------------------------------------------------
def _title_text(v) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        t = v.get("text", "")
        return " ".join(t) if isinstance(t, list) else str(t)
    if isinstance(v, list):
        return " ".join(str(x) for x in v)
    return ""


def _chrome_spec(args, default_title: str, subtitle_default: str = "", type_: str = "vl") -> ChartSpec:
    title = args.title or default_title
    if not title:
        raise SpecError("give the card a takeaway with --title (or put a title in the spec)")
    spec = ChartSpec(type=type_, title=title, kicker=args.kicker or "", subtitle=args.subtitle or subtitle_default)
    spec.notes = Notes(args.source or "", args.as_of or "", args.note or "")
    spec.logo = args.logo or ""
    if getattr(args, "hero", None):
        val, _, label = args.hero.partition("|")
        spec.hero = Hero(val.strip(), label.strip())
    spec.theme = args.theme or "clean"
    spec.size = args.size or "square"
    return spec


def cmd_vl(args) -> int:
    p = Path(args.spec)
    if not p.is_file():
        raise SpecError(f"Vega-Lite spec not found: {p}")
    try:
        vl = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SpecError(f"{p} is not valid JSON at line {exc.lineno}: {exc.msg}") from exc
    if not isinstance(vl, dict):
        raise SpecError("a Vega-Lite spec is a JSON object")
    spec_title = _title_text(vl.get("title"))
    subtitle_default = ""
    if isinstance(vl.get("title"), dict):
        subtitle_default = _title_text({"text": vl["title"].get("subtitle", "")})
    spec = _chrome_spec(args, spec_title, subtitle_default)
    if not args.keep_title:
        vl.pop("title", None)
    theme = themes.load_theme(spec.theme)
    themes.report_notes(theme)
    measurer = _measurer(theme)
    spec.measurer = measurer
    lay = layout_mod.compute_layout(spec, theme, spec.size, measurer, supports_annotations=False, preferred_height=None, has_chart=True)
    spec.layout = lay
    vl = frame.finalize_vl(vl, theme, lay, force_size=not args.keep_size)
    page = frame.build_page(lay, theme, vl, svg_card=args.svg_card, embed_fonts=args.embed_fonts, page_title=spec.title,
                            meta={"type": "vega-lite", "theme": theme.name, "size": spec.size})
    out = resolve_out(args.out, spec.title)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out}  ({lay.width}x{lay.height}, {theme.name}, {lay.preset}, vega-lite)")
    print(f"next: {_render_hint(out, lay)}")
    return 0


# ---------------------------------------------------------------------------
# frame — wrap arbitrary markup
# ---------------------------------------------------------------------------
def cmd_frame(args) -> int:
    p = Path(args.body)
    if not p.is_file():
        raise SpecError(f"--body file not found: {p}")
    spec = _chrome_spec(args, args.title or "")
    theme = themes.load_theme(spec.theme)
    themes.report_notes(theme)
    measurer = _measurer(theme)
    spec.measurer = measurer
    lay = layout_mod.compute_layout(spec, theme, spec.size, measurer, supports_annotations=False, preferred_height=None, has_chart=True)
    spec.layout = lay
    markup = p.read_text(encoding="utf-8")
    fit = None
    if p.suffix.lower() == ".svg":
        markup, fit = frame.svg_body_fit(markup, lay.chart)
    page = frame.build_page(lay, theme, None, body_markup=markup, body_fit=fit, svg_card=args.svg_card, embed_fonts=args.embed_fonts,
                            page_title=spec.title, meta={"type": "frame", "theme": theme.name, "size": spec.size})
    out = resolve_out(args.out, spec.title)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out}  ({lay.width}x{lay.height}, {theme.name}, {lay.preset}, frame)")
    print(f"next: {_render_hint(out, lay)}")
    return 0


# ---------------------------------------------------------------------------
# gallery
# ---------------------------------------------------------------------------
GALLERY_SIZES = ("square", "landscape", "slide", "email")


def cmd_gallery(args) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = list(themes.BUILTIN)
    if args.themes == "all" and (Path.cwd() / "brand" / "tokens.json").is_file():
        names.append("brand")
    examples = sorted(EXAMPLES_DIR.glob("*.json"))
    if not examples:
        raise SpecError(f"no examples in {EXAMPLES_DIR}")
    failures = 0
    for ex in examples:
        for th in names:
            for size in GALLERY_SIZES:
                target = out_dir / f"{ex.stem}--{th}--{size}.html"
                try:
                    spec = load_spec(ex, theme=th, size=size)
                    theme = themes.load_theme(spec.theme)
                    lay, vl = build_from_recipe(spec, theme, None)
                    page = frame.build_page(lay, theme, vl, svg_card=args.svg_card, page_title=spec.title,
                                            meta={"type": spec.type, "theme": theme.name, "size": size})
                    target.write_text(page, encoding="utf-8")
                    print(target)
                except Exception as exc:  # keep going, report at the end
                    failures += 1
                    print(f"FAILED {target.name}: {exc}", file=sys.stderr)
    if failures:
        print(f"{failures} gallery page(s) failed", file=sys.stderr)
        return 1
    return 0


# ---------------------------------------------------------------------------
# validate-palette / themes
# ---------------------------------------------------------------------------
def cmd_validate_palette(args) -> int:
    import importlib.util
    vp_path = HERE / "validate_palette.py"
    mod_spec = importlib.util.spec_from_file_location("validate_palette_cli", vp_path)
    mod = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(mod)  # type: ignore[union-attr]
    argv = [str(vp_path), args.palette, "--mode", args.mode]
    if args.surface:
        argv += ["--surface", args.surface]
    if args.pairs:
        argv += ["--pairs", args.pairs]
    if args.ordinal:
        argv.append("--ordinal")
    sys.argv = argv
    mod.main()  # exits with the validator's own code
    return 0


def cmd_themes(args) -> int:
    print(themes.themes_summary())
    if args.check:
        from olano_chart import palette
        all_ok = True
        for name in themes.BUILTIN:
            th = themes.load_builtin(name)
            rows = palette.check_theme(th.tokens, th.mode)
            ok = all(r[1] for r in rows)
            all_ok &= ok
            print(f"== {name} ({th.mode}, surface {th.tokens['surface']}) → {'PASS' if ok else 'FAIL'}")
            print(palette.format_rows(rows))
            print()
        return 0 if all_ok else 1
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _chrome_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--title", help="the takeaway (one sentence)")
    p.add_argument("--subtitle", help="the measure and period")
    p.add_argument("--kicker", help="small uppercase label above the title")
    p.add_argument("--source", help="data source, e.g. Salesforce")
    p.add_argument("--as-of", dest="as_of", help="as-of date/time, e.g. 2026-09-06")
    p.add_argument("--note", help="data-quality note for the footer")
    p.add_argument("--hero", help="hero block as 'VALUE|label', e.g. '63|customer accounts'")
    p.add_argument("--logo", help="logo image path (png/svg/jpg), drawn bottom-right")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="chart.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("render", help="recipe JSON → themed HTML chart")
    r.add_argument("spec")
    r.add_argument("--theme", choices=["clean", "midnight", "editorial", "brand", "brand:light", "brand:dark"])
    r.add_argument("--size", help="square|landscape|portrait|story|slide|email|report or WxH")
    r.add_argument("--out", help="output .html (default reports/<kebab-title>.html)")
    r.add_argument("--recipe", help="custom recipe module with build(spec, theme) -> dict")
    r.add_argument("--emit-vl", action="store_true", help="print the generated Vega-Lite JSON and stop")
    r.add_argument("--svg-card", action="store_true", help="also build an <svg id=\"card\"> in the page")
    r.add_argument("--embed-fonts", action="store_true", help="inline @font-face data URIs into the SVG card")
    r.set_defaults(fn=cmd_render)

    v = sub.add_parser("vl", help="wrap any Vega-Lite spec in the themed frame")
    v.add_argument("spec")
    v.add_argument("--theme", choices=["clean", "midnight", "editorial", "brand", "brand:light", "brand:dark"])
    v.add_argument("--size")
    _chrome_args(v)
    v.add_argument("--out")
    v.add_argument("--keep-title", action="store_true", help="leave the spec's own title inside the chart as well")
    v.add_argument("--keep-size", action="store_true", help="respect the spec's width/height instead of fitting the box")
    v.add_argument("--svg-card", action="store_true")
    v.add_argument("--embed-fonts", action="store_true")
    v.set_defaults(fn=cmd_vl)

    f = sub.add_parser("frame", help="wrap an SVG or HTML fragment in the themed frame (no Vega)")
    f.add_argument("--body", required=True, help="file.svg or file.html")
    f.add_argument("--theme", choices=["clean", "midnight", "editorial", "brand", "brand:light", "brand:dark"])
    f.add_argument("--size")
    _chrome_args(f)
    f.add_argument("--out")
    f.add_argument("--svg-card", action="store_true")
    f.add_argument("--embed-fonts", action="store_true")
    f.set_defaults(fn=cmd_frame)

    g = sub.add_parser("gallery", help="render every example × theme × preset")
    g.add_argument("--out", required=True)
    g.add_argument("--themes", choices=["builtin", "all"], default="all")
    g.add_argument("--svg-card", action="store_true")
    g.set_defaults(fn=cmd_gallery)

    vp = sub.add_parser("validate-palette", help="check a palette (lightness, chroma, contrast, separation, colour-blind separation)")
    vp.add_argument("palette")
    vp.add_argument("--mode", choices=["light", "dark"], default="light")
    vp.add_argument("--surface")
    vp.add_argument("--pairs", choices=["adjacent", "all"])
    vp.add_argument("--ordinal", action="store_true")
    vp.set_defaults(fn=cmd_validate_palette)

    t = sub.add_parser("themes", help="print each theme's tokens")
    t.add_argument("--check", action="store_true", help="also run the palette gates on every theme")
    t.set_defaults(fn=cmd_themes)
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    try:
        return int(args.fn(args) or 0)
    except SystemExit:
        raise
    except (SpecError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # unexpected — still exit 1, with a trace when asked
        if os.environ.get("OLANO_CHART_DEBUG"):
            traceback.print_exc()
        print(f"error: {type(exc).__name__}: {exc}  (set OLANO_CHART_DEBUG=1 for a trace)", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
