# Vega-Lite cookbook (the raw tier)

When a recipe cannot express the chart, write Vega-Lite and wrap it:

```
python3 <skill>/scripts/chart.py render spec.json --emit-vl > chart.vl.json   # start from a recipe, or write from scratch
python3 <skill>/scripts/chart.py vl chart.vl.json --title "…" --subtitle "…" --kicker "…" \
        --source "…" --as-of 2026-09-06 [--note "…"] [--hero "63|customer accounts"] \
        [--theme midnight] [--size slide] [--out reports/name.html] [--svg-card]
```

The frame merges the theme's `config` under the spec's own `config` (yours wins), sizes a
single or layered view to the chart box with `autosize: fit`, and leaves the data alone.
A `title` inside the spec becomes the card title unless `--title` is given (`--keep-title`
keeps it in the chart too). Schema: `https://vega.github.io/schema/vega-lite/v6.json`.

Everything the recipes do — ink text, hairline grid, 4 px rounded bar ends, 2 px surface
rings, top legend, the categorical range — is in that config, so a plain spec already
looks themed. Colours: `"color": {"field": "series", "type": "nominal"}` takes the
theme's categorical slots in order; a quantitative colour on `rect` takes the sequential
ramp; use `theme.tokens` values from `chart.py themes` for anything explicit.

## Patterns

### Nested categories: xOffset, row, column

```json
{"data": {"values": [{"region": "EU", "product": "Platform", "q": "Q1", "v": 12}, "…"]},
 "mark": {"type": "bar", "cornerRadiusEnd": 4, "width": 18},
 "encoding": {"x": {"field": "q", "type": "nominal", "sort": null, "axis": {"title": null, "labelAngle": 0}},
              "xOffset": {"field": "product"},
              "y": {"field": "v", "type": "quantitative", "axis": {"title": null}},
              "color": {"field": "product", "type": "nominal"},
              "column": {"field": "region", "header": {"labelFontSize": 18, "title": null}}}}
```

`xOffset` groups within a band; `column`/`row` facet into panels. Faceted and
concatenated specs cannot `fit` — give them an explicit `width`/`height` per panel that
fits the box (roughly 1056×780 on a square card, 1092×400 on landscape, 1750×760 on a
slide) and pass `--keep-size`.

### Binning in Vega-Lite (instead of the histogram recipe)

```json
{"mark": {"type": "bar", "stroke": "#fcfcfb", "strokeWidth": 2, "cornerRadiusEnd": 2},
 "encoding": {"x": {"field": "amount", "type": "quantitative", "bin": {"maxbins": 20}, "axis": {"title": "Deal value, $K"}},
              "y": {"aggregate": "count", "axis": {"title": "Deals"}}}}
```

### Direct labels as a layer

```json
{"layer": [
  {"mark": {"type": "bar", "height": 22, "cornerRadiusEnd": 4},
   "encoding": {"y": {"field": "name", "type": "nominal", "sort": null, "axis": {"title": null}},
                "x": {"field": "v", "type": "quantitative", "axis": null, "scale": {"domain": [0, 30]}}}},
  {"mark": {"type": "text", "align": "left", "baseline": "middle", "dx": 8, "fontWeight": 700},
   "encoding": {"y": {"field": "name", "type": "nominal", "sort": null},
                "x": {"field": "v", "type": "quantitative"},
                "text": {"field": "v", "format": ",.0f"}}}]}
```

Stretch the domain past the longest bar so labels have room; text colour comes from the
theme's `text` config (ink) — do not put the series colour on text.

### An annotation beside one mark

```json
{"mark": {"type": "text", "align": "left", "baseline": "middle", "dx": 60, "fontStyle": "italic", "color": "#52514e"},
 "transform": [{"filter": {"field": "name", "equal": "United States"}}],
 "encoding": {"y": {"field": "name", "type": "nominal", "sort": null},
              "x": {"field": "v", "type": "quantitative"},
              "text": {"value": "35% of accounts"}}}
```

Use the `{"field": …, "equal": …}` filter form — no quoting problems in names.

### Two measures without a dual axis

Index both to 100 at the first point and plot on one axis:

```json
{"transform": [
   {"window": [{"op": "first_value", "field": "v", "as": "base"}], "groupby": ["series"], "sort": [{"field": "month"}]},
   {"calculate": "100 * datum.v / datum.base", "as": "index"}],
 "mark": {"type": "line", "point": true},
 "encoding": {"x": {"field": "month", "type": "ordinal", "sort": null},
              "y": {"field": "index", "type": "quantitative", "axis": {"title": "Index, first month = 100"}},
              "color": {"field": "series", "type": "nominal"}}}
```

Or small multiples: `{"vconcat": [specA, specB]}` with explicit sizes, one shared x.

### Small multiples

```json
{"facet": {"field": "region", "columns": 3, "header": {"title": null, "labelFontSize": 18}},
 "spec": {"width": 300, "height": 180, "mark": "line",
          "encoding": {"x": {"field": "month", "type": "ordinal", "sort": null, "axis": {"title": null}},
                       "y": {"field": "v", "type": "quantitative", "axis": {"title": null}}}}}
```

### Heatmap

```json
{"mark": {"type": "rect", "stroke": "#fcfcfb", "strokeWidth": 2},
 "encoding": {"x": {"field": "hour", "type": "ordinal", "sort": null, "axis": {"orient": "top", "title": null}},
              "y": {"field": "day", "type": "ordinal", "sort": null, "axis": {"title": null}},
              "color": {"field": "v", "type": "quantitative", "legend": {"orient": "bottom", "title": null}}}}
```

## Gotchas

- **Text that overflows the plot is fine.** `autosize: fit` measures labels that stick out
  (line-end labels, an annotation past the last bar) and shrinks the plot to make room. Do
  not add `padding` for them — it double-counts. A mark anchored *near* but not at the edge
  can keep a few residual pixels; a small `padding.right` (10–15% of the label) covers it.
- **Ranged bars need a baseline.** With `x`/`x2` given (pre-binned data), add
  `"y2": {"datum": 0}` or the bars collapse to lines.
- **A `scale: null` colour field cannot sit in a layer over a quantitative colour scale**
  (Vega-Lite merges the scales and fails). Use `"color": {"condition": {"test": "datum.light", "value": "#fff"}, "value": "#0b0b0b"}`.
- **Keep the data order:** `"sort": null` on the category channel; otherwise Vega-Lite sorts alphabetically.
- **Horizontal labels:** `"axis": {"labelAngle": 0}` — the default for nominal x is rotated.
- **Number formats:** `"format": ",.0f"` on a text or axis, or a `labelExpr` such as
  `"format(datum.value, ',.1~f') + 'K'"`; `~` trims trailing zeros.
- **Expressions on mark properties** (`"dx": {"expr": "datum.up ? 8 : -8"}`) work for
  `align`, `dx`, `dy`, `fontWeight`, `cornerRadiusEnd`, etc.
- **Fonts:** the page embeds the theme's faces; `config.font` is already set. Refer to a
  face by family name (`"font": "Instrument Sans"`) if you must override.
- **Never** dual y axes, dashed grids, `scheme: "category10"`, or a 9th colour.
