# Story and style

Decide what the chart says before you build it. The text fields of a recipe tell
the story; the marks are the evidence for it. If the chart needs a paragraph of
explanation, change the chart.

## The text fields

- **`kicker`**: the topic, in two or three words ("Customer footprint",
  "Q2 pipeline"). Not a sentence.
- **`title`**: the conclusion, as one sentence the chart can be checked against.
  The largest text on the card.
- **`subtitle`**: what was measured, the unit and the period ("Accounts by billing
  country · 63 total").
- **`hero`**: one figure, only when the point is a single number:
  `{"value": "63", "label": "customer accounts"}`.
- **`highlight`** or **`role: "emphasis"`**: the one or two things the chart is
  about; everything else turns gray.
- **`annotations`**: a short fact next to the highlighted mark ("35% of accounts",
  "new editor launched"). Three at most.
- **`notes.source`** and **`notes.as_of`**: always set. "Salesforce" and
  "2026-09-06" print as `Source: Salesforce · as of 2026-09-06`.
- **`notes.note`**: anything left out or merged ("3 accounts have no billing
  country and are not shown.").

## Writing the title

State the finding, not the axes. Some rewrites:

- "Accounts by country" → "The US is a third of the customer base"
- "Weekly active users, 2025–26" → "Web usage doubled in a year while mobile stayed flat"
- "Revenue by region and product" → "Platform brings in more than half of every region's revenue"
- "Support tickets per channel" → "Chat overtook email as the busiest support channel this quarter"

Useful shapes: a share ("X is a third of Y"), a change ("X doubled", "X fell by a
third", "X overtook Y"), a majority with an exception ("most X are Y, but…"), or a
recommendation ("X is the bottleneck; fix Y first"). Aim for twelve words or fewer.
The frame wraps a title to at most three lines and shrinks the type before it would
cut anything off. Units and dates go in the subtitle.

## Emphasis

Emphasise one thing. On a single-series chart, `highlight: ["United States"]` paints
that bar in the theme's emphasis colour and the rest in the de-emphasis gray; its
name turns bold and its value label stays dark while the others go to the secondary
colour. With several series, `"role": "emphasis"` on one of them does the same for
lines and stacks, and the other series get different grays so the legend still
separates them. Emphasising two things turns the chart into a comparison;
emphasising three is just a categorical chart.

## Annotation

Attach one note to the emphasised thing and write it as a fact: "35% of accounts",
"+57% quarter on quarter", "GPU cluster added". Bars put it beside the value label,
columns above the bar, lines beside the point on the side away from the line.
Charts with nowhere to put a note next to a mark (donut, heatmap, histogram, stat)
show it as a caption under the chart.

## Number formats

`value_format` sets how every value on the card is written. For example,
`{"kind": "currency", "currency": "USD", "decimals": 1, "compact": true}` gives
`$4.2M`, `$12.9K`, `$860`, and `compact: false` gives `$4,210,000`. With
`"kind": "percent"` the values are already percentages (`35` prints as `35%`).
`percent_of_total: true` adds each value's share, as in `22 (35%)`. Axis ticks
follow the same format. Hero values are strings, so write them exactly as they
should appear (`"$4.21M"`).

## Choosing size and theme for where it goes

- **Chat reply**: readable on a phone at a glance. `landscape`, clean.
- **Email or newsletter**: wide and short, light background. `email`, clean.
- **LinkedIn**: a big takeaway and one emphasised mark; dark backgrounds work well.
  `square` or `portrait`, midnight or clean.
- **X**: wide and high contrast. `landscape`, midnight.
- **Instagram**: square or 4:5 in the feed; stories keep the top and bottom clear.
  `square` or `story`, midnight.
- **A slide**: match the deck; the title is the slide's claim. `slide`, the deck's
  theme.
- **A report or print**: warm paper, a serif title, thin rules. `report`, editorial.

## What good looks like

Restraint. One message, large and clear, and everything else in the background. The
exact numbers sit where the eye lands. Margins are generous and nothing touches an
edge. Colours come from a checked palette. The test: after two seconds, can the
reader repeat the title? Bright colours everywhere, gradients, shadows, 3-D, a value
on every point, or eight colours for a one-number story all make a chart look
amateurish.
