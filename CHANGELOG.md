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
- Review-and-iterate mode: locate the funnel stage, change at most two modules per round, log hypothesis and review date
- Two-version output on request: a search-coverage version and a conversion version
- Brand tone fallback (compact Brand OS card) for visual tasks without a brand tone
- `references/alexa-insight.md`: optional path for collecting real buyer questions by asking Alexa for Shopping in bulk (amazon-alexa-insight / apinsight), used two ways — ask competitors to learn what buyers care about, and ask your own live product to verify coverage with measured answers instead of a simulation; falls back to simulated questions when the tool is unavailable
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
- Claim words the checker questions now cover consumer goods (safety, tested performance, environmental and endorsement claims), not only supplements; the checker reads the claims table itself and stays quiet about words it already backs, while a claim marked unverified is still raised

### Fixed

- A verdict written as "not covered, but minor" no longer slips past the uncovered-question warning: the leading word decides and a reason may follow it; verdicts outside the four allowed words are now flagged

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
