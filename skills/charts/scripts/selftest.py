#!/usr/bin/env python3
"""Self-test for the charts skill — standard library only, no browser needed.

    python3 scripts/selftest.py            # run everything
    python3 scripts/selftest.py -v         # verbose

Proves that every shipped theme passes the palette validator in its
own mode against its own surface (plus the text-contrast, emphasis and ordinal
gates), that every example recipe builds a well-formed Vega-Lite spec for every
theme and preset, that the HTML page carries the render contract (vendored
scripts by absolute file:// URL, inlined fonts, the ``.render-done`` sentinel),
and that the validation errors are the actionable ones the SKILL promises.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from olano_chart import frame, layout, palette, themes  # noqa: E402
from olano_chart.fonts import Measurer, fonts_dir  # noqa: E402
from olano_chart.recipes import RECIPES, load_recipe  # noqa: E402
from olano_chart.spec import SpecError, load_spec  # noqa: E402

SKILL = HERE.parent
EXAMPLES = sorted((SKILL / "assets" / "examples").glob("*.json"))
CHART = HERE / "chart.py"


def build(example: Path, theme_name: str = "clean", size: str = "square"):
    spec = load_spec(example, theme=theme_name, size=size)
    theme = themes.load_theme(spec.theme)
    recipe = load_recipe(spec.type)
    spec.measurer = Measurer(theme.fontset, theme.generic_by_family())
    has_chart_fn = getattr(recipe, "has_chart", None)
    has_chart = bool(has_chart_fn(spec)) if callable(has_chart_fn) else True
    lay = layout.compute_layout(spec, theme, size, spec.measurer,
                                supports_annotations=bool(getattr(recipe, "SUPPORTS_ANNOTATIONS", False)),
                                preferred_height=getattr(recipe, "preferred_height", None), has_chart=has_chart,
                                places_hero=bool(getattr(recipe, "PLACES_HERO", False)))
    spec.layout = lay
    vl = recipe.build(spec, theme) if has_chart else None
    if vl is not None:
        vl = frame.finalize_vl(vl, theme, lay)
    return spec, theme, lay, vl


class ThemeGates(unittest.TestCase):
    def test_every_theme_passes_every_gate(self):
        for name in themes.BUILTIN:
            th = themes.load_builtin(name)
            rows = palette.check_theme(th.tokens, th.mode)
            failing = [r for r in rows if not r[1]]
            self.assertFalse(failing, f"{name}: " + palette.format_rows(failing))

    def test_validator_cli_agrees(self):
        for name in themes.BUILTIN:
            th = themes.load_builtin(name)
            proc = subprocess.run([sys.executable, str(HERE / "validate_palette.py"), ",".join(th.tokens["categorical"]),
                                   "--mode", th.mode, "--surface", th.tokens["surface"]], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, f"{name}: {proc.stdout}")
            self.assertIn("ALL CHECKS PASS", proc.stdout)

    def test_validator_rejects_a_bad_palette(self):
        # Two near-identical greens: too close for normal vision and for colour-blind viewers.
        proc = subprocess.run([sys.executable, str(HERE / "validate_palette.py"), "#1baf7a,#20b27d,#cccccc",
                               "--mode", "light"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("SOME CHECKS FAIL", proc.stdout)

    def test_text_never_below_4_5_to_1(self):
        for name in themes.BUILTIN:
            th = themes.load_builtin(name)
            for role in ("ink", "secondary"):
                self.assertGreaterEqual(palette.contrast(th.tokens[role], th.tokens["surface"]), 4.5, f"{name}.{role}")

    def test_palette_reexports_the_validator(self):
        for fn in ("validate", "validate_ordinal", "contrast", "oklch", "deltaE"):
            self.assertTrue(callable(getattr(palette, fn)))
        self.assertAlmostEqual(palette.contrast("#000000", "#ffffff"), 21.0, places=3)
        self.assertAlmostEqual(palette.oklch("#ffffff")[0], 1.0, places=3)

class Recipes(unittest.TestCase):
    def test_every_example_builds_for_every_theme_and_preset(self):
        self.assertGreaterEqual(len(EXAMPLES), 9)
        for ex in EXAMPLES:
            for th in themes.BUILTIN:
                for size in ("square", "landscape", "slide", "email", "story", "portrait", "report", "900x1600"):
                    spec, theme, lay, vl = build(ex, th, size)
                    self.assertGreater(lay.width, 0)
                    if vl is None:
                        self.assertEqual(spec.type, "stat")
                        continue
                    self.assertEqual(vl["$schema"], frame.SCHEMA)
                    self.assertIn("config", vl)
                    self.assertEqual(vl["config"]["background"], theme.tokens["surface"])
                    self.assertEqual(vl["autosize"]["type"], "fit")
                    json.dumps(vl)  # serialisable
                    self.assertEqual(round(lay.chart.w), vl["width"])
                    self.assertEqual(round(lay.chart.h), vl["height"])
                    # nothing may touch the card edge
                    for b in lay.blocks:
                        self.assertGreaterEqual(b.x, lay.margin - 0.01, f"{ex.name} {b.role}")
                        self.assertLessEqual(b.bottom, lay.height + 0.01)
                    self.assertGreaterEqual(lay.chart.y, 0)
                    self.assertLessEqual(lay.chart.bottom, lay.height)

    def test_every_recipe_type_is_covered_by_an_example(self):
        types = {json.loads(p.read_text())["type"] for p in EXAMPLES}
        self.assertEqual(types, set(RECIPES))

    def test_single_nominal_series_takes_slot_one_only(self):
        spec, theme, lay, vl = build(SKILL / "assets" / "examples" / "area.json")
        colors = {row["color"] for row in vl["data"]["values"]}
        self.assertEqual(colors, {theme.tokens["categorical"][0]})

    def test_emphasis_uses_emphasis_and_deemphasis_only(self):
        spec, theme, lay, vl = build(SKILL / "assets" / "examples" / "bar-emphasis.json")
        colors = {row["color"] for row in vl["data"]["values"]}
        self.assertEqual(colors, {theme.tokens["emphasis"], theme.tokens["deemphasis"]})

    def test_bars_respect_the_thickness_cap(self):
        for th in themes.BUILTIN:
            for size in ("square", "slide", "email"):
                spec, theme, lay, vl = build(SKILL / "assets" / "examples" / "bar-emphasis.json", th, size)
                self.assertLessEqual(vl["layer"][0]["mark"]["height"], lay.scale.bar_cap)
                self.assertEqual(vl["layer"][0]["mark"]["cornerRadiusEnd"], 4)

    def test_labels_are_ink_never_series_colour(self):
        spec, theme, lay, vl = build(SKILL / "assets" / "examples" / "grouped.json")
        text_layer = vl["layer"][1]
        self.assertEqual(text_layer["mark"]["type"], "text")
        used = {row["lbl"] for row in vl["data"]["values"]}
        self.assertTrue(used <= {theme.tokens["ink"], theme.tokens["secondary"]})

    def test_donut_places_its_own_hero(self):
        spec, theme, lay, vl = build(SKILL / "assets" / "examples" / "donut.json")
        self.assertIsNone(lay.block("hero_value"))
        self.assertTrue(any(l["mark"].get("type") == "text" and l["encoding"].get("text", {}).get("value") == "258" for l in vl["layer"]))

    def test_stat_without_series_has_no_chart(self):
        spec, theme, lay, vl = build(SKILL / "assets" / "examples" / "stat-hero.json")
        self.assertIsNotNone(vl)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.json"
            p.write_text(json.dumps({"type": "stat", "title": "One number", "hero": {"value": "42", "label": "things"}}))
            spec, theme, lay, vl = build(p)
            self.assertIsNone(vl)
            self.assertIsNone(lay.chart)
            self.assertIsNotNone(lay.block("hero_value"))

    def test_custom_recipe_hook(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.py"
            p.write_text("def build(spec, theme):\n    return {'mark': 'bar', 'data': {'values': []}, 'encoding': {}}\n")
            mod = load_recipe("bar", p)
            self.assertTrue(callable(mod.build))
            bad = Path(d) / "bad.py"
            bad.write_text("x = 1\n")
            with self.assertRaises(ValueError):
                load_recipe("bar", bad)


class Page(unittest.TestCase):
    def test_page_contract(self):
        spec, theme, lay, vl = build(SKILL / "assets" / "examples" / "line.json", "midnight", "landscape")
        page = frame.build_page(lay, theme, vl, svg_card=True, embed_fonts=True, page_title=spec.title)
        for name in frame.VENDOR_FILES:
            self.assertIn((frame.VENDOR_DIR / name).as_uri(), page)
        self.assertIn("render-done", page)
        self.assertIn("renderer: 'svg'", page)
        self.assertIn("actions: false", page)
        self.assertIn("document.fonts", page)
        if fonts_dir() is not None:
            self.assertIn("@font-face", page)
            self.assertIn("data:font/ttf;base64,", page)
        self.assertNotIn("<foreignObject", page)
        self.assertIn('id="frame"', page)
        # the chart box and every chrome block are absolutely positioned from the layout
        self.assertIn(f'id="chart" style="left:{lay.chart.x:.2f}px;top:{lay.chart.y:.2f}px', page)

    def test_fonts_measure_when_bundled(self):
        th = themes.load_builtin("clean")
        m = Measurer(th.fontset, th.generic_by_family())
        if fonts_dir() is None:
            self.skipTest("bundled fonts not available")
        w = m.width("United States", "Instrument Sans", 20, 400)
        self.assertTrue(100 < w < 160, w)
        self.assertGreater(m.width("United States", "Instrument Sans", 20, 700), w)
        lines = m.wrap("The US is a third of the customer base and growing fast", 300, "Instrument Sans", 40, 700)
        self.assertGreater(len(lines), 1)


class Errors(unittest.TestCase):
    def _err(self, recipe: dict) -> str:
        with self.assertRaises(SpecError) as cm:
            load_spec(recipe)
        return str(cm.exception)

    def test_actionable_messages(self):
        base = {"type": "bar", "title": "t", "categories": ["a", "b"], "series": [{"name": "s", "values": [1, 2]}]}
        self.assertIn("fold the tail", self._err({**base, "series": [{"name": f"s{i}", "values": [1, 2]} for i in range(9)]}))
        self.assertIn("one value per category", self._err({**base, "series": [{"name": "s", "values": [1]}]}))
        self.assertIn("use 'bar'", self._err({**base, "type": "donut", "categories": list("abcdefg"), "series": [{"name": "s", "values": [1] * 7}]}))
        self.assertIn("at least 2 series", self._err({**base, "type": "stacked_bar"}))
        self.assertIn("at least 2 categories", self._err({**base, "type": "line", "categories": ["a"], "series": [{"name": "s", "values": [1]}]}))
        self.assertIn("not in the chart", self._err({**base, "highlight": ["zzz"]}))
        self.assertIn("not in the chart", self._err({**base, "annotations": [{"target": "zzz", "text": "x"}]}))
        self.assertIn("did you mean 'bar'", self._err({**base, "type": "bars"}))
        self.assertIn("did you mean 'size'", self._err({**base, "sizes": "square"}))
        self.assertIn("finite", self._err({**base, "series": [{"name": "s", "values": [1, float("inf")]}]}))
        self.assertIn("exactly 2 series", self._err({**base, "type": "dumbbell"}))
        self.assertIn("needs a hero", self._err({"type": "stat", "title": "t"}))
        self.assertIn("fold to 3 groups", self._err({"type": "scatter", "title": "t", "points": [{"x": i, "y": i, "group": f"g{i}"} for i in range(4)]}))
        with self.assertRaises(ValueError):
            layout.parse_size("100x100")
        with self.assertRaises(ValueError):
            layout.parse_size("5000x600")

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.json"
            bad.write_text('{"type": "bar", "title": "x", "categories": ["a"], "series": [{"name": "s", "values": [1, 2]}]}')
            proc = subprocess.run([sys.executable, str(CHART), "render", str(bad), "--out", str(Path(d) / "o.html")], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertTrue(proc.stderr.startswith("error:"))
            proc = subprocess.run([sys.executable, str(CHART), "nonsense"], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            ok = Path(d) / "o.html"
            proc = subprocess.run([sys.executable, str(CHART), "render", str(EXAMPLES[0]), "--out", str(ok)], capture_output=True, text=True, cwd=d)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(ok.is_file())
            self.assertIn("render_html_image(", proc.stdout)
            self.assertFalse(list(Path(d).glob("reports/*")), "must write only where --out says")


if __name__ == "__main__":
    unittest.main(verbosity=1)
