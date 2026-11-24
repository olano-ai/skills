# Colour and palette

Never pick chart colours by eye. Use the colours from a theme, and check any new
colour with the validator before it reaches a chart. The shipped themes all pass.

## What colour is used for

Each colour on a chart does one of these things.

- **Telling series apart (categorical).** The theme's eight colours, always used in
  their listed order and never reused within a chart. Recipes apply them when you
  pass several `series`.
- **Showing an order (ordinal).** One hue in steps from light to dark, for stages,
  tiers or bands. Use `"ordinal": true` on a single series.
- **Showing an amount (sequential).** One hue whose darkness follows the value
  (reversed on a dark background). Used by `heatmap`.
- **Pointing at one thing (emphasis).** The accent colour for the thing that
  matters, a neutral gray for everything else. Use `highlight` or
  `role: "emphasis"`.

How to tell categorical from ordinal: if reordering the categories would change
what the chart says (stages, size bands, age groups), they are ordinal. If not
(products, teams, countries), every bar takes the same first colour, because the
bar length already shows the value.

## What the validator checks

`scripts/validate_palette.py` (also reachable as `chart.py validate-palette`) is
Olano's own checker. For a categorical palette it reports:

- **Lightness band.** Each colour's OKLCH lightness is within 0.43 to 0.77 on a
  light background, 0.48 to 0.67 on a dark one, so no series fades into the
  background or overpowers the rest.
- **Chroma floor.** Each colour has OKLCH chroma of at least 0.10; below that it
  looks gray.
- **Contrast against the background.** At least 3:1 (the WCAG level for graphics).
  Between 2:1 and 3:1 is reported as `RELIEF`: acceptable only because the marks
  also carry direct labels, which the recipes always draw. Under 2:1 fails.
- **Normal-vision separation.** The closest pair of neighbouring colours is at
  least 15 apart (OKLab distance × 100).
- **Colour-blind separation.** The same pairs, simulated for protanopia and
  deuteranopia with the Machado, Oliveira & Fernandes (2009) model, stay at least
  8 apart. Between 6 and 8 is reported as `FLOOR`: usable with direct labels.

For an ordinal ramp (`--ordinal`) it checks instead that lightness changes in one
direction, that neighbouring steps differ by at least 0.06 in lightness, and that
the faintest step reaches 2:1 against the background.

Two things the validator cannot check, so you must: keep the theme's colour order
(the order is what keeps neighbours apart), and take colours from a theme file
rather than typing new hex values.

Examples:

```
python3 <skill>/scripts/chart.py validate-palette "#2a78d6,#eb6834,#1baf7a" --mode light --surface "#fcfcfb"
python3 <skill>/scripts/chart.py validate-palette "#86b6ef,#5598e7,#2a78d6,#1c5cab" --mode light --ordinal
python3 <skill>/scripts/chart.py validate-palette "#3987e5,#d95926,#199e70" --mode dark --surface "#0d0d0d" --pairs all
```

`--pairs all` compares every pair instead of neighbours only. Use it for scatter
plots and small multiples, where any two colours can end up side by side; only
the first three colours of a theme pass it, which is why `scatter` allows three
groups. `chart.py themes --check` re-runs every check on the shipped themes.

## The shipped themes

In every theme, body text reaches at least 4.5:1 against the background (muted
text 3:1), and the categorical order and the emphasis colour pass the validator in
that theme's mode.

### clean (light), background `#fcfcfb`

| Token | Value |
|---|---|
| ink / secondary / muted | `#0b0b0b` / `#52514e` / `#898781` |
| grid / baseline | `#e1e0d9` / `#c3c2b7` |
| categorical | `#2a78d6` `#eb6834` `#1baf7a` `#eda100` `#e87ba4` `#008300` `#4a3aa7` `#e34948` |
| emphasis / de-emphasis | `#2a78d6` (first colour) / `#c9c8c1` |
| ordinal ramp | `#86b6ef` `#5598e7` `#2a78d6` `#1c5cab` `#104281` |
| sequential | `#cde2fb` to `#0d366b` (7 steps) |
| fonts | Instrument Sans: 700 titles, 400 body, 700 numbers |

The third, fourth and fifth colours (green, amber, pink) fall between 2:1 and 3:1
on this near-white background, so they pass on relief: the recipes label bars and
line ends, which gives every one of those marks a second cue besides colour.

### midnight (dark), background `#0d0d0d`

| Token | Value |
|---|---|
| ink / secondary / muted | `#ffffff` / `#c3c2b7` / `#8b8a84` |
| grid / baseline | `#2c2c2a` / `#383835` |
| categorical | `#3987e5` `#d95926` `#199e70` `#c98500` `#d55181` `#008300` `#9085e9` `#e66767` |
| emphasis / de-emphasis | `#c98500` (gold) / `#3a3a38` |
| ordinal ramp | `#184f95` `#256abf` `#3987e5` `#6da7ec` `#9ec5f4` |
| sequential | `#14294a` to `#cde2fb` (the dark end is closest to the background) |
| fonts | Instrument Sans for titles and body, Big Shoulders for numbers |

Every colour clears 3:1 on black (the darkest, green `#008300`, reaches 3.9:1). The
emphasis gold is deliberately muted: a brighter gold such as `#e8a93a` has OKLCH
lightness 0.78, above the dark band, and fails.

### editorial (light), background `#faf7f2`

| Token | Value |
|---|---|
| ink / secondary / muted | `#1a1a1a` / `#4a4741` / `#8a857b` |
| grid / rule | `#e6e1d8` / `#1a1a1a` |
| categorical | `#b5382d` `#1f5fa8` `#b8860b` `#7a4b9a` `#4f7d2a` `#c05a8a` `#3b4fa8` `#c9622b` |
| emphasis / de-emphasis | `#b5382d` / `#cfc9be` (context series use a warm gray ramp) |
| ordinal ramp | `#e59b91` `#d3705f` `#c14b3c` `#a12f25` `#7a2118` |
| fonts | Instrument Serif titles, Instrument Sans body, IBM Plex Mono numbers |

Plain grays fail the chroma floor, so the seven supporting colours are deep,
ink-like hues chosen by search (their closest colour-blind pair is 11.5 apart). In
emphasis mode the context series switch to the warm grays, which is the look this
theme is designed for.

## How recipes use the theme

- One series: every bar in the first colour, no legend.
- `highlight`: the named bars, slices or points in the emphasis colour, the rest in
  the de-emphasis gray.
- Several series: colours 1 to N in order, always with a legend. With
  `role: "emphasis"` on one series, that series takes the emphasis colour and the
  others take stepped grays.
- `ordinal: true`: N evenly spaced steps of the ordinal ramp, checked at that
  number of steps.
- `heatmap`: the sequential ramp, with each cell's label in white or ink depending
  on the cell's brightness.
- Text always uses an ink colour; the mark next to it carries the series colour.

## Brand colours (`--theme brand`)

Reads `brand/tokens.json` (the `brand-kit` skill's format) from the working
directory, starting from `clean` for a light brand or `midnight` for a dark one
(`--theme brand:dark` forces dark):

1. The brand background and text colours replace the theme's only if text reaches
   4.5:1 on that background; the muted colour only if it reaches 3:1. Otherwise the
   theme's values stay and a note says why.
2. The brand accent becomes the first colour and the emphasis colour only if it
   passes the lightness, chroma and contrast checks on that background *and* an
   eight-colour order exists around it that passes (the other seven are reordered to
   keep the closest neighbours as far apart as possible). If the accent passes on
   its own but no order does, it is used for emphasis only.
3. The brand's display and body font files are used only if they exist on this
   machine.

Each decision is printed to stderr as `note: …`. A brand colour that fails is not
something to work around: a readable chart in the theme's blue beats an unreadable
one in the brand's red.
