# Anti-patterns

Before you hand a chart over, look for these. Each one is a reason to fix and
re-render, not a matter of taste.

## Encoding mistakes

- **Two value axes on one plot.** A second y-scale lets any two lines appear to move
  together. Use two cards, small multiples, or index both series to 100 at the
  start and plot them on one axis.
- **Colouring nominal bars by size.** Products, teams and countries get one colour;
  the bar length already shows the size. Shading is for ordered categories
  (`ordinal: true`).
- **A rainbow for magnitude.** Amounts are shown with one hue going from light to
  dark, never a spectrum.
- **Inventing a ninth colour.** Extra hues collapse into existing ones for
  colour-blind readers. The script stops at eight; fold the tail into "Other".
- **Judging colour-blind safety by eye.** Run `chart.py validate-palette` on any
  new palette instead.
- **Red and green as plain series colours.** They read as bad and good. Use status
  colours only when the series really are good and bad.

## Choosing the wrong form

- **Many colours when the point is one number.** If the message is "this one went
  up", use emphasis or a `stat` card, not a full categorical chart.
- **One bar, or a pie with two slices.** The number alone is clearer: `stat`.
- **A donut for similar shares.** Angles of 28% and 31% look the same; use `bar`.
- **More than about seven categories that each need a colour.** Give a table.
- **A spreadsheet when someone asked for a chart.** They want an image they can
  paste into a post or a deck, not a file with a chart tab.

## Visual noise

- **Heavy marks and gridlines with no space around them.** Keep marks slim, grids
  faint and margins generous.
- **Dashed gridlines or axes.** Dashes suggest a forecast or a threshold. Keep
  rules solid and thin.
- **A value on every point.** Nobody reads them. Label ends, extremes and the one
  series that matters; the axis covers the rest.
- **Outlines around marks.** The recipes separate touching marks with a thin gap
  in the background colour instead.
- **Labels squeezed into marks too small for them.** Put the label outside the
  bar, or leave it off.
- **Text in the series colour.** A yellow value on a pale background disappears.
  Text uses the theme's ink colours; the coloured mark next to it identifies it.
- **A decorative face on the headline number.** The hero figure uses the theme's
  numeric face; only the editorial theme sets its title in a serif.
- **Gradients, shadows, background bands, 3-D, rounding everything.** These make a
  chart look machine-made. Keep the surface flat and use one accent.
- **Anything touching the edge of the card.** If text reaches the edge, the title
  is too long or a hand-written spec ignored the margins.

## Producing the file

- **Placing labels by hand-typed coordinates.** They break the moment the data or
  the size changes. Use the recipe switches (`labels`, `annotations`) or the
  Vega-Lite layer patterns, and let Vega measure the text.
- **Installing a plotting library or a font.** Everything needed is bundled, and the
  sandbox may have no package index. A chart that depends on an install breaks on
  the next machine.
- **Using `image_generate` for data.** A generated picture makes up numbers and
  misspells labels. At most it is a background layer under a real chart.
- **Leaving copies behind.** One HTML file and one PNG per chart in `reports/`,
  re-rendered in place; no `final_v2` beside `final`.
- **Saying an image "should appear".** The file path is the deliverable: write
  `Saved: <path>` and attach the PNG where the channel can show images.
- **Critiquing in circles.** One `image_describe` pass against the checklist, at
  most one re-render, then ask the person.
- **Rendering variants nobody asked for.** Offer the dark, wide or slide version;
  do not post four images unprompted.
- **Letting the chart contradict the table.** The table in your reply is the
  source of truth. If they disagree, the chart is the one to fix.
