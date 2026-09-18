# Changelog

All notable changes to this project will be documented in this file.

The format is intentionally simple and optimized for release notes and repository readers.

## [Unreleased]

## [v2.0.0] - not released yet

Rebuilds the skill from a set of prompts into a pipeline with inputs fixed before writing, a script check after writing, and one round of rework in between.

### Added

- Must-answer buyer question table, built before writing and verified after writing; questions with no supporting facts are neither answered nor implied and go to a pre-launch to-do list
- Backend attribute sheet, filled before the copy so front-end and back-end values agree
- Selling point to user story table shared by bullets, description, images, A+, and video
- Product description module, written only when there is no A+ or on request
- `scripts/check_listing.py`: standard-library checker for lengths, banned characters, repetition, placeholders, and table completeness; it writes its own result section with a copy fingerprint
- `assets/listing-package-template.md`: the fixed deliverable template the checker parses
- `references/platform-rules.md`: single source of Amazon numbers, each rule marked hard, recommended, or practice, with its help-page source and verification date
- Variation-family rules with a per-child difference table that the checker validates
- The checker now reads the backend attribute sheet too: every attribute needs a source, a full check asks which front-end sentence carries it, and a full pack without the sheet does not pass
- Every section the template carries is now one the checker knows: image, A+ and video briefs, the user-story table, the human-judgment table, the iteration log and the review notes all get at least an is-it-filled check, and a repository lint fails if a future template section is added without teaching the checker
- The storyboard is counted cell by cell, so a shot list whose storyboard was emptied or overwritten no longer passes
- Human-judgment rows must open with one of the three allowed results; a reason may follow
- Review-and-iterate mode: locate the funnel stage, change at most two modules per round, log hypothesis and review date
- Two-version output on request: a search-coverage version and a conversion version
- Brand tone fallback (compact Brand OS card) for visual tasks without a brand tone
- Alexa question collection as the first preparation module (`references/modules/00-alexa-insight.md`), built on [amazon-alexa-insight](https://github.com/WaytoAIC/amazon-alexa-insight). Used two ways: ask competitors to learn what buyers care about, and ask your own live product to verify coverage with measured answers instead of a simulation. Three ways to feed it — a CSV / Excel / JSON the user exported from the browser extension, the CLI run by the skill, or neither, in which case the skill writes its own questions and says so. Preparation modules renumbered 01–04 to make room
- Newly covered Amazon rules: Alexa for Shopping, AI-generated people metadata tag, A+ and video content rules, description HTML rule, narrowed review sharing across variations

### Changed

- Rufus Q&A validation is now Alexa question coverage verification and runs against the must-answer table; old names are still accepted
- Listing self-check is now the compliance check: the script runs first and always last, human judgment covers only what the script cannot decide
- Image, A+, and video briefs upgraded: one job per image, explicit forbidden elements, an English image-generation prompt per slot, a 6–9 shot list with three consistency rules; briefs and prompts only, no tool calls
- Bullets follow Amazon's recommended format: header, colon, description; no end punctuation; at least one statement of who the product suits or does not suit
- One field vocabulary across all files (`marketplace`, `bullets`, `search_terms`, `banned_terms`, and so on)
- Module instructions split into twelve files under `references/modules/`; the entry file routes to one file per step
- `install.sh` no longer installs `tests/`, `.claude/`, or `.github/`
- Must-answer questions now come from asking Alexa rather than from imagination: sources rank measured > collected > reviews > simulated, and simulated questions only fill dimensions the first three miss
- Coverage verification on a live product asks Alexa directly instead of role-playing it; a verdict of "do not answer" is recorded together with what Alexa says instead, because shoppers still get an answer — one drawn from reviews
- Image and A+ briefs now carry the two-step text treatment as the default, not a fallback: the model renders a text-free base, code places the copy and the leader lines, and a base with no text is not the deliverable. A+ keeps module headlines and body in the backend text fields while in-image labels — dimension lines, part callouts, hotspot numbers — are placed by code
- A+ modules are routed by what they actually produce — pure fields, a single image, a consistent set, a base image plus hotspot coordinates, or a shot list — instead of one prompt per screen. A comparison chart or a Q&A module is laid out from fields, so generating an image for it is wasted work
- Anything that has to be exact is taken away from the model: counts, true relative proportions, fine repeating pattern (it weaves in fake letters), rulers and readings, and subject coverage and margins. Each has a stated code-side alternative
- Every image slot carries acceptance criteria filled in with measured values against required values, not a bare "passed"; unfilled measurements are caught by the placeholder check
- A picture makes claims too: a slot whose image demonstrates an unverified feature has to be shot for real, a known defect may not be smoothed away in the image, and when the image is changed to avoid a complaint the copy and the alt text change with it
- Claim words the checker questions now cover consumer goods (safety, tested performance, environmental and endorsement claims), not only supplements; the checker reads the claims table itself and stays quiet about words it already backs, while a claim marked unverified is still raised

### Fixed

- Main images are no longer treated as always-white: a limited set of product types may use a lifestyle main image (with no text or extra logos), decided by the category's product page style guide. When in doubt the brief now carries both a white-background and a lifestyle version
- Small images are never upscaled to hit a pixel target — Amazon forbids artificially enlarging them. Cropping the margin and flattening the background to pure white are still fine
- Premium A+ is no longer gated behind a permission the seller has to claim: it costs nothing extra and has no eligibility criteria, so the brief now plans for Premium by default and drops to Basic only on request. Brand story is covered as a third content type that coexists with either
- A verdict written as "not covered, but minor" no longer slips past the uncovered-question warning: the leading word decides and a reason may follow it; verdicts outside the four allowed words are now flagged
- A deliverable with no copy sections no longer reports a fingerprint. Every such file used to share one constant hash, which read as a match between unrelated files; the report now says there is no copy to fingerprint

### Removed

- `references/module-prompts.md` and all prompt skeletons; the agent follows the module rules directly
- Amazon numbers from every file except `references/platform-rules.md` and the checker

## [v1.1.0] - 2026-09-18

Aligns the skill with Amazon's 2026 title rules: titles of 75 characters or fewer and the new Item Highlights field. Also ships the MCP-aware enrichment work that had not been released yet.

### Added

- Item Highlights module: up to 125 characters, comma-separated phrases, no words repeated from the title. The full pack is now 9 modules
- Keyword four-layer allocation step before drafting: core product terms go to the title, feature and material terms to Item Highlights, use-case and purchase-reason terms to bullets and A+, long-tail terms and synonyms to Search Terms. Each keyword goes to one place only, and keywords with no support in the product facts are marked unused
- `keyword_allocation` and `existing_listing.item_highlights` fields in the intake schema
- Numeric checklist in the Listing self-check module: title 75, Item Highlights 125, bullets 10–255 each, description 2000, Search Terms under 250 bytes, image basics
- MCP-aware data enrichment guidance for Sorftime, 卖家精灵, and similar Amazon data sources
- A dedicated reference for mapping keyword, competitor, review, and category data into Listing drafting

### Changed

- Title module now targets 75 characters or fewer including spaces (was 100–125) and treats the title as the product's identity rather than a keyword container
- Search Terms module now excludes words already used in the title, Item Highlights, and bullets, takes the terms allocated to it first, fills remaining space only with synonyms that match the product facts, and no longer collects common misspellings, which Amazon advises against
- Existing-listing optimization now flags titles over 75 characters and splits them into a compliant title plus Item Highlights
- Title, Item Highlights, and Search Terms outputs now report their actual length
- SKILL.md, README (CN/EN), agents/openai.yaml, workflow, intake schema, and MCP mapping now describe the 9-module flow
- Updated the main skill workflow to prefer MCP data enrichment before drafting when connected
- Expanded the intake schema and module rules to capture MCP-derived evidence safely

## [v1.0.0] - 2026-04-02

First public release.

### Added

- Initial `amazon-listing-generator` skill
- Full Amazon Listing workflow covering 8 output modules
- Chinese-first guidance with target-marketplace language output rules
- Built-in workflow, intake-schema, and module-prompt references
- Installer for Codex and OpenClaw
- Bilingual README and source-available license files
