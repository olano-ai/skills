# olano-ai / skills

A catalog of [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
for use with Claude Code and other Claude agents.

Each skill is a self-contained directory under [`skills/`](./skills) holding a
`SKILL.md` (with YAML frontmatter describing when to use it) plus any supporting
scripts, references, templates, and assets it needs. Agents load a skill's
instructions on demand when the task matches the skill's `description`.

## Directory structure

```
skills/
  <skill-name>/
    SKILL.md          # required — frontmatter (name, description) + instructions
    reference.md ...  # optional supporting docs the skill links to
    scripts/          # optional executable helpers
    assets/           # optional templates, fonts, examples, binaries
```

## Skills catalog

This catalog holds Olano's **general and vendored** skills: every general
skill bundled with [olano-ai/olano](https://github.com/olano-ai/olano)
(`olano/skills/built_in/`) and additional vendored skills (see
[Document skills](#document-skills)). Olano installs
copy this catalog into the common skills directory (`<home>/skills/`) — see
[Using these skills with Olano](#using-these-skills-with-olano).

**Platform skills ship with Olano, not here.** `olano-platform`,
`olano-agent`, `olano-cloud`, `olano-admin` and `olano-agent-builder` live only
in `olano/skills/built_in/` because they teach the tool surface of the exact
Olano version that is installed (the `self_*`, `magic_link_*` and `olano_*`
tools); a copy in this catalog would drift from it. The two AgentFather
playbooks (`olano-admin`, `olano-agent-builder`) declare `requires_tools` and
are advertised only to agents holding the admin tools.

| Skill | What it does | Source |
| --- | --- | --- |
| [architecture-diagram](./skills/architecture-diagram) | Generate Mermaid architecture diagrams from code or descriptions. | olano-ai/olano |
| [brainstorming](./skills/brainstorming) | Explore intent, requirements, and design before any creative/build work. | obra/superpowers |
| [brand-kit](./skills/brand-kit) | Set up or read the brand kit — palette, fonts, logo, design tokens, and a voice profile — that every graphic and post is built from. | original |
| [browser-use](./skills/browser-use) | Drive the headless browser tools — one-shot captures vs interactive sessions, selectors, extraction, screenshots. | olano-ai/olano |
| [canvas-design](./skills/canvas-design) | Create original visual art as `.png`/`.pdf` (posters, designs) with a bundled font library. | anthropics/skills |
| [charts](./skills/charts) | Publication-quality data charts for chat, email, decks and social media — recipes, raw Vega-Lite and a themed frame, rendered on the bundled Chromium. | original |
| [codebase-inspection](./skills/codebase-inspection) | Systematic repo map and symbol lookup for understanding an unfamiliar codebase. | olano-ai/olano |
| [content-humanizer](./skills/content-humanizer) | Rewrite AI-sounding copy so it reads like a person wrote it, and check a draft against the brand's voice profile. | original |
| [doc-coauthoring](./skills/doc-coauthoring) | Structured workflow for co-authoring docs, proposals, specs, and decision docs. | anthropics/skills |
| [frontend-design](./skills/frontend-design) | Aesthetic direction, typography, and distinctive UI choices when building or reshaping a UI. | anthropics/skills |
| [github-pr-workflow](./skills/github-pr-workflow) | End-to-end GitHub PR creation, review, and merge workflow. | olano-ai/olano |
| [image](./skills/image) | Umbrella skill for every kind of image — routes each request to `image_generate`, `render_html_image`, a diagram, a chart or `canvas-design`, then prompting, QA and delivery rules for generated pictures. | coreyhaines31/marketingskills |
| [internal-comms](./skills/internal-comms) | Write internal communications (status reports, leadership updates, newsletters, FAQs). | anthropics/skills |
| [mcp-builder](./skills/mcp-builder) | Build an MCP server to connect a platform, API or internal system that has no existing integration. | anthropics/skills |
| [plan](./skills/plan) | Structured planning and TDD workflow for non-trivial tasks. | olano-ai/olano |
| [product-marketing](./skills/product-marketing) | Build the product marketing context doc — positioning, ICP, competitors, proof — that other marketing skills read. | coreyhaines31/marketingskills |
| [requesting-code-review](./skills/requesting-code-review) | Prepare a diff summary and review checklist for an effective code review. | olano-ai/olano |
| [skill-creator](./skills/skill-creator) | Create, improve, and evaluate skills; benchmark and optimize skill descriptions. | anthropics/skills |
| [slack-gif-creator](./skills/slack-gif-creator) | Create animated GIFs optimized for Slack — constraints, validation tools, animation concepts. | anthropics/skills |
| [social](./skills/social) | Create, repurpose and schedule social content across platforms, plus short-form video scripting and social listening. | coreyhaines31/marketingskills |
| [social-campaign](./skills/social-campaign) | Run a social campaign end to end — brief, research, per-platform drafts, visuals, review, approval gate. | original |
| [social-image-composer](./skills/social-image-composer) | Compose branded social graphics and carousels at exact platform dimensions with HTML/CSS over generated artwork. | original |
| [systematic-debugging](./skills/systematic-debugging) | Step-by-step debugging recipe for isolating and fixing bugs. | olano-ai/olano |
| [test-driven-development](./skills/test-driven-development) | Red-green-refactor TDD loop for building reliable, testable code. | olano-ai/olano |
| [theme-factory](./skills/theme-factory) | Apply one of 10 preset themes (colors/fonts) to artifacts, or generate a new theme. | anthropics/skills |
| [web-artifacts-builder](./skills/web-artifacts-builder) | Build elaborate multi-component claude.ai HTML artifacts (React, Tailwind, shadcn/ui). | anthropics/skills |
| [web-research](./skills/web-research) | Fetch, summarize, and cite web content for answering questions. | olano-ai/olano |
| [webapp-testing](./skills/webapp-testing) | Drive and test local web apps with Playwright (screenshots, logs, UI debugging). | anthropics/skills |
| [writing-plans](./skills/writing-plans) | Author clear implementation plans and technical proposals. | olano-ai/olano |

### Document skills

The `docx`, `pdf`, `pptx` and `xlsx` skills are not part of this repository.
They are Olano's own, are not open source, and reach managed deployments
through the Olano cloud skills catalog. A self-hosted install has the document
toolchain (LibreOffice, Tesseract, qpdf, ImageMagick) and can use any skill of
its own for these formats.

## Using these skills with Olano

[Olano](https://github.com/olano-ai/olano) fetches this repository during
install/setup and copies each skill into the deployment's **common skills
directory** (`<home>/skills/`, i.e. `~/.olano/skills/`), where every agent
picks it up. This mirrors how the canonical agent pack
([olano-ai/olano-agents](https://github.com/olano-ai/olano-agents)) is fetched
into `<home>/archetypes/`.

```bash
# Clone/refresh this catalog into the common skills directory (idempotent):
olano skills update

# Point at a fork/mirror instead:
olano skills update --url https://github.com/your-org/skills.git
# or: export OLANO_SKILLS_REPO_URL=https://github.com/your-org/skills.git
```

`olano skills sync` still copies the skills bundled inside the Olano package;
`olano skills update` overlays the (richer) catalog from this repository.

## Attribution & licensing

These skills are vendored from their upstream projects. Please observe each source's license.

- **anthropics/skills**: <https://github.com/anthropics/skills>. Each skill
  from that repository is Apache-2.0 licensed and ships the complete licence
  text as its own `LICENSE.txt`. Skills Olano has changed say so in their
  `SKILL.md` frontmatter (`Modified by Olano from the anthropics/skills
  original`).
- **obra/superpowers** — <https://github.com/obra/superpowers>. The
  `brainstorming` skill is MIT licensed (© 2025 Jesse Vincent); the MIT license
  text is included at [`skills/brainstorming/LICENSE`](./skills/brainstorming/LICENSE).
- **olano-ai/olano** — <https://github.com/olano-ai/olano>. Skills bundled with
  Olano itself (`olano/skills/built_in/`). Skills that originate from
  `anthropics/skills` but ship inside Olano (`frontend-design`,
  `slack-gif-creator`) retain their upstream `LICENSE.txt`.
- **coreyhaines31/marketingskills** — <https://github.com/coreyhaines31/marketingskills>.
  The `product-marketing`, `social` and `image` skills are MIT licensed
  (© 2025 Corey Haines); each ships the MIT license text as its own `LICENSE`.
- **Vega, Vega-Lite and Vega-Embed**: the `charts` skill vendors these
  libraries (BSD-3-Clause); their licence files are kept under
  `skills/charts/assets/vendor/`. The skill's method, references and palette
  validator are Olano's own work.
- **Fonts**: `canvas-design/canvas-fonts/` bundles typefaces under the SIL Open
  Font License 1.1, each with its licence file beside it.
- **shadcn/ui**: `web-artifacts-builder/scripts/shadcn-components.tar.gz` holds
  shadcn/ui components (MIT, see `scripts/THIRD_PARTY_NOTICES.md` there).

Skills marked `original` in the table above were written by Olano and, like
everything else in this repository that does not carry its own licence file,
are released under the MIT License in [`LICENSE`](./LICENSE).
