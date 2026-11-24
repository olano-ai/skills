---
name: brand-kit
description: "Set up or read the brand kit — the visual and voice identity that every graphic, post and campaign is built from. Use this skill whenever the user mentions 'brand kit,' 'brand colors,' 'brand colours,' 'brand palette,' 'our fonts,' 'brand fonts,' 'typography,' 'logo,' 'design tokens,' 'style guide,' 'brand guidelines,' 'visual identity,' 'tone of voice,' 'brand voice,' 'how we sound,' 'on-brand,' or 'off-brand.' Use it BEFORE producing any social graphic, carousel, post or campaign, so the output uses real colours, real fonts and a real voice instead of invented ones. Also use it when a user says an asset looks generic, off-brand, or 'not like us.' For product positioning, ICP and competitive context, see product-marketing — this skill deliberately does not duplicate those."
---

# Brand Kit

A brand kit is the difference between "an AI made this" and "our team made this."
Without one, every generated post invents a palette, reaches for a default
sans-serif, and writes in the same cheerful nowhere-voice. With one, the
composer has hex values to fill and font files to load, and the writer has
sentences to sound like.

This skill owns the **visual and voice identity**. It does not own positioning,
ICP, competitors or proof points — `product-marketing` owns those in
`.agents/product-marketing.md`, and the two are designed to sit side by side.
When both exist, read both.

## Where it lives

```
<workspace>/brand/
  tokens.json     # machine-readable: palette, fonts, spacing, logo paths
  voice.md        # on-voice / off-voice sentence pairs
  do-not-say.md   # banned words, claims that need legal, competitor rules
  logo/           # logo.svg, logo-light.png, logo-dark.png, mark.svg
  fonts/          # any .ttf/.woff2 the brand owns
```

`tokens.json` is the contract. `social-image-composer` reads it to build HTML,
`content-humanizer` reads `voice.md` and `do-not-say.md`, and any skill that
produces something a customer will see should read all three.

## Reading an existing kit

Check `<workspace>/brand/tokens.json` first. If it exists, read it plus
`voice.md` and `do-not-say.md`, and use those values — do not re-derive colours
from a screenshot or invent a font. Report what you loaded in one line
("Brand kit: Acme, 4 colours, Inter/Söhne, logo present") so the user can see
which identity is in play before you spend a turn on the wrong one.

If `tokens.json` is missing, say so and offer to build one — do not silently
proceed with invented colours. A graphic in the wrong blue is worse than a
graphic that waited a minute.

## Building a kit

### Step 1 — Find what already exists

Ask for the fastest source in this order, and stop at the first one that lands:

1. **An existing brand guideline** (PDF, Figma export, a `styles.css`, a
   Tailwind config). Read it and extract values directly.
2. **A live site.** Fetch it and pull the computed palette and font stack — the
   real values beat anyone's memory of them.
3. **A logo file plus two or three sentences.** Enough to derive a palette.
4. **Nothing.** Then interview, using Step 2.

Never guess a hex value you were not given or did not read. `#0A66C2` is
LinkedIn's blue, not the user's.

### Step 2 — Capture the palette

Four to six colours, each with a **role**, not just a name. The role is what
makes a token usable: a composer needs to know which colour is the page
background and which is the one thing on the slide that should catch the eye.

| Role | What it does | How many |
|---|---|---|
| `background` | The dominant field behind everything | 1 |
| `surface` | Cards, panels, quote blocks sitting on the background | 0–1 |
| `text` | Body copy on `background`. Must clear 4.5:1 against it | 1 |
| `accent` | The single colour that draws the eye — CTA, key stat, underline | 1 |
| `muted` | Secondary text, captions, dividers. 3:1 minimum | 0–1 |

Check contrast as you go and say the number. A palette that fails on a phone in
sunlight is a palette that fails.

If the brand has a dark and a light treatment, capture both as `light` and
`dark` blocks — social platforms show graphics against both.

### Step 3 — Capture typography

Two faces at most: a **display** face for headlines and a **body** face for
everything else. One face used at two weights is also a complete answer.

For each, record the CSS family name, a real fallback stack, and — this is the
part people forget — **a file path if the font is not a system font**. A token
naming "Söhne" with no file renders as Helvetica on the rendering box and
nobody notices until the post is live.

Fonts already on every Olano box live in the bundled `canvas-design` skill's
`canvas-fonts/` directory (Big Shoulders, IBM Plex Serif/Mono, Instrument
Sans/Serif, JetBrains Mono, Lora, Work Sans, Outfit, Crimson Pro, Young Serif,
Gloock and ~19 more, all SIL Open Font License). If the brand has no licensed
font of its own, pick from there and record the absolute path — it costs
nothing and it will always be present.

Record the type scale too: headline, subhead, body, caption in px at the
canvas's logical size (see `references/tokens-schema.md`).

### Step 4 — Capture the voice

This is the section that decides whether the copy sounds like a person. Write
`voice.md` as **paired examples**, not adjectives. "Professional but warm" tells
a model nothing; two sentences do.

```markdown
## On voice
"We shipped it Tuesday. It broke Wednesday. Here's what we changed."
"Three things we got wrong about onboarding — and the one that cost us 40% of signups."

## Off voice
"We're thrilled to announce an exciting new milestone in our journey!"
"In today's fast-paced digital landscape, onboarding is more important than ever."
```

Six to ten pairs beats a paragraph of description. Pull the on-voice ones from
things the user actually wrote — a real email, a Slack message, a past post that
worked. If `product-marketing` has already captured tone and personality
adjectives, use them to *pick* examples, not to replace them.

Then write `do-not-say.md`: words the brand never uses, claims that need legal
review before they go out, competitor-naming rules, and any regulated language.
Keep it short and specific enough to check against mechanically.

### Step 5 — Write the files

Write `tokens.json` to the schema in `references/tokens-schema.md`, then
`voice.md` and `do-not-say.md`. Copy any logo and font files the user supplies
into `brand/logo/` and `brand/fonts/` and reference them by path in the tokens —
relative paths resolve against the workspace when a renderer loads them.

Finish by rendering one proof: a single 1080×1080 card using every token, via
`social-image-composer`. Looking at it is how the user catches a wrong hex in
ten seconds instead of after ten posts.

## Keeping it current

A brand kit drifts. When a user corrects a colour, rejects a headline as
off-voice, or supplies a new logo, write the correction back into the files
rather than remembering it for one turn. Bump `version` and add a line to
`changelog` in `tokens.json` on any substantive change, so there is a record of
what moved and when.

## Reference files

- `references/tokens-schema.md` — the full `tokens.json` schema with a worked
  example. Read it before writing or editing the file.
