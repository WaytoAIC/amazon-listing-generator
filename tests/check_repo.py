#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repository lints for the amazon-listing-generator skill.

Run from anywhere:  python3 tests/check_repo.py
Standard library only. Exit code 0 = all lints pass, 1 = at least one failed.

Lints:
  1. character budgets (the whole corpus is read by the end of a full-pack run)
  2. every file mentioned in the instructions exists; no orphan reference files
  3. deprecated field names are gone
  4. Amazon numbers appear only where they are allowed to
  5. README prefix block (lines 1-32) is byte-identical to the published one
  6. SKILL.md frontmatter is well formed
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BUDGETS = {"SKILL.md": 6000, "text_module": 2200, "visual_module": 3000, "corpus": 36000}
README_PREFIX_SHA256 = "28e7413c09e7722683e7a30fe51e341bf95826ce97b191c0b462f027cdc20965"
DEPRECATED = [
    "country_site", "bullet_points", "usps_specs", "backend_terms", "backend_keywords",
    "keywords_optional", "brand_name", "other_product_info", "keyword_evidence",
    "review_evidence", "module-prompts",
]
# Platform limits that must live only in platform-rules.md (and the checker / tests / release docs).
PLATFORM_NUMBERS = re.compile(r"(?<![0-9.])(75|125|249|250|255|2000)(?![0-9])")
NUMBER_ALLOWED = {"references/platform-rules.md"}
NON_FILE_MENTIONS = {"SKILL.md", "README.md", "CHANGELOG.md", "LICENSE.md", "ADDITIONAL_TERMS.md"}

failures = []


def fail(lint, message):
    failures.append(f"[{lint}] {message}")


def read(path):
    return path.read_text(encoding="utf-8")


def instruction_files():
    files = [ROOT / "SKILL.md"]
    files += sorted((ROOT / "references").rglob("*.md"))
    return files


def lint_budgets():
    total = 0
    for path in instruction_files():
        size = len(read(path))
        total += size
        rel = path.relative_to(ROOT).as_posix()
        if rel == "SKILL.md":
            limit = BUDGETS["SKILL.md"]
        elif path.parent.name == "modules":
            limit = BUDGETS["visual_module"] if path.name.startswith("2") else BUDGETS["text_module"]
        else:
            limit = None
        if limit and size > limit:
            fail("budget", f"{rel}: {size} chars > {limit}")
    if total > BUDGETS["corpus"]:
        fail("budget", f"instruction corpus: {total} chars > {BUDGETS['corpus']}")
    return total


def lint_links():
    mentioned = set()
    sources = instruction_files() + [ROOT / "assets" / "listing-package-template.md", ROOT / "README.md"]
    for path in sources:
        text = read(path)
        for match in re.finditer(r"\]\((\./[^)#\s]+)(?:#[^)]*)?\)", text):
            target = (path.parent / match.group(1)).resolve()
            if target.exists():
                mentioned.add(target)
            else:
                fail("links", f"{path.relative_to(ROOT)} -> {match.group(1)} does not exist")
        for match in re.finditer(r"(?<![\w/.-])((?:references|scripts|assets)/[\w./-]+\.(?:md|py))", text):
            target = (ROOT / match.group(1)).resolve()
            if target.exists():
                mentioned.add(target)
            else:
                fail("links", f"{path.relative_to(ROOT)} mentions missing {match.group(1)}")
        if path.name == "README.md":
            continue
        for match in re.finditer(r"(?<![\w/-])([0-9a-z][\w-]*\.md)", text):
            name = match.group(1)
            if name in NON_FILE_MENTIONS:
                continue
            hits = [p for p in ROOT.rglob(name) if ".git" not in p.parts and "tests" not in p.parts]
            if hits:
                mentioned.update(p.resolve() for p in hits)
            else:
                fail("links", f"{path.relative_to(ROOT)} mentions unknown file {name}")
    expected = {p.resolve() for p in (ROOT / "references").rglob("*.md")}
    expected.add((ROOT / "assets" / "listing-package-template.md").resolve())
    expected.add((ROOT / "scripts" / "check_listing.py").resolve())
    for orphan in sorted(expected - mentioned):
        fail("links", f"orphan file never mentioned: {orphan.relative_to(ROOT)}")


def lint_vocabulary():
    for path in instruction_files() + [ROOT / "assets" / "listing-package-template.md"]:
        text = read(path)
        for name in DEPRECATED:
            if name in text:
                fail("vocabulary", f"{path.relative_to(ROOT)} still uses deprecated name '{name}'")


def lint_numbers():
    for path in instruction_files() + [ROOT / "assets" / "listing-package-template.md"]:
        rel = path.relative_to(ROOT).as_posix()
        if rel in NUMBER_ALLOWED:
            continue
        text = read(path)
        if rel == "SKILL.md":
            # the frontmatter description may carry the headline title limit
            text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)
        for line_no, line in enumerate(text.splitlines(), 1):
            if PLATFORM_NUMBERS.search(line):
                fail("numbers", f"{rel}:{line_no} carries a platform number: {line.strip()[:60]}")


def lint_readme_prefix():
    lines = read(ROOT / "README.md").split("\n")
    digest = hashlib.sha256(("\n".join(lines[:32]) + "\n").encode("utf-8")).hexdigest()
    if digest != README_PREFIX_SHA256:
        fail("readme", "README.md lines 1-32 (Way to AIC prefix block) were changed")


def lint_frontmatter():
    text = read(ROOT / "SKILL.md")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        fail("frontmatter", "SKILL.md has no YAML frontmatter")
        return
    block = match.group(1)
    if not re.search(r"^name:\s*amazon-listing-generator\s*$", block, re.M):
        fail("frontmatter", "name must be amazon-listing-generator")
    description = re.search(r"^description:\s*(.+)$", block, re.M)
    if not description:
        fail("frontmatter", "description is missing")
    else:
        value = description.group(1)
        if "<" in value or ">" in value:
            fail("frontmatter", "description must not contain < or >")
        if len(value) > 1024:
            fail("frontmatter", f"description is {len(value)} chars, over 1024")


def lint_template_sections():
    """Every table the template carries must be one the checker knows about.

    Adding a section to the template without teaching the checker is silent: the section
    can go missing or turn to garbage and the run still reports a pass.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location("cl", ROOT / "scripts" / "check_listing.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    # "Listing 文案" only wraps the ### copy headings the checker already knows.
    containers = {"Listing 文案"}
    text = read(ROOT / "assets" / "listing-package-template.md")
    for line in text.split("\n"):
        if not line.startswith("## "):
            continue
        heading = line[3:].strip()
        if heading not in containers and checker.heading_key(heading) is None:
            fail("template", f"模板有「{heading}」小节，但检查脚本不认识它")


def main():
    total = lint_budgets()
    lint_links()
    lint_vocabulary()
    lint_numbers()
    lint_readme_prefix()
    lint_frontmatter()
    lint_template_sections()
    print(f"instruction corpus: {total} chars (budget {BUDGETS['corpus']})")
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for item in failures:
            print("  " + item)
        return 1
    print("PASS: budgets, links, vocabulary, numbers, README prefix, frontmatter")
    return 0


if __name__ == "__main__":
    sys.exit(main())
