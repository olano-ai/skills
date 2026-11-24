# Recipes

A recipe is a small JSON file: the data as `categories × series`, the story as text
fields, and a few switches. `chart.py render spec.json` validates it (every error says
what to do instead), applies the design rules and writes one themed HTML card.

```
python3 <skill>/scripts/chart.py render spec.json [--theme clean|midnight|editorial|brand]
        [--size square|landscape|portrait|story|slide|email|report|WxH] [--out reports/name.html]
        [--recipe my_recipe.py] [--emit-vl] [--svg-card] [--embed-fonts]
```

`--theme` and `--size` on the command line override the file. `--emit-vl` prints the
generated Vega-Lite instead of writing HTML (hand-edit it, then `chart.py vl`).

## Common fields

| Field | Type · default | Meaning |
|---|---|---|
| `type` | one of `bar column stacked_bar grouped_bar line area dumbbell donut stat histogram heatmap scatter` | The recipe. |
| `title` | string, **required** | The takeaway. Wraps to three lines, shrinks before truncating. |
| `kicker` | string | Small uppercase label above the title. |
| `subtitle` | string | The measure and period. |
| `categories` | list of strings | The x positions / rows. Must be unique (merge "US"/"USA" first). |
| `series` | list of `{name, values, role}` · 1–8 | `values` has one number (or `null`) per category. `role`: `"emphasis"`, `"context"` or omitted. |
| `value_format` | `{kind, currency, decimals, compact}` · `number, USD, 0, true` | `kind`: `number` · `currency` · `percent` (values already in percent units). `compact` → `12.9K`, `$4.2M`. |
| `value_axis` | `{label, min, max}` | Axis title; fixed bounds (leave `null` for data-driven). |
| `category_axis` | `{label}` | Title for the category axis (rarely needed). |
| `labels` | `auto` · `none` · `extremes` · `ends` · `all` · default `auto` | Which values get a direct label. `auto` is the design rule per chart. |
| `percent_of_total` | bool · false | Append the share: `22 (35%)`. |
| `sort` | `desc` · `asc` · `none` · default `desc` (`none` when `ordinal`) | Category order by value. Lines/areas keep their order and reject `sort`. |
| `ordinal` | bool · false | Categories are an ordered scale → one-hue ramp, no re-sorting. Single series only. |
| `highlight` | list of names | Categories (or series) to paint in the emphasis colour; the rest go gray. |
| `annotations` | list of `{target, text}` · ≤ 3 | A note beside a category, series or point label. Target must exist. |
| `hero` | `{value, label, delta}` | Big number under the subtitle (`value` is a string you format yourself). Required for `stat`. `delta` is a signed string, coloured by sign. |
| `notes` | `{source, as_of, note}` | Footer: `Source: … · as of …` left; the note right or below. |
| `theme` | `clean` · `midnight` · `editorial` · `brand` · `brand:dark` | Default `clean`. |
| `size` | preset or `WxH` (320–4000) | Default `square`. |
| `logo` | file path (png/svg/jpg/webp), relative to the working directory | Drawn bottom-right, sized to the footer. |
| `orientation` | `horizontal` · `vertical` | `stacked_bar` and `grouped_bar` only. |

Type-specific: `histogram` takes `values` (raw numbers) + `bins` (int, default 20) +
`x_axis.label`; `heatmap` takes `rows`, `columns`, `matrix`; `scatter` takes `points`
(`{x, y, label?, group?}`) + `x_axis.label`. Unknown fields are refused with a suggestion.

### Validation (what the script refuses, and what it says)

9+ series → *fold the tail into 'Other' or facet* · a series with the wrong number of
values · non-finite numbers (use `null`) · `stacked_bar`/`grouped_bar` with one series
(*use bar*) · `line`/`area` with one category (*use stat*) · `area` with several series
(*use line*) · `dumbbell` without exactly two series · `donut` with more than six slices
(*use bar*) or several series · `stat` without a `hero` · a `highlight` or annotation
target that is not in the chart · more than 3 annotations · a scatter with more than 3
groups (*fold or facet*) · `ordinal` with several series · a custom size outside 320–4000.

## bar — horizontal bars (the default for categories)

```json
{"type": "bar",
 "kicker": "Customer footprint",
 "title": "The US is a third of the customer base",
 "subtitle": "Accounts by billing country · 63 total",
 "categories": ["United States", "Singapore", "China", "Spain", "France", "Germany", "United Kingdom"],
 "series": [{"name": "Accounts", "values": [22, 13, 12, 12, 1, 2, 1]}],
 "highlight": ["United States"],
 "annotations": [{"target": "United States", "text": "35% of accounts"}],
 "hero": {"value": "63", "label": "customer accounts"},
 "notes": {"source": "Salesforce", "as_of": "2026-09-06", "note": "3 accounts have no billing country and are not shown."}}
```

Sorted by value; one hue; the highlighted bar in the emphasis colour with a bold label;
values outside the tips (the tail is short), so the value axis is dropped.

## column — vertical bars

```json
{"type": "column", "kicker": "Hiring funnel",
 "title": "Nine in ten applicants never reach a first interview",
 "subtitle": "Candidates per stage, engineering roles, H1 2026",
 "categories": ["Applied", "Screened", "Interview 1", "Interview 2", "Offer", "Hired"],
 "series": [{"name": "Candidates", "values": [2840, 612, 268, 121, 44, 31]}],
 "ordinal": true,
 "annotations": [{"target": "Hired", "text": "1.1% of applicants"}],
 "notes": {"source": "Greenhouse", "as_of": "2026-07-01"}}
```

`ordinal: true` keeps the stage order and paints a light→dark ramp of one hue.

## stacked_bar — part-to-whole per category

```json
{"type": "stacked_bar", "kicker": "Revenue mix",
 "title": "Platform now brings in more than half of every region's revenue",
 "subtitle": "FY2025 revenue by region and product line, $M",
 "categories": ["North America", "Europe", "Asia-Pacific", "Latin America", "Middle East & Africa"],
 "series": [{"name": "Platform", "values": [48.2, 31.5, 22.9, 9.4, 4.1], "role": "emphasis"},
            {"name": "Services", "values": [21.0, 14.2, 9.8, 5.1, 2.6]},
            {"name": "Hardware", "values": [12.4, 8.9, 11.2, 3.0, 1.9]}],
 "value_format": {"kind": "currency", "currency": "USD", "decimals": 1, "compact": false},
 "notes": {"source": "Finance data warehouse", "as_of": "2026-01-15"}}
```

Sorted by total; segment values inside when they fit, totals at the tip; legend on top;
`"orientation": "vertical"` for columns.

## grouped_bar — series side by side

```json
{"type": "grouped_bar", "kicker": "Support load",
 "title": "Chat overtook email as the busiest support channel this quarter",
 "subtitle": "Tickets per channel, Q1 vs Q2 2026",
 "categories": ["Chat", "Email", "Phone", "Community", "Social"],
 "series": [{"name": "Q1 2026", "values": [3120, 4210, 1830, 640, 410]},
            {"name": "Q2 2026", "values": [4890, 3960, 1710, 920, 530], "role": "emphasis"}],
 "annotations": [{"target": "Chat", "text": "+57% quarter on quarter"}],
 "notes": {"source": "Zendesk", "as_of": "2026-07-01", "note": "Q2 is a partial quarter through 30 June."}}
```

Sorted by the emphasis series; every bar labelled while there are ≤ 16 bars.

## line — trend, one line per series

```json
{"type": "line", "kicker": "Product usage",
 "title": "Web usage doubled in a year while mobile stayed flat",
 "subtitle": "Weekly active users by platform, monthly average, 2025–26",
 "categories": ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
 "series": [{"name": "Web", "values": [41200, 43800, 47100, 45900, 52300, 56800, 61400, 66200, 71900, 75300, 79800, 84100], "role": "emphasis"},
            {"name": "iOS", "values": [22100, 22800, 23400, 22900, 23600, 24100, 24800, 25200, 25100, 25600, 26000, 26300]},
            {"name": "Android", "values": [15400, 15900, 16200, 15800, 16400, 16900, 17300, 17600, 17900, 18200, 18400, 18700]}],
 "value_axis": {"min": 0},
 "annotations": [{"target": "Mar", "text": "New editor launched"}],
 "notes": {"source": "Product analytics (Amplitude)", "as_of": "2026-09-01"}}
```

End labels `Name · value`; legend on top; an annotation on a category lands on the
emphasis series at that point. `labels: "extremes"` marks each series' high and low.

## area — one series with a wash

```json
{"type": "area", "kicker": "Cloud spend",
 "title": "Monthly cloud spend has tripled since January",
 "subtitle": "Total infrastructure cost per month, 2026",
 "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
 "series": [{"name": "Spend", "values": [41200, 45800, 52300, 61900, 74600, 88200, 104900, 123800]}],
 "value_format": {"kind": "currency", "currency": "USD", "decimals": 0, "compact": true},
 "labels": "ends",
 "annotations": [{"target": "May", "text": "GPU cluster added"}],
 "notes": {"source": "AWS Cost Explorer", "as_of": "2026-09-01"}}
```

## dumbbell — before → after per item

```json
{"type": "dumbbell", "kicker": "Onboarding redesign",
 "title": "Time to first value fell by more than a third for every team",
 "subtitle": "Median days from signup to first published project, before vs after the redesign",
 "categories": ["Marketing", "Sales", "Engineering", "Design", "Finance", "Operations"],
 "series": [{"name": "Before (Q4 2025)", "values": [9.5, 8.1, 6.4, 7.2, 12.3, 10.8]},
            {"name": "After (Q2 2026)", "values": [5.2, 4.9, 3.8, 4.1, 7.6, 6.9]}],
 "value_format": {"kind": "number", "decimals": 1, "compact": false},
 "annotations": [{"target": "Finance", "text": "Largest absolute gain"}],
 "notes": {"source": "Product analytics", "as_of": "2026-07-14"}}
```

The second series is "after" (slot 1, bold label); sorted by the after value.

## donut — part-to-whole at a glance (≤ 6 slices)

```json
{"type": "donut", "kicker": "Pipeline",
 "title": "Half the open pipeline is still at the qualification stage",
 "subtitle": "Open opportunities by stage, count",
 "categories": ["Qualification", "Discovery", "Proposal", "Negotiation", "Closing"],
 "series": [{"name": "Opportunities", "values": [128, 61, 38, 19, 12]}],
 "percent_of_total": true,
 "highlight": ["Qualification"],
 "hero": {"value": "258", "label": "open deals"},
 "notes": {"source": "HubSpot", "as_of": "2026-09-05"}}
```

Labels outside each slice (name over value); the hero sits in the hole. Annotations
become captions under the chart.

## stat — the number is the chart

```json
{"type": "stat", "kicker": "Annual recurring revenue",
 "title": "ARR crossed $4M with expansion outpacing new logos for the first time",
 "subtitle": "Monthly ARR, trailing 12 months",
 "categories": ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
 "series": [{"name": "ARR", "values": [2.71, 2.84, 2.95, 3.02, 3.18, 3.31, 3.42, 3.55, 3.71, 3.86, 4.02, 4.21]}],
 "hero": {"value": "$4.21M", "label": "ARR at end of August 2026", "delta": "+55% year on year"},
 "notes": {"source": "Billing system", "as_of": "2026-09-01"}}
```

`categories` + one `series` are optional — they draw a sparkline (gray line, last point
in the emphasis colour). Without them the card is the hero, the title and the footer.

## histogram — distribution of raw values

```json
{"type": "histogram", "kicker": "Deal sizes",
 "title": "Most deals close under $20K, but a long tail carries the revenue",
 "subtitle": "Closed-won deal value, FY2025 · 60 deals",
 "values": [4.2, 6.1, 7.8, 9.1, 12.3, 14.8, 17.3, 19.6, 22.5, 27.5, 34.0, 43.8, 57.9, 78.1, 107.2, 147.5],
 "bins": 12,
 "value_format": {"kind": "currency", "currency": "USD", "decimals": 0, "compact": true},
 "x_axis": {"label": "Deal value, $K"},
 "value_axis": {"label": "Deals"},
 "notes": {"source": "CRM export", "as_of": "2026-01-31"}}
```

Bins are snapped to 1/2/2.5/5 × 10ⁿ near the requested count; counts on the caps while
there are ≤ 12 bins. `value_format` formats the bin edges; `value_axis.label` titles the
count axis (shown when caps are unlabelled).

## heatmap — magnitude over a grid

```json
{"type": "heatmap", "kicker": "Support demand",
 "title": "Tuesday and Wednesday mornings are the crunch — staff them first",
 "subtitle": "Tickets opened per hour band, average week, Q2 2026",
 "rows": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
 "columns": ["6–9", "9–12", "12–15", "15–18", "18–21", "21–24"],
 "matrix": [[18, 64, 52, 41, 22, 9], [21, 88, 71, 47, 25, 10], [23, 91, 69, 45, 24, 11],
            [19, 72, 58, 43, 21, 8], [16, 55, 44, 30, 15, 6], [5, 14, 17, 12, 8, 4], [4, 9, 11, 10, 7, 3]],
 "value_axis": {"label": "Tickets per hour band"},
 "highlight": ["Tue", "Wed"],
 "notes": {"source": "Zendesk", "as_of": "2026-07-01"}}
```

Rows and columns keep their order; `highlight` bolds row/column headers; `null` cells
are drawn in the grid colour; the gradient legend sits under the grid.

## scatter — two measures per point

```json
{"type": "scatter", "kicker": "Account health",
 "title": "The accounts that use the API most are also the ones expanding",
 "subtitle": "Monthly API calls vs net revenue retention, top 18 accounts",
 "points": [{"x": 1.2, "y": 96, "label": "Acme", "group": "Enterprise"},
            {"x": 0.8, "y": 91, "label": "Umbrella", "group": "Mid-market"},
            {"x": 7.1, "y": 138, "label": "Weyland", "group": "Enterprise"}],
 "value_format": {"kind": "percent", "decimals": 0},
 "x_axis": {"label": "API calls per month, millions"},
 "value_axis": {"label": "Net revenue retention"},
 "annotations": [{"target": "Weyland", "text": "Largest expansion"}],
 "notes": {"source": "Billing + API gateway logs", "as_of": "2026-08-31"}}
```

`group` colours points (≤ 3 groups, legend on top); `highlight` names point labels or a
group; labels on every point up to 20, then the four extremes.

## Forking a recipe

Copy `scripts/olano_chart/recipes/bar.py` (or any other) to `scratch/my_recipe.py`, edit
`build(spec, theme)` — it receives the validated recipe (`spec.categories`, `spec.series`,
`spec.layout.chart` for the box size, `spec.layout.scale` for the type scale) and the theme
(`theme.tokens`, `theme.stack("body")`) and returns a Vega-Lite dict without `$schema`,
`config`, `width` or `height` — then run `render spec.json --recipe scratch/my_recipe.py`.
Optional module attributes: `SUPPORTS_ANNOTATIONS`, `PLACES_HERO`, `preferred_height(spec,
scale, chart_w)`, `has_chart(spec)`.
