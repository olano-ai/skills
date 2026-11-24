---
name: charts
description: "Make publication-quality data charts on the first attempt — bar, column, stacked, grouped, line, area, dumbbell, donut, stat/KPI card, histogram, heatmap, scatter — for a chat reply, an email or newsletter, a slide deck, a report, or a social post (LinkedIn, X, Instagram, stories). Use this skill whenever the deliverable is a chart, graph, plot, histogram, heatmap, trend, comparison, breakdown, KPI card or any picture of numbers, whether the user says 'chart', 'graph', 'plot', 'visualise', 'show me the numbers', 'make an image of this data', 'a graphic for LinkedIn with our revenue', or asks how something changed over time. It wins over xlsx when the deliverable is a picture of data rather than a spreadsheet, and over canvas-design whenever real numbers are on the artwork. Zero installs: bundled Vega-Lite, bundled fonts, themed frames (clean, midnight, editorial, brand) rendered to PNG or SVG through the built-in browser."
metadata:
  requires_tools: [render_html_image]
---

# Charts

A chart is a sentence with evidence. This skill turns a small recipe JSON (or any
Vega-Lite spec) into a themed, self-contained HTML card — takeaway title, one
emphasised thing, labelled values, source line — and the built-in browser turns
that into exact-pixel PNG or SVG. Pick the form from the reader's task, take colours
from a checked palette, keep the mark specs fixed, and let the title carry the point.

## 1. Environment

What ships with this skill and needs no setup:

- `scripts/chart.py` — recipe → Vega-Lite → themed HTML. Python 3.11, standard library only.
- `assets/vendor/` — Vega, Vega-Lite and vega-embed, loaded by absolute `file://` path.
- Bundled OFL fonts from the sibling `canvas-design` skill (Instrument Sans/Serif, Big Shoulders, IBM Plex Mono), inlined into the page as data URIs.
- Olano's `render_html_image` (PNG, exact pixels, 2× by default) and `render_html_svg` (extracts a native SVG) — both run on the bundled Chromium, no credits.
- Three validated themes (`clean` light, `midnight` dark, `editorial` warm paper) plus `brand`, which reads `brand/tokens.json` from the working directory when a brand kit exists.

Never: `pip install` a plotting library, `apt-get` anything, download a font, hand-place
text with matplotlib coordinates, or call `image_generate` for data. A generated
picture is a decorative option only — offer it as an illustration with the real numbers
composed on top via the `social-image-composer` skill, never as the chart itself.

`scripts/` and `references/` are relative to this skill's base directory (shown where
the skill was loaded). Claude Code users without the render tools open the HTML in any browser.

## 2. Workflow

**(a) Get the data and show it first.** Put the numbers in the reply as a markdown
table (at most ~25 rows; otherwise top-N plus an "Other" row) with the source, the
as-of time and any data-quality notes — nulls become "Unspecified", "US" and "USA" are
merged, partial periods are named. The table is the contract the chart must match.

**(b) Propose, then wait.** Offer one or two chart forms with a one-line reason each
(see `references/choosing-a-form.md`) and name the destination, which fixes the preset
and theme (table in §4). Wait for the go-ahead. Skip the wait only when the person said
"just make it" or already confirmed the same data earlier in the thread.

**(c) Write the story before the spec** (`references/story-and-style.md`):
title = the takeaway in one sentence; subtitle = the measure and period; sort by value
unless the categories are ordered; highlight the one thing that matters and put one
annotation on it; use a hero number when the point is a single figure; source and
as-of always. Then write the recipe (`references/recipes.md`).

**(d) Render.**

```
python3 <skill>/scripts/chart.py render spec.json --theme clean --size square --out reports/<name>.html
render_html_image(html="reports/<name>.html", width=1200, height=1200,
                  save_path="reports/<name>.png", wait_for=".render-done")
```

`width`/`height` come from the preset table in §4 — the script prints the exact call
after every render. The page appends `.render-done` once Vega has drawn; `wait_for` is
what makes the capture deterministic.

**(e) Verify.** Trust the script's validation for data problems — it refuses a
mismatched series length, a 9th series, a 7-slice donut, an unknown highlight target,
and says what to do instead. For social, deck and email deliverables run exactly one
`image_describe` pass on the PNG with this fixed checklist:

1. Any text cut off or overlapping?
2. Is the title readable at thumbnail size?
3. Is there one clear emphasis?
4. Do the numbers match the table?
5. Anything outside the canvas or off-theme?

Fix and re-render at most once more, then stop and ask rather than looping.

**(f) Deliver.** One file in `reports/`. Finish with `Saved: <path>` on its own line,
no backticks. Offer variants (dark, landscape, deck size) instead of producing them
unasked.

## 3. Three tiers of flexibility

| Tier | Command | When |
|---|---|---|
| Recipe | `chart.py render spec.json` | Twelve chart types, all design rules applied for you. Default. |
| Raw Vega-Lite | `chart.py vl spec.vl.json --title … --subtitle … --source …` | Anything a recipe cannot express: facets, binning, layered marks, small multiples. Start from a recipe with `render … --emit-vl`, edit, then `vl`. Theme config merges into the spec; the data is untouched. Patterns in `references/vega-lite-cookbook.md`. |
| Any markup | `chart.py frame --body figure.svg\|figure.html --title …` | A hand-made SVG or HTML fragment in the themed frame, no Vega. |

Common options: `--theme clean|midnight|editorial|brand`, `--size <preset>|WxH`
(320–4000 px), `--out path.html`, `--svg-card` (also builds `<svg id="card">` for
`render_html_svg(html=…, selector="#card", save_path="….svg", wait_for=".render-done")`),
`--embed-fonts` (fonts inside that SVG). `chart.py themes` prints the tokens;
`chart.py validate-palette "#hex,…" --mode light|dark --surface #hex` runs the palette
validator on any palette; `chart.py gallery --out DIR` renders every example.

**Fork a recipe** when a rule needs bending: copy `scripts/olano_chart/recipes/bar.py`
to `scratch/my_recipe.py`, edit `build(spec, theme)` (it returns a plain Vega-Lite
dict), run `render spec.json --recipe scratch/my_recipe.py`. Every recipe is a short
flat file written to be copied.

**No shell available?** `references/manual-frame.md` is a copy-paste HTML template:
fill in the spec, save it with `write_file`, render with `render_html_image`.

## 4. Destinations → preset and theme

| Destination | `--size` | CSS px (W×H for the render call) | Theme | Format |
|---|---|---|---|---|
| Chat reply (Telegram, WhatsApp, Slack) | `landscape` | 1200×675 | clean | PNG |
| Email / newsletter | `email` | 1200×600 | clean | PNG |
| LinkedIn / Instagram feed | `square` | 1200×1200 | clean or midnight | PNG |
| LinkedIn / Instagram portrait | `portrait` | 1080×1350 | midnight or clean | PNG |
| Story / Reel | `story` | 1080×1920 | midnight | PNG |
| X / link card | `landscape` | 1200×675 | midnight or clean | PNG |
| Slide (16:9 deck) | `slide` | 1920×1080 | match the deck; midnight for dark decks | SVG for HTML decks, PNG for pptx |
| Report / document figure | `report` | 1600×900 | editorial or clean | SVG for print and design tools, PNG otherwise |
| Anything on-brand | as above | — | `brand` (needs `brand/tokens.json`) | — |

The PNG is captured at 2× (a `square` card is 2400×2400 pixels). SVG (`--svg-card` +
`render_html_svg`) is for HTML decks, design tools and print — it scales and its text
stays editable; PNG is for email, LinkedIn, chat and anywhere an image is pasted.

## 5. Quality bar

Before handing over, the card must pass the checklist in §2(e) and read as one quiet
system: a takeaway title, one emphasis, labelled values in ink (never in the series
colour), ≤ 24 px bars with air around them, hairline solid gridlines, a legend for two
or more series, a source line — and nothing touching the card edge. The colour comes
from a theme whose every slot passed the validator; do not eyeball a new hex.

- `references/choosing-a-form.md` — is it a chart, and which one.
- `references/story-and-style.md` — titles, emphasis, annotation, destinations, what "impressive" means.
- `references/color-and-palette.md`: what colour is for, the validator's checks, the themes' tokens, brand colours.
- `references/marks-and-anatomy.md` — presets, margins, type scale, mark specs, label rules.
- `references/anti-patterns.md` — what goes wrong, and the static-output additions.
- `references/recipes.md` — every recipe field with a full example each.
- `references/vega-lite-cookbook.md` — patterns for the raw Vega-Lite tier.
- `references/manual-frame.md` — the copy-paste HTML template.
