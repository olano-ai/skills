---
name: content-humanizer
description: "Rewrite AI-sounding copy so it reads like a specific person wrote it, and check a draft against the brand's voice profile before it ships. Use this skill whenever the user says a draft 'sounds like AI,' 'sounds generic,' 'sounds corporate,' 'is too formal,' 'doesn't sound like me,' or asks to 'humanize,' 'de-AI,' 'make it sound human,' 'remove the em dashes,' 'strip the AI tells,' or 'match our voice.' Apply it as a final pass on any social post, caption, newsletter, landing page or announcement before publishing or filing for approval, even when the user did not ask — copy that reads as machine-written costs reach and trust. Reads brand/voice.md and brand/do-not-say.md when they exist."
---

# Content Humanizer

Readers spot machine-written copy in about a sentence, and once they have, they
stop reading. The tells are consistent and mostly mechanical, which is what
makes this fixable: it is closer to editing than to rewriting.

Two passes. **Strip the tells**, then **match the voice**. The first is generic
and always applies. The second needs a voice profile and is what turns "not
obviously AI" into "obviously us."

## Pass 1 — Strip the tells

### Opening moves that give it away

| Tell | Replace with |
|---|---|
| "In today's fast-paced digital landscape…" | The specific thing that happened |
| "We're thrilled/excited to announce…" | What it is and who it is for |
| "Let's dive in." / "Let's explore." | The first actual point |
| "In this post, I'll share…" | Sharing it |
| A rhetorical question as the first line | A statement worth arguing with |

### Vocabulary that reads as generated

Delve · leverage (as a verb) · utilize · robust · seamless · seamlessly ·
elevate · unlock · harness · navigate (figuratively) · landscape (figuratively) ·
realm · tapestry · testament · underscore · pivotal · crucial · vital ·
comprehensive · holistic · myriad · plethora · game-changer · cutting-edge ·
state-of-the-art · empower · foster · embark · journey (figuratively) ·
ever-evolving · fast-paced · unprecedented · transformative · synergy ·
resonate · curated · bespoke · meticulous · profound.

None of these is banned outright — "crucial" is a real word. The signal is
*density*. Three in a paragraph is the tell.

### Structural tells

- **"It's not just X, it's Y."** And its family: "This isn't about X. It's about
  Y." One per piece at most; ideally none.
- **Tricolon everywhere.** Three-item lists in every sentence. Vary to one, two,
  four.
- **Every paragraph the same length.** Real writing has a one-line paragraph
  after a long one.
- **The summarising close.** "In conclusion," "Ultimately," "At the end of the
  day," or a paragraph restating what was just said. Stop at the last real
  point.
- **Bolding the first phrase of every bullet.** A formatting habit, not emphasis.
- **Em dashes as the default connector.** Not because em dashes are wrong — they
  are not — but because one per paragraph across a whole piece is a fingerprint.
  Keep the ones doing work; make the rest commas, colons or full stops.
- **Hedging stacked on hedging.** "It's worth noting that it may potentially be
  somewhat beneficial." Say it or cut it.
- **Emoji as section markers.** 🚀 ✨ 💡 opening bullets.

### What to put back

Stripping tells leaves copy that is clean and still lifeless. The things that
make it read human:

- **A specific number, name, date or place.** "94 applications, 3 replies" beats
  "many applications, few replies." Never invent one — ask if you do not have it.
- **A concrete moment.** "Tuesday, 9pm, about to hit send" beats "a difficult
  career decision."
- **An admission.** What went wrong, what surprised you, what you got wrong for
  years. Machines write about successes.
- **A position someone could disagree with.** Balanced copy is forgettable copy.
- **Rhythm.** A short sentence after a long one. A fragment. Like that.
- **Plain verbs.** Use, not utilize. Help, not empower. Start, not embark on.

## Pass 2 — Match the voice

Read `<workspace>/brand/voice.md` and `<workspace>/brand/do-not-say.md`. If
they do not exist, generic de-AI-ing is all that is available — say so, and offer
to build a voice profile with `brand-kit`, because that is what makes the
difference between "not AI" and "us."

With a profile:

1. **Read the on-voice examples first**, then the draft. The mismatch is usually
   immediate and specific — the examples are terse and the draft is padded, or
   the examples take positions and the draft explains.
2. **Rewrite toward the examples**, not toward "good writing." A brand that
   writes in fragments should keep writing in fragments.
3. **Check `do-not-say.md`** literally. Banned words, claims needing legal
   review, competitor-naming rules. This is a checklist, not a judgement call.
4. **Read the result against the off-voice examples.** If it could plausibly sit
   in that list, it is not done.

## Working with the user's own words

The single highest-leverage move: ask for something they actually wrote — a
Slack message, an email, an old post that worked — and edit *that* toward the
draft's content, rather than editing the draft toward a voice. It preserves
idiosyncrasies no profile captures: how they open, whether they use contractions,
how long their sentences run, the joke they always make.

When a user corrects your rewrite, that correction is voice data. Offer to add it
to `brand/voice.md` as a new on-voice/off-voice pair so the next draft starts
closer.

## What not to do

**Do not add errors to seem human.** Deliberate typos, broken grammar and forced
slang read as sloppy, not authentic.

**Do not manufacture specifics.** If the draft needs a number and there is not
one, ask. Inventing "we grew 3x" to make copy land is fabrication, and it is the
one failure here that does real damage.

**Do not flatten expertise.** Humanizing is not dumbing down. A technical reader
wants the precise term; the fix is to stop *padding* around it.

**Do not strip a voice that is genuinely formal.** A legal or medical brand
writing carefully is on-voice. Match the profile, not a generic idea of casual.

## Delivering the pass

Return the rewritten copy first — that is what the user needs. Then, briefly,
what changed and why: the two or three tells that mattered most, and anything you
could not fix without information you do not have ("this needs a real number in
the second line"). Skip a full diff unless asked; a list of thirty edits buries
the three that count.
