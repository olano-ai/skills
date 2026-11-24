---
name: social-campaign
description: "Run a social campaign end to end — brief, research, per-platform drafts, visuals, review and approval — producing one reviewable bundle on disk instead of scattered chat messages. Use this skill whenever the user asks to 'run a campaign,' 'launch this,' 'announce this,' 'promote this,' 'post about this everywhere,' 'write posts for LinkedIn and X,' 'do a content push,' 'plan a week of content,' or wants one piece of news adapted across several platforms with graphics. Also use it whenever something is about to be published to a real audience, because it is what puts a human approval gate in front of publishing. For a single post with no visuals, the social skill alone is enough."
---

# Social Campaign

One announcement becomes a LinkedIn post, an X thread, a Facebook post, two
graphics and a schedule. Done in chat, that is fifteen messages nobody can
review as a whole, and the version that gets published is whichever one someone
scrolled back to. Done as a campaign, it is a folder: everything in it, side by
side, reviewable in one pass, and nothing goes out until a human says so.

## The bundle

```
<workspace>/campaigns/<yyyy-mm-dd>-<slug>/
  brief.json         # goal, audience, key message, platforms, timing
  research.md        # sources, evidence, competitor angles — with links
  linkedin.md        # the draft, plus the hook variants considered
  x.md               # single post and/or thread
  facebook.md
  visual-brief.md    # what each graphic must show and why
  cards/             # the HTML sources for the graphics
  renders/           # the finished PNG/PDF assets
  approval.json      # status, who approved, when, what was approved
```

One folder per campaign, named by date so they sort. Everything is a file
because a file can be reviewed, corrected, re-rendered and pointed at six weeks
later — none of which chat scrollback supports.

## Order of work

### 1. Load context before writing anything

Read, in this order:

- `<workspace>/brand/tokens.json`, `voice.md`, `do-not-say.md` — via `brand-kit`
- `.agents/product-marketing.md` — via `product-marketing`

If neither exists, stop and set them up first. A campaign written without them
is a campaign that gets rewritten. It costs one turn now and saves the whole
output later.

### 2. Write the brief, and get it agreed

`brief.json`:

```json
{
  "slug": "scheduling-launch",
  "goal": "signups",
  "one_metric": "trial starts from social in the 14 days after launch",
  "audience": "heads of brand at 20-200 person B2B companies",
  "key_message": "your posts stop looking generic because the brand kit renders them",
  "proof": ["40% of signups were lost at onboarding step 1", "Northwind cut design turnaround from 3 days to 1"],
  "platforms": ["linkedin", "x", "facebook"],
  "publish_at": "2026-09-01T14:30:00Z",
  "cta": "Start a trial at acme.com/start"
}
```

`one_metric` is the field that does the work. "Awareness" is not a goal anyone
can check afterwards; "trial starts from social in 14 days" is.

Show the brief and get it agreed before drafting. A wrong key message caught
here costs a minute; caught after three drafts and four graphics it costs the
whole campaign.

### 3. Research, and keep the receipts

Gather what the copy will claim: real numbers, real quotes, what competitors are
saying, what the audience is already complaining about. Write `research.md` with
**a link next to every claim**.

Anything that ends up in a post must be traceable to a line in this file. A
statistic that cannot be sourced does not go in the copy — that is the rule that
stops a campaign becoming a correction.

### 4. Draft per platform — adapted, not copy-pasted

Use the `social` skill for the platform craft. Same message, genuinely different
executions: the same 900-word LinkedIn post pasted into X is the most common
tell that nobody thought about the audience.

For each platform write the draft plus **the hook variants you considered**, and
say which you picked and why. That is what makes the review useful — the
reviewer can take a different hook without asking you to start over.

Then run every draft through `content-humanizer`. Not optional: this is the pass
that decides whether the copy reads as written by the company or by a machine
in the company's colours.

### 5. Visual brief, then the assets

`visual-brief.md` says, per asset: the placement and canvas, what it must
communicate in the two seconds someone looks at it, the headline text verbatim,
which brand tokens it uses, and whether it needs generated artwork or is type on
a field.

Then build them with `social-image-composer` — HTML sources into `cards/`,
finished files into `renders/`. Keep the sources: a resize or a copy fix is a
re-render, not a redesign.

### 6. Review before you ask anyone else to

Check the bundle yourself, against the brief, not against your own drafts:

- Does every post carry the `key_message`, in that platform's idiom?
- Is every claim traceable to `research.md`?
- Does every asset use real brand tokens, with legible text and nothing in a
  platform safe zone? (`image_describe` on each render.)
- Does the copy pass `do-not-say.md` literally?
- Is the CTA the same one, everywhere, and is it one thing?
- Would this be embarrassing if it were screenshotted and quoted back?

Fix what fails before it reaches a human. A reviewer whose first three campaigns
were fine starts approving without reading, which is exactly when the bad one
gets through.

### 7. The approval gate

**Nothing publishes without an explicit human approval.** Scheduled posts reach
a real audience under the customer's name; that is not a decision to make
autonomously, and "the user asked me to run a campaign" is not approval of the
specific words.

File the request:

```
approvals_list()      # what is already waiting
approvals_approve(id) # a human does this, not you
```

Write `approval.json` alongside it:

```json
{
  "status": "pending",
  "requested_at": "2026-08-26T09:00:00Z",
  "assets": ["linkedin.md", "x.md", "facebook.md", "renders/hero.png"],
  "approved_by": null,
  "approved_at": null,
  "notes": ""
}
```

Then present the bundle for review: what each platform gets, the assets, the
schedule, and anything you are unsure about. Say what you would change if you
had one more thing — usually a number you could not source.

If the box has no approvals lane configured, ask in the conversation and record
the answer in `approval.json`. Either way the record exists.

### 8. Publish

Only after `approval.json` reads `approved`. Then, per platform:

| Route | When |
|---|---|
| `buffer_create_post` | The default. One call queues or schedules across every connected channel, images included — but Buffer fetches attachments by URL, so a workspace render must be published somewhere reachable first |
| `linkedin_post`, `facebook_publish_post`, `instagram_publish_image`, `x_post_tweet`, `tiktok_create_post` | Direct publishing, and the route to use when the asset is a local file |

Record what actually went out — post IDs, URLs, timestamps — back into
`approval.json`. Without that, measurement in step 9 has nothing to join on.

If a platform fails, publish the rest and report the failure specifically. A
half-published campaign that is reported is recoverable; one that silently
half-published is not.

### 9. Measure against `one_metric`

After the window in the brief, pull what the platforms report —
`linkedin_get_analytics`, `facebook_get_page_insights`,
`instagram_get_media_insights`, `tiktok_post_analytics`, `x_timeline` — and
write `results.md` in the bundle.

Report against `one_metric` first, then engagement. Engagement without the goal
metric is the number that makes a campaign look successful while nothing
happened.

Then write the durable part: which hook worked, which visual format worked, what
you would do differently. Put it in `MEMORY.md` or the daily log, not only in
this folder — the point of running the tenth campaign better than the first is
that the lesson is somewhere the next one reads.

## Shorter jobs

Not everything is a full campaign. One post with no graphic: use `social`, run
`content-humanizer`, and ask before publishing. The bundle is worth it once
there is more than one platform, more than one asset, or a real audience.

The approval gate is not skippable at any size.
