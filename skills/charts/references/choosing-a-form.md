# Choosing a form

Pick the form first, before colour, size or wording. Ask what the reader has to
*do* with the numbers (compare, rank, follow over time, see a share, spot an
outlier) and choose the recipe that makes that task effortless. The output is a
still image: nobody can hover, filter or open the table behind it, so every value
the reader needs has to be on the card or in your reply.

## First: does this need a chart?

Often the honest answer is no.

- **A single number**, possibly with its recent trend: a `stat` card. A chart with
  one bar adds nothing the number does not already say.
- **Three or four headline figures**: a few `stat` cards, or one card plus a small
  table in your reply.
- **A long list where every row matters** (more than about 25): put the full table
  in the reply and, if a picture helps, chart the top items with the rest folded
  into "Other".
- **Many categories that each need their own colour** (more than about seven): a
  table, optionally beside a chart of the few that matter.

## Matching the task to a recipe

**Comparing sizes across categories.** `bar`, horizontal and sorted largest first.
Switch to `column` when there are six or fewer short names, or when the categories
have a natural left-to-right order (months, pipeline stages).

**One category against the rest.** `bar` with `highlight` naming it: that bar
takes the theme's emphasis colour and the others turn gray.

**A ranked or staged scale** (tiers, funnel steps, age bands). `column` or `bar`
with `ordinal: true`, which keeps your order and shades the bars light to dark.

**Change over time.** `line` for one to five series; `area` for a single series
when the filled volume is the point. If one series is the story, give it
`role: "emphasis"` and let the others recede.

**How a whole splits up, per category.** `stacked_bar` (horizontal, so long names
fit). **Two or three measures side by side per category:** `grouped_bar`.

**Before and after for each item.** `dumbbell`.

**A share of one whole at a glance.** `donut`, at most six slices and only when the
parts are clearly unequal; the total sits in the hole. Close shares (28% against
31%) cannot be read from angles; use `bar`.

**How raw observations spread out.** `histogram`.

**A value over a two-way grid** (weekday by hour, region by product). `heatmap`.

**Two measures against each other.** `scatter`, with at most three colour groups
and labels on the points the reader should notice. More groups cannot be coloured
safely because any two points may sit side by side; fold them to three or facet
them in the raw Vega-Lite tier.

**Positive and negative values around a baseline.** `column` (the zero line is
drawn), or `line` with `value_axis.min`.

## Sorting and orientation

Recipes sort bars from largest to smallest unless the order carries meaning; pass
`ordinal: true` or `sort: "none"` to keep yours. Lines and areas follow their
x-axis and are never sorted. Horizontal bars are the default because names read
at full length and the value sits at the end of each bar.

## How many series

Every extra colour costs the reader attention, and past a handful the colours stop
being distinguishable for people with colour-vision deficiency.

- **One series:** one colour, no legend (the title says what it is), every bar
  labelled.
- **Two or three:** colour carries them comfortably; a legend plus labels at the
  ends or totals.
- **Four:** the legend and direct labels both become necessary.
- **Five or six:** workable but crowded. Usually better as one emphasised series
  against gray context, or as small multiples in the raw Vega-Lite tier.
- **Seven or eight:** the limit. The script refuses more; group the tail into
  "Other" or split into facets. Never invent extra hues to make room.

## Labels on a still image

- Label what the reader will ask about: each bar of a single-series chart, the
  last point of each line, the total of each stack. `labels: "auto"` does this.
- When two line-end labels would overlap, `auto` drops them in favour of the
  legend. That is deliberate; add an annotation for the one value that matters.
- A `bar` holds about 25 categories comfortably. Beyond that, chart the top ones
  plus "Other" and give the full list as a table in your reply.
