# Changelog

All notable changes to this project will be documented in this file.

The format is intentionally simple and optimized for release notes and repository readers.

## [Unreleased]

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
