# Marks and anatomy

What a finished card is made of, and the measurements the recipes use. You need
this page when you review a render, or when you write raw Vega-Lite and want it
to match the recipes. The data should be the boldest thing on the card; the rest
stays quiet.

## Card sizes (presets)

All sizes are CSS pixels; the PNG is exported at twice this resolution. Type
scales with the card.

| Preset | Size | Margin | Title | Subtitle | Ticks / labels | Footer |
|---|---|---|---|---|---|---|
| `square` | 1200×1200 | 72 | 50 | 24 | 18 / 19 | 15 |
| `landscape` | 1200×675 | 54 | 41 | 20 | 15 / 15 | 12 |
| `portrait` | 1080×1350 | 65 | 50 | 24 | 18 / 19 | 15 |
| `story` | 1080×1920 | 86 sides, 211 top, 307 bottom | 60 | 29 | 22 / 22 | 17 |
| `slide` | 1920×1080 | 86 | 66 | 32 | 24 / 24 | 19 |
| `email` | 1200×600 | 54 | 40 | 19 | 14 / 15 | 12 |
| `report` | 1600×900 | 72 | 55 | 26 | 20 / 20 | 16 |
| `WxH` | 320 to 4000 per side | max(6% of the short side, 4.5% of the long side) | 0.024·W + 0.018·H | half the title | 0.36 × title | 0.29 × title |

`story` leaves the top 11% and bottom 16% empty because the platform draws its own
controls there. The editorial theme sets its serif title 12% larger.

## Layout of a card

From top to bottom:

1. **Kicker**: a short topic in small capitals, secondary ink.
2. **Title**: the takeaway, in the display face, up to three lines.
3. **Subtitle**: what is measured and over which period.
4. **Hero** (optional): one large figure with its label.
5. **Chart**: legend (for two or more series), marks, value labels, annotation.
6. **Caption** (optional): an annotation that could not sit next to a mark.
7. **Footer**: source and as-of date on the left, a note on the right, the logo
   bottom-right.

Text is measured from the bundled fonts' glyph widths, so the title wraps where
the browser will wrap it and the chart receives exactly the space left over. Bar
charts stop growing once each row is about 2.6 times the bar's thickness; on
square and taller cards the chart may then grow up to 1.6 times and is centred so
no empty band sits above the footer. A `stat` card centres its content, and the
editorial theme adds a thin rule at the top and above the footer.

## Mark measurements

| Mark | How it is drawn |
|---|---|
| Bar and column | At most 24 px thick at a 16 px tick size (27 on a square card, 36 on a slide); 4 px rounding on the value end, square at the baseline; all bars start from one baseline |
| Stacked or grouped bars | Touching marks are separated by a 2 px gap in the background colour; only the outermost segment is rounded |
| Line | 2 px with round joins and caps; points at least 8 px with a 2 px ring in the background colour (only the end points once there are more than 30 categories) |
| Area | The series colour at 12% opacity beneath a 2 px line |
| Dumbbell | Two dots joined by a 2 px de-emphasis rule; "after" uses the first palette colour, "before" a lighter step of the same hue |
| Donut | 2 px gaps, inner radius 62% of the outer, the hero figure in the hole |
| Heatmap | 2 px gaps, a single-hue ramp, each cell label in white or ink depending on the cell's brightness |
| Gridlines | 1 px, solid, one shade away from the background; no axis line on value axes; a baseline on the category axis |

Never used: dashed lines, gradients, drop shadows, outlines around marks, 3-D.

## Labels

- **Text is never in a series colour.** Values, names, legend entries and axis
  ticks use the ink colours. A label inside a filled mark is white or ink,
  whichever reads better on that fill.
- **Bars** carry their value at the tip: outside the bar when any bar is shorter
  than about 2.5 times its label (usually true, since the shortest bar is short),
  inside and right-aligned when every bar is long enough. Once every bar is
  labelled the value axis is dropped, and the domain is stretched to leave room for
  the longest label and any annotation.
- **Columns** carry the value on top; long category names wrap to two lines.
- **Stacks** label a segment only when the value fits with padding, and always
  label the total at the end.
- **Grouped bars** label every bar up to 16 bars, then rely on the axis.
- **Lines**: `auto` labels the last point of each series (`Name · value` when
  there are several) and falls back to the legend alone when two end labels would
  be within one label height of each other; `extremes` labels each series' high and
  low; `ends` labels the first and last points; `all` labels every point up to 12.
  A label goes below a point that is a local low so it never crosses the line, and
  tick labels thin out to every second or third point when they would collide.
- **Scatter** labels every point up to 20, otherwise the four most extreme, and
  always the highlighted ones.
- **Legend**: shown at the top for two or more series, with round swatches and no
  title (the subtitle names the measure). A single series has no legend.
- **Axis ticks** use the same number format as the labels (`$20K`, `35%`), with
  thousands separators and round values.

## Smallest sizes

Nothing is drawn smaller than 12 px CSS (24 px in the PNG). At thumbnail size only
the title and the emphasised mark remain legible, which is why the title states the
takeaway and only one thing is emphasised.

## Headline figures

- A hero figure is at least 48 px in the theme's numeric face; on a `stat` card it
  is about 17% of the card's short side. Digits are proportional, not tabular, so a
  number like `121` does not look spaced out.
- `hero` on any recipe places the figure under the subtitle with its label beside
  it on the same baseline, plus an optional signed `delta` in the theme's positive
  or negative colour.
- The donut puts the hero in its hole and leaves out the inline block.
