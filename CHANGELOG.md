# Changelog

All notable changes to this project will be documented in this file.

The format is intentionally simple and optimized for release notes and repository readers.

## [Unreleased]

### Added

- MCP-aware data enrichment guidance for Sorftime, 卖家精灵, and similar Amazon data sources
- A dedicated reference for mapping keyword, competitor, review, and category data into Listing drafting

### Changed

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
