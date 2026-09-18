#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scripts/check_listing.py.

Run from anywhere:  python3 tests/run_tests.py
Python 3.8+, standard library only (unittest, no pytest).
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "scripts", "check_listing.py")
FIXTURES = os.path.join(HERE, "fixtures")
TEMPLATE = os.path.join(ROOT, "assets", "listing-package-template.md")
RULES = os.path.join(ROOT, "references", "platform-rules.md")


sys.dont_write_bytecode = True  # do not leave scripts/__pycache__ behind in the skill folder


def load_script():
    spec = importlib.util.spec_from_file_location("check_listing", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cl = load_script()


def fixture(name):
    return os.path.join(FIXTURES, name)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run_cli(*args, **kwargs):
    """Run the script in a subprocess. Returns (exit code, stdout, stderr)."""
    stdin = kwargs.pop("stdin", None)
    cwd = kwargs.pop("cwd", None)
    proc = subprocess.run([sys.executable, SCRIPT] + list(args), input=stdin, cwd=cwd,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


def run_json(*args, **kwargs):
    """Run with --json. Returns (exit code, parsed result of the first file)."""
    code, out, err = run_cli(*(list(args) + ["--json"]), **kwargs)
    lines = [line for line in out.splitlines() if line.strip()]
    return code, (json.loads(lines[0]) if lines else None)


def ids(result, level):
    return [c["id"] for c in result["checks"] if c["level"] == level]


def entries(result, cid, level=None):
    return [c for c in result["checks"] if c["id"] == cid and (level is None or c["level"] == level)]


def package(title=None, highlights=None, bullets=None, description=None, search_terms=None,
            params=None, extra=""):
    """Build a small package in the template's layout."""
    lines = []
    if params is not None:
        lines += ["## 检查参数", ""] + ["- %s: %s" % item for item in params.items()] + [""]
    for heading, value in (("Title", title), ("Item Highlights", highlights)):
        if value is not None:
            lines += ["### " + heading, "", value, ""]
    if bullets is not None:
        lines += ["### Bullet Points", ""] + ["%d. %s" % (i + 1, b) for i, b in enumerate(bullets)] + [""]
    for heading, value in (("Product Description", description), ("Search Terms", search_terms)):
        if value is not None:
            lines += ["### " + heading, "", value, ""]
    return "\n".join(lines) + extra


def check(text, full=False, **overrides):
    return cl.check_text(text, "-", full, overrides)


GOOD_BULLETS = [
    "Even extraction: spiral ribs lift the paper so water flows steadily",
    "Sized for a solo morning: brews 300 to 500 ml per session",
    "Glazed stoneware: holds heat during the pour and rinses clean",
]


class LimitsSyncTest(unittest.TestCase):
    """Script constants must equal the 机器可读限值 table in references/platform-rules.md."""

    def parse_limits(self):
        rows, inside = {}, False
        for line in read(RULES).splitlines():
            if line.startswith("## "):
                inside = line[3:].strip() == "机器可读限值"
                continue
            match = re.match(r"^\|\s*([a-z_]+)\s*\|\s*([^|]+?)\s*\|\s*$", line)
            if inside and match and match.group(1) != "key":
                rows[match.group(1)] = match.group(2)
        return rows

    def test_constants_equal_the_rules_table(self):
        limits = self.parse_limits()
        self.assertIn("rules_as_of", limits)
        self.assertEqual(cl.RULES_AS_OF, limits.pop("rules_as_of"))
        self.assertGreaterEqual(len(limits), 7, "limits table looks truncated: %r" % limits)
        for key, value in limits.items():
            self.assertTrue(value.isdigit(), "non-numeric limit %s=%s" % (key, value))
            self.assertTrue(hasattr(cl, key.upper()), "script has no constant %s" % key.upper())
            self.assertEqual(getattr(cl, key.upper()), int(value), key)

    def test_version_flag(self):
        code, out, _err = run_cli("--version")
        self.assertEqual(code, 0)
        self.assertIn("2.0.0", out)
        self.assertIn(cl.RULES_AS_OF, out)
        self.assertEqual(cl.SCRIPT_VERSION, "2.0.0")


class TemplateContractTest(unittest.TestCase):
    """The raw template is the contract: it must parse, and fail only because it is unfilled."""

    def test_raw_template_exits_1_not_2(self):
        code, out, err = run_cli(TEMPLATE)
        self.assertEqual(code, 1, err)
        self.assertNotIn("Traceback", err)
        self.assertIn("占位符未填", out)

    def test_raw_template_full_mode(self):
        code, result = run_json(TEMPLATE, "--full")
        self.assertEqual(code, 1)
        self.assertEqual(result["mode"], "full")
        for cid in ("B4", "X1", "X2", "X3", "X4"):
            self.assertIn(cid, ids(result, "FAIL"))

    def test_template_has_every_heading_the_script_looks_for(self):
        doc = cl.Document(read(TEMPLATE))
        self.assertEqual(sorted(doc.sections), sorted(cl.HEADING_ALIASES))
        self.assertEqual(doc.duplicates, [])

    def test_template_tables_have_the_columns_the_script_needs(self):
        doc = cl.Document(read(TEMPLATE))
        needed = {
            "qa_table": ("编号", "有无依据", "实际由哪句回答", "判定"),
            "claims_table": ("编号", "依据"),
            "variation_table": ("子体", "title", "item highlights", "search terms"),
        }
        for key, columns in needed.items():
            headers, rows = cl.parse_table(doc.sections[key].lines)
            for column in columns:
                self.assertIn(column, headers, "%s lost column %s" % (key, column))
            self.assertEqual(cl.data_rows(rows), [], "%s: untouched template rows must not count as data" % key)

    def test_template_params_are_empty_until_filled(self):
        params = cl.parse_params(cl.Document(read(TEMPLATE)).sections["params"])
        self.assertEqual(params["brand"], "")
        self.assertEqual(params["language"], "")
        self.assertEqual(params["title_limit_exempt"], "no")


class FixtureTest(unittest.TestCase):
    def test_pass_full(self):
        code, result = run_json(fixture("pass-full.md"), "--full")
        self.assertEqual(code, 0)
        self.assertEqual(ids(result, "FAIL"), [])
        self.assertEqual(ids(result, "WARN"), ["S7"])
        self.assertEqual(entries(result, "S7")[0]["measured"], "filter")
        self.assertEqual(result["summary"], {"fail": 0, "warn": 1, "info": 2})  # S1 official count + L1 lengths
        self.assertEqual(result["params"]["brand"], "Brewlane")
        self.assertEqual(result["params"]["banned_terms"], ["unbreakable", "barista approved"])
        code, _out, _err = run_cli(fixture("pass-full.md"))
        self.assertEqual(code, 0)

    def test_fail_lengths_chars(self):
        code, result = run_json(fixture("fail-lengths-chars.md"))
        self.assertEqual(code, 1)
        self.assertEqual(set(ids(result, "FAIL")), {"T1", "T2", "H1", "B1", "B2", "B3", "G6", "S1", "S3", "G1"})
        measured = dict((c["id"], c) for c in result["checks"] if c["level"] == "FAIL")
        self.assertEqual(measured["T1"]["measured"], "81 字符")
        self.assertEqual(measured["H1"]["measured"], "130 字符")
        self.assertEqual(measured["B1"]["measured"], "2 条")
        self.assertEqual((measured["B2"]["field"], measured["B2"]["measured"]), ("Bullet 1", "270 字符"))
        self.assertEqual(measured["B3"]["field"], "Bullet 1")
        self.assertEqual(measured["G6"]["field"], "Bullet 1")
        self.assertEqual(measured["S1"]["measured"], "260 字节")
        self.assertIn("Brewlane", measured["S3"]["measured"])
        self.assertIn("B0FAKE1234", measured["S3"]["measured"])
        self.assertEqual((measured["G1"]["field"], measured["G1"]["measured"]), ("Bullet 2", "dishwasher safe"))
        self.assertIn("H2", ids(result, "WARN"))

    def test_fail_structure(self):
        code, result = run_json(fixture("fail-structure.md"), "--full")
        self.assertEqual(code, 1)
        self.assertEqual(set(ids(result, "FAIL")), {"X2b", "X2c", "X3", "X8"})
        self.assertEqual(entries(result, "X2b", "FAIL")[0]["measured"], "Q02")
        self.assertEqual(entries(result, "X2c", "FAIL")[0]["measured"], "Q04")
        self.assertEqual(entries(result, "X3", "FAIL")[0]["measured"], "C03")
        self.assertEqual(entries(result, "X2d", "WARN")[0]["measured"], "Q05")
        self.assertIn("1 处", entries(result, "X6", "WARN")[0]["measured"])

    def test_partial_title_only(self):
        code, result = run_json(fixture("partial-title-only.md"))
        self.assertEqual(code, 0)
        self.assertEqual(result["mode"], "partial")
        self.assertEqual(ids(result, "FAIL"), [])
        # "dishwasher safe" is a claim and this file carries no claims table to back it.
        self.assertEqual(ids(result, "WARN"), ["G2"])
        skipped = [c["field"] for c in result["checks"] if c["level"] == "SKIP"]
        for label in ("Bullet Points", "Search Terms", "必答问题表", "宣称依据表", "上架前待办", "关键词分配表"):
            self.assertIn(label, skipped)
        code, result = run_json(fixture("partial-title-only.md"), "--full")
        self.assertEqual(code, 1)
        self.assertEqual(set(ids(result, "FAIL")), {"X1", "X2", "X3", "X4", "X8"})
        missing = [c["field"] for c in entries(result, "X1", "FAIL")]
        self.assertEqual(sorted(missing), ["Bullet Points", "Search Terms", "关键词分配表"])

    def test_missing_item_highlights_only_warns_in_full_mode(self):
        # Item Highlights is still rolling out by product type, so --full must not fail on it.
        text = package(title="Brewlane Ceramic Pour Over Coffee Dripper", bullets=GOOD_BULLETS,
                       search_terms="cone brewer filter holder")
        result = check(text, full=True)
        self.assertEqual([c["field"] for c in entries(result, "X1", "WARN")], ["Item Highlights"])
        self.assertNotIn("Item Highlights", [c["field"] for c in entries(result, "X1", "FAIL")])

    def test_measured_lengths_are_always_reported(self):
        # Agents kept counting by hand after a pass, so the report must show the numbers itself.
        title = "Brewlane Ceramic Pour Over Coffee Dripper"
        text = package(title=title, highlights="Glazed Stoneware, Spiral Ribs", bullets=GOOD_BULLETS,
                       search_terms="cone brewer filter holder")
        overview = entries(check(text), "L1", "INFO")
        self.assertEqual(len(overview), 1)
        measured = overview[0]["measured"]
        self.assertIn("Title %d 字符" % len(title), measured)
        self.assertIn("Item Highlights 29 字符", measured)
        self.assertIn("Bullets %s 字符" % "/".join(str(len(b)) for b in GOOD_BULLETS), measured)
        self.assertIn("Search Terms 25 字节", measured)
        code, result = run_json(fixture("variation.md"))
        children = entries(result, "L2", "INFO")
        self.assertEqual(len(children), 1)
        self.assertIn("标题", children[0]["measured"])
        self.assertIn("78 字符", children[0]["measured"], "the over-limit child is listed with its real length")

    def test_markdown_marks_inside_copy_warn(self):
        bullets = ["**Even extraction**: spiral ribs lift the paper so water flows steadily"] + GOOD_BULLETS[1:]
        result = check(package(title="Brewlane Ceramic Pour Over Coffee Dripper", bullets=bullets))
        hits = entries(result, "G7", "WARN")
        self.assertEqual([c["field"] for c in hits], ["Bullet 1"])
        self.assertIn("**", hits[0]["measured"])
        clean = check(package(title="Brewlane Ceramic Pour Over Coffee Dripper", bullets=GOOD_BULLETS))
        self.assertEqual(entries(clean, "G7", "WARN"), [])

    def test_variation(self):
        code, result = run_json(fixture("variation.md"))
        self.assertEqual(code, 1)
        failures = entries(result, "X5", "FAIL")
        self.assertEqual(len(failures), 1, "the 75-character child must pass")
        self.assertIn("Speckled Sea Salt 02", failures[0]["field"])
        self.assertEqual(failures[0]["measured"], "78 字符")
        code, out, _err = run_cli(fixture("variation.md"))
        self.assertIn("Speckled Sea Salt 02", out)

    def test_fixture_set_is_complete(self):
        names = sorted(n for n in os.listdir(FIXTURES) if n.endswith(".md"))
        self.assertEqual(names, ["fail-lengths-chars.md", "fail-structure.md", "partial-title-only.md",
                                 "pass-full.md", "variation.md"])


class MatchingTest(unittest.TestCase):
    def hit(self, term, text):
        return bool(cl.term_regex(term).search(text))

    def test_banned_terms_respect_word_boundaries(self):
        self.assertTrue(self.hit("treat", "Will treat stains"))
        self.assertFalse(self.hit("treat", "A gentle treatment"))
        self.assertTrue(self.hit("best", "The Best cup"))
        self.assertFalse(self.hit("best", "asbestos free"))
        self.assertTrue(self.hit("#1", "the #1 pick"))
        self.assertFalse(self.hit("#1", "item #10"))

    def test_space_hyphen_and_no_separator_are_the_same(self):
        for text in ("leak proof lid", "Leak-Proof lid", "leakproof lid", "leak  proof lid"):
            self.assertTrue(self.hit("leak proof", text), text)
        self.assertTrue(self.hit("leak-proof", "a leakproof lid"))
        self.assertFalse(self.hit("leak proof", "leakproofing spray"))

    def test_user_banned_term_fails_wherever_it_appears(self):
        bullets = GOOD_BULLETS[:2] + ["Leakproof base: stays dry on the counter after a gentle treatment"]
        result = check(package(title="Brewlane Ceramic Dripper", bullets=bullets), banned="leak proof, treat")
        found = [(c["field"], c["measured"]) for c in entries(result, "G1", "FAIL")]
        self.assertEqual(found, [("Bullet 3", "leak proof")])

    def test_caution_words_warn_but_do_not_fail(self):
        result = check(package(title="Brewlane Certified Ceramic Dripper"))
        self.assertEqual(entries(result, "G2", "WARN")[0]["measured"], "certified")
        self.assertEqual(result["summary"]["fail"], 0)


class CountingTest(unittest.TestCase):
    def test_bytes_and_characters(self):
        self.assertEqual(cl.byte_len("é"), 2)
        self.assertEqual(cl.byte_len(chr(0x2019)), 3)
        self.assertEqual(cl.char_len("café"), 4)
        self.assertEqual(cl.char_len("cafe" + chr(0x301)), 4, "counts are NFC-normalised")
        self.assertEqual(cl.byte_len("pour-over cup's"), 15)
        self.assertEqual(cl.byte_len_official("pour-over cup's"), 12)

    def test_search_terms_limit_is_bytes_with_spaces(self):
        for text, level in (("a" * 249, "PASS"), ("a" * 250, "FAIL"), ("é" * 124, "PASS"), ("é" * 125, "FAIL")):
            result = check(package(search_terms=text))
            s1 = [c for c in entries(result, "S1") if c["level"] != "INFO"]
            self.assertEqual([c["level"] for c in s1], [level], text[:3])
            self.assertEqual(len(entries(result, "S1", "INFO")), 1, "the official count is always reported")
        spaced = check(package(search_terms=" ".join(["ab"] * 84)))  # 84 * 2 + 83 spaces = 251 bytes
        self.assertEqual(entries(spaced, "S1", "FAIL")[0]["measured"], "251 字节")
        self.assertEqual(entries(spaced, "S1", "INFO")[0]["measured"], "168 字节")

    def test_title_and_highlights_limits(self):
        for length, level in ((75, "PASS"), (76, "FAIL")):
            result = check(package(title="Brewlane " + "x" * (length - 9)))
            self.assertEqual([c["level"] for c in entries(result, "T1")], [level])
        for length, level in ((125, "PASS"), (126, "FAIL")):
            result = check(package(highlights="y" * length))
            self.assertEqual([c["level"] for c in entries(result, "H1")], [level])

    def test_bullet_count_and_length(self):
        result = check(package(bullets=GOOD_BULLETS))
        self.assertEqual([c["level"] for c in entries(result, "B1")], ["PASS"])
        self.assertEqual([c["level"] for c in entries(result, "B1b")], ["WARN"])
        result = check(package(bullets=GOOD_BULLETS + ["Too short", "Z" * 256]))
        self.assertEqual([(c["field"], c["measured"]) for c in entries(result, "B2", "FAIL")],
                         [("Bullet 4", "9 字符"), ("Bullet 5", "256 字符")])

    def test_fingerprint_covers_only_the_copy(self):
        import hashlib
        parts = dict(title="Brewlane Ceramic Dripper", highlights="Spiral ribs, single hole base",
                     bullets=GOOD_BULLETS, description="Plain text here", search_terms="pourover cone")
        joined = "\n\n".join([parts["title"], parts["highlights"], "\n".join(GOOD_BULLETS),
                              parts["description"], parts["search_terms"]])
        expected = hashlib.sha1(joined.encode("utf-8")).hexdigest()[:8]
        self.assertEqual(check(package(**parts))["fingerprint"], expected)
        dressed = package(params={"brand": "Brewlane"}, extra="\n## 机器检查结果\n\nanything at all\n", **parts)
        self.assertEqual(check(dressed)["fingerprint"], expected)
        parts["title"] += " White"
        self.assertNotEqual(check(package(**parts))["fingerprint"], expected)


class WordRuleTest(unittest.TestCase):
    def test_stop_words_are_exempt_from_title_repeats(self):
        title = "Brewlane Dripper for Coffee and Tea for Home and Office for Mugs and Cups"
        self.assertEqual([c["level"] for c in entries(check(package(title=title)), "T3")], ["PASS"])
        result = check(package(title="Brewlane Cup Dripper with Cup Stand and Cup Lid"))
        self.assertEqual(entries(result, "T3", "FAIL")[0]["measured"], "cup ×3")

    def test_singular_and_plural_together(self):
        result = check(package(title="Brewlane Cup Dripper with Cups Stand and Cup Lid"))
        self.assertEqual([c["level"] for c in entries(result, "T3")], ["PASS"])
        self.assertEqual(entries(result, "T3b", "WARN")[0]["measured"], "cup/cups ×3")

    def test_stop_words_are_exempt_from_highlights_overlap(self):
        title = "Brewlane Ceramic Dripper for Coffee with Stand"
        result = check(package(title=title, highlights="Spiral ribs for even flow, works with most mugs"))
        self.assertEqual([c["level"] for c in entries(result, "H4")], ["PASS"])
        result = check(package(title=title, highlights="Ceramic body, spiral ribs"))
        self.assertEqual(entries(result, "H4", "WARN")[0]["measured"], "ceramic")

    def test_promo_phrases_fail_and_ambiguous_words_warn(self):
        result = check(package(title="Brewlane Best Seller Dripper, New Glaze"))
        self.assertEqual(entries(result, "T4", "FAIL")[0]["measured"], "best seller")
        self.assertEqual(entries(result, "T4b", "WARN")[0]["measured"], "new")
        result = check(package(title="Brewlane Top-Rated Bestseller Dripper"))
        self.assertEqual(entries(result, "T4", "FAIL")[0]["measured"], "best seller、top rated")

    def test_title_style_warnings(self):
        result = check(package(title="BREWLANE PREMIUM CERAMIC Dripper with Two Filters" + chr(0x2122),
                               params={"brand": "Brewlane"}))
        self.assertEqual(entries(result, "T5", "WARN")[0]["measured"], "PREMIUM、CERAMIC")
        self.assertEqual(entries(result, "T6", "WARN")[0]["measured"], "Two")
        self.assertEqual(len(entries(result, "T8", "WARN")), 1)
        self.assertEqual([c["level"] for c in entries(result, "T7")], ["PASS"])
        result = check(package(title="Ceramic Dripper by Brewlane", params={"brand": "Brewlane"}))
        self.assertEqual(len(entries(result, "T7", "WARN")), 1)

    def test_highlights_should_be_phrases(self):
        result = check(package(highlights="This dripper is made of stoneware. It fits most mugs."))
        self.assertEqual(len(entries(result, "H3", "WARN")), 1)
        result = check(package(highlights="Spiral ribs, single hole base, fits most mugs"))
        self.assertEqual([c["level"] for c in entries(result, "H3")], ["PASS"])

    def test_search_terms_rules(self):
        result = check(package(title="Brewlane Ceramic Dripper", params={"brand": "Brewlane"},
                               search_terms="Pourover cone, cone cups cup best ceramic brewlane b0abcd1234"))
        self.assertIn("ASIN", entries(result, "S3", "FAIL")[0]["measured"])
        self.assertIn("Brewlane", entries(result, "S3", "FAIL")[0]["measured"])
        self.assertEqual(entries(result, "S4", "WARN")[0]["measured"], "best")
        self.assertIn("有大写字母", entries(result, "S5", "WARN")[0]["measured"])
        self.assertIn(",", entries(result, "S5", "WARN")[0]["measured"])
        self.assertEqual(entries(result, "S6", "WARN")[0]["measured"], "cone ×2")
        self.assertEqual(entries(result, "S7", "WARN")[0]["measured"], "ceramic、brewlane")
        self.assertIn("浪费字节，不是违规", entries(result, "S7", "WARN")[0]["message"])
        self.assertEqual(entries(result, "S8", "WARN")[0]["measured"], "cups/cup")

    def test_non_english_downgrades_word_checks_only(self):
        title = "Brewlane Tasse Filter Tasse Keramik Tasse"
        self.assertEqual(len(entries(check(package(title=title)), "T3", "FAIL")), 1)
        result = check(package(title=title), lang="de-DE")
        self.assertEqual(entries(result, "T3", "FAIL"), [])
        self.assertIn(cl.NON_EN_NOTE, entries(result, "T3", "WARN")[0]["message"])
        result = check(package(title="Brewlane " + "x" * 80), lang="de-DE")
        self.assertEqual(len(entries(result, "T1", "FAIL")), 1, "length checks stay as they are")


class CharacterRuleTest(unittest.TestCase):
    def test_full_width_comma_is_cjk(self):
        title = "Brewlane Dripper" + chr(0xFF0C) + "White"
        found = entries(check(package(title=title)), "G3", "FAIL")
        self.assertEqual([c["field"] for c in found], ["Title"])
        result = check(package(title=title), lang="ja-JP")
        self.assertEqual(entries(result, "G3", "FAIL"), [])
        self.assertEqual(len(entries(result, "G3", "SKIP")), 1)
        self.assertEqual([c["level"] for c in entries(check(package(title="Brewlane Dripper, White")), "G3")], ["PASS"])

    def test_curly_quote_in_search_terms_mentions_the_byte_cost(self):
        result = check(package(search_terms="barista" + chr(0x2019) + "s tool"))
        warning = entries(result, "G4", "WARN")[0]
        self.assertEqual(warning["field"], "Search Terms")
        self.assertIn("3 字节", warning["message"])
        self.assertEqual(entries(result, "G3", "FAIL"), [], "curly quotes are a WARN, not CJK")
        title = check(package(title="Brewlane Dripper " + chr(0x2014) + " White"))
        self.assertNotIn("字节", entries(title, "G4", "WARN")[0]["message"])

    def test_spacing(self):
        result = check("### Title\n\nBrewlane  Ceramic Dripper \n")
        self.assertIn("连续空格", entries(result, "G5", "WARN")[0]["measured"])
        self.assertIn("行首或行尾有空格", entries(result, "G5", "WARN")[0]["measured"])

    def test_emoji_fails_and_is_reported_as_a_code_point(self):
        result = check(package(title="Brewlane Dripper " + chr(0x1F600)))
        self.assertEqual(entries(result, "G6", "FAIL")[0]["measured"], "U+1F600（共 1 个）")
        self.assertIsNone(cl.EMOJI_RE.search(cl.render_report(result)), "no emoji in the script's own output")

    def test_title_symbols(self):
        result = check(package(title="Brewlane Dripper_Set $9 {White}"))
        self.assertEqual(entries(result, "T2", "FAIL")[0]["measured"], "$ ×1、_ ×1、{ ×1、} ×1")
        self.assertIn("品牌字段", entries(result, "T2", "FAIL")[0]["message"])

    def test_placeholders(self):
        result = check(package(title="{{一行}}"))
        self.assertEqual(entries(result, "B4", "FAIL")[0]["message"], "占位符未填")
        self.assertEqual(entries(result, "T1"), [], "an unfilled field is not checked further")
        result = check(package(title="Brewlane {{color}} Dripper"))
        self.assertEqual(entries(result, "B4", "FAIL")[0]["field"], "Title")
        result = check(package(bullets=GOOD_BULLETS + ["Care instructions: N/A for now", "Origin: TBD by the factory"]))
        self.assertEqual([(c["field"], c["measured"]) for c in entries(result, "B4", "FAIL")],
                         [("Bullet 4", "N/A"), ("Bullet 5", "TBD")])
        result = check(package(bullets=GOOD_BULLETS + ["A banana scented glaze is not an option"]))
        self.assertEqual(entries(result, "B4", "FAIL"), [], "NA only counts as an upper-case whole word")

    def test_bullet_content_rules(self):
        bullets = [
            "Order at www.brewlane.example or write to help@brewlane.example today",
            "Eco-friendly glaze with a full refund if not satisfied",
            "glazed stoneware holds heat during the pour.",
            "Glazed stoneware holds heat during every pour",
            "Glazed  stoneware holds heat during every POUR",
            "Replaces model B0ABCD1234 from last year, see example.com",
            "Trademark sign" + chr(0x2122) + " and a tilde ~ in one line",
        ]
        result = check(package(bullets=bullets))
        b5 = dict((c["field"], c["measured"]) for c in entries(result, "B5", "FAIL"))
        self.assertEqual(sorted(b5), ["Bullet 1", "Bullet 6"])
        self.assertIn("邮箱 help@brewlane.example", b5["Bullet 1"])
        self.assertIn("网址 www.brewlane.example", b5["Bullet 1"])
        self.assertEqual(b5["Bullet 6"], "网址 example.com、ASIN B0ABCD1234")
        self.assertEqual([(c["field"], c["measured"]) for c in entries(result, "B6", "FAIL")],
                         [("Bullet 2", "eco friendly、full refund、if not satisfied")])
        self.assertEqual(entries(result, "B7", "FAIL")[0]["measured"], "Bullet 4 = Bullet 5")
        self.assertEqual([(c["field"], c["measured"]) for c in entries(result, "B8", "WARN")],
                         [("Bullet 3", "小写字母开头、结尾有标点 .")])
        self.assertEqual(entries(result, "B3", "FAIL")[0]["field"], "Bullet 7")
        self.assertEqual(len(entries(result, "B1b", "WARN")), 1)

    def test_description_rules(self):
        text = "<b>Brewlane</b> dripper.<br>Rinse after use.</br>See example.com or write to care@example.com"
        result = check(package(description=text))
        self.assertEqual(entries(result, "D2", "FAIL")[0]["measured"], "`<b>`、`</b>`")
        self.assertEqual(entries(result, "D3", "FAIL")[0]["measured"], "邮箱 care@example.com、网址 example.com")
        result = check(package(description="Plain words.<br/>More plain words. " + "x" * 2000))
        self.assertEqual([c["level"] for c in entries(result, "D2")], ["PASS"])
        self.assertEqual(len(entries(result, "D1", "WARN")), 1)
        self.assertEqual(result["summary"]["fail"], 0)


QA_HEADER = ("| 编号 | 问题 | 来源 | 优先级 | 有无依据 | 计划放哪 | 实际由哪句回答 | 判定 |\n"
             "|---|---|---|---|---|---|---|---|\n")


class StructureTest(unittest.TestCase):
    def test_verdicts_are_checked_only_after_the_second_pass(self):
        table = ("## 必答问题表\n\n" + QA_HEADER
                 + "| Q01 | What size filter? | 实采 | 高 | 有 | 标题 | | |\n"
                 + "| Q02 | Is the glaze tested? | 实采 | 中 | 无 | 不写 | | 不写 |\n")
        result = check(table)  # first pass: rows without evidence already say 不写, nothing else is judged yet
        self.assertEqual([c["level"] for c in entries(result, "X2b")], ["SKIP"])
        self.assertEqual(result["summary"]["fail"], 0)
        self.assertEqual(entries(check(table, full=True), "X2b", "FAIL")[0]["measured"], "Q01")
        started = table + "| Q03 | Dishwasher safe? | 评论 | 高 | 有 | 五点 | Bullet 3 | 已覆盖 |\n"
        self.assertEqual(entries(check(started), "X2b", "FAIL")[0]["measured"], "Q01")

    def test_unanswered_values_for_rows_without_evidence(self):
        rows = "".join("| Q%02d | Question %d? | 模拟 | 低 | 无 | 不写 | %s | 不写 |\n" % (i, i, answer)
                       for i, answer in enumerate(["", "—", "-", "无", "不写", "Bullet 2"], 1))
        result = check("## 必答问题表\n\n" + QA_HEADER + rows)
        self.assertEqual(entries(result, "X2c", "FAIL")[0]["measured"], "Q06")

    def test_unknown_evidence_value_warns(self):
        result = check("## 必答问题表\n\n" + QA_HEADER + "| Q01 | Size? | 实采 | 高 | maybe | 标题 | Title | 已覆盖 |\n")
        self.assertEqual(entries(result, "X2e", "WARN")[0]["measured"], "Q01")

    def test_verdict_keeps_its_meaning_when_a_reason_follows_it(self):
        # Writers append a reason after the verdict word; the leading word still decides.
        rows = ("| Q01 | Fits a door? | 实测 | 高 | 有 | 五点 | | 未覆盖，但影响不大 |\n"
                + "| Q02 | Pet safe? | 模拟 | 低 | 无 | 不写 | | 不写。没有检测报告 |\n"
                + "| Q03 | Machine washable? | 实测 | 高 | 有 | 五点 | Bullet 3 | 已覆盖 |\n")
        result = check("## 必答问题表\n\n" + QA_HEADER + rows)
        self.assertEqual(entries(result, "X2d", "WARN")[0]["measured"], "Q01")
        self.assertEqual(entries(result, "X2f", "PASS")[0]["level"], "PASS")

    def test_claims_table_with_evidence_silences_the_caution_word(self):
        copy = ("## Listing 文案\n\n### Title\n\nBrewlane Ceramic Dripper, 1-2 Cup, Matte White\n\n"
                "### Item Highlights\n\nSpiral ribs, single hole base, dishwasher safe stoneware\n\n")
        head = "## 宣称依据表\n\n| 依据 | 编号 | 买家能看到的宣称 | 出现位置 |\n|---|---|---|---|\n"
        self.assertEqual(ids(check(copy), "WARN"), ["G2"])
        backed = copy + head + "| 用户资料：洗碗机测试记录 | C01 | dishwasher safe | Item Highlights |\n"
        self.assertEqual(ids(check(backed), "WARN"), [])
        # 待核实 is not evidence yet, so the word still has to be questioned.
        unverified = copy + head + "| 待核实：供应商口头说的 | C01 | dishwasher safe | Item Highlights |\n"
        self.assertEqual(ids(check(unverified), "WARN"), ["G2"])

    def test_verdict_outside_the_four_values_warns(self):
        rows = ("| Q01 | Fits a door? | 实测 | 高 | 有 | 五点 | Bullet 1 | 回头再说 |\n"
                + "| Q02 | Pet safe? | 实测 | 高 | 有 | 五点 | Bullet 2 | 已覆盖 |\n")
        result = check("## 必答问题表\n\n" + QA_HEADER + rows)
        self.assertEqual(entries(result, "X2f", "WARN")[0]["measured"], "Q01")

    def test_backend_attributes_need_a_source_and_a_front_end_link(self):
        table = ("## 后台属性表\n\n| 属性 | 值 | 依据 | 对应前台哪句 |\n|---|---|---|---|\n"
                 "| Material | Faux Wool | 用户资料：规格表 | Bullet 4 |\n"
                 "| Pile Height | 0.2 in | — | Bullet 1 |\n"
                 "| Weave Type | Machine Made | 用户资料：规格表 | |\n")
        self.assertEqual(entries(check(table), "X8", "FAIL")[0]["measured"], "Pile Height")
        # 对应前台哪句 is filled during the check pass, so only a full check asks for it.
        self.assertEqual([c["level"] for c in entries(check(table), "X8b")], ["SKIP"])
        self.assertEqual(entries(check(table, full=True), "X8b", "WARN")[0]["measured"], "Weave Type")

    def test_visual_briefs_are_checked_only_when_present(self):
        shots = ("## 视频分镜表\n\n| 镜头 | 目的 | 画面 |\n|---|---|---|\n"
                 + "".join("| %d | 目的 | 画面 |\n" % i for i in range(1, 4)))
        board = "\n### 九宫格故事板描述\n\n" + "".join("%d. 第 %d 格画面\n" % (i, i) for i in range(1, 10))
        # No visual section at all: recorded as skipped, never as a problem.
        absent = [c for c in check("## 上架前待办\n\n无\n")["checks"] if c["id"].startswith("X9")]
        self.assertEqual(sorted(set(c["level"] for c in absent)), ["SKIP"])
        # Shot list without a storyboard, and with a storyboard that lost its cells.
        self.assertEqual(entries(check(shots), "X9b", "WARN")[0]["measured"], "没有")
        broken = shots + "\n### 九宫格故事板描述\n\n一行串进来的无关文字\n"
        self.assertEqual(entries(check(broken), "X9b", "WARN")[0]["measured"], "0 格")
        self.assertEqual(entries(check(shots + board), "X9b", "PASS")[0]["level"], "PASS")
        self.assertEqual(entries(check(shots + board), "X9", "PASS")[0]["measured"], "3 行")

    def test_tables_are_read_by_header_text_not_position(self):
        table = ("## 宣称依据表\n\n| 依据 | 编号 | 买家能看到的宣称 | 出现位置 |\n|---|---|---|---|\n"
                 "| 用户资料：规格表 | C01 | 1-2 Cup | Title |\n| — | C02 | dishwasher safe | Bullet 3 |\n"
                 "| 待核实 | C03 | holds heat | Bullet 3 |\n")
        self.assertEqual(entries(check(table), "X3", "FAIL")[0]["measured"], "C02")

    def test_renamed_table_header_is_reported_not_ignored(self):
        table = "## 宣称依据表\n\n| 编号 | 宣称 | 位置 | 证据 |\n|---|---|---|---|\n| C01 | 1-2 Cup | Title | 规格表 |\n"
        self.assertIn("表头被改过", entries(check(table), "X3", "FAIL")[0]["message"])

    def test_todo_section(self):
        copy = package(title="Brewlane Ceramic Dripper")
        self.assertEqual([c["level"] for c in entries(check(copy + "\n## 上架前待办\n\n无\n", full=True), "X4")], ["PASS"])
        self.assertEqual([c["level"] for c in entries(check(copy + "\n## 上架前待办\n\n", full=True), "X4")], ["FAIL"])
        self.assertEqual([c["level"] for c in entries(check(copy, full=True), "X4")], ["FAIL"])
        self.assertEqual([c["level"] for c in entries(check(copy), "X4")], ["SKIP"])

    def test_variation_rows_use_the_same_limits(self):
        table = ("## 变体差异表\n\n| 子体 | Title | Item Highlights | Search Terms | 本子体独有的事实 |\n|---|---|---|---|---|\n"
                 "| Large | %s | %s | %s | 大号 |\n" % ("T" * 76, "H" * 126, "s" * 250))
        found = entries(check(table), "X5", "FAIL")
        self.assertEqual([c["measured"] for c in found], ["76 字符", "126 字符", "250 字节"])
        self.assertTrue(all("Large" in c["field"] for c in found))
        exempt = check(table, title_limit_exempt=True)
        self.assertEqual([c["measured"] for c in entries(exempt, "X5", "FAIL")], ["126 字符", "250 字节"])

    def test_leftover_placeholders_outside_copy(self):
        text = package(title="Brewlane Ceramic Dripper", params={"brand": "{{品牌名}}"}) + (
            "\n## 后台属性表\n\n| 属性 | 值 | 依据 | 对应前台哪句 |\n|---|---|---|---|\n| Material | {{值}} | {{依据}} | Title |\n")
        warning = entries(check(text), "X6", "WARN")[0]
        self.assertIn("2 处", warning["measured"])

    def test_duplicate_section_warns(self):
        text = package(title="Brewlane Ceramic Dripper") + "\n### Title\n\n" + "X" * 90 + "\n"
        result = check(text)
        self.assertEqual(entries(result, "X7", "WARN")[0]["measured"], "Title")
        self.assertEqual(entries(result, "T1", "FAIL"), [], "only the first section is checked")


class ParsingTest(unittest.TestCase):
    def test_heading_aliases_in_any_case_and_level(self):
        text = ("## 标题\n\nBrewlane Ceramic Dripper\n\n# 商品亮点\n\nSpiral ribs, single hole base\n\n"
                "#### 五点\n\n- First bullet goes here\n* Second bullet goes here\n3) Third bullet goes here\n\n"
                "## DESCRIPTION\n\nPlain words.\n\n## 后台搜索词\n\npourover cone\n")
        doc = cl.Document(text)
        self.assertEqual(sorted(doc.sections), sorted(cl.COPY_KEYS))
        self.assertEqual(len(cl.extract_field(doc, "bullets").values), 3)
        for heading in ("Title", "TITLE", "**Title**", "Title:", "1. Title", "Title（标题）", "商品标题"):
            self.assertEqual(cl.heading_key(heading), "title", heading)
        for heading in ("Bullets", "商品要点", "bullet points"):
            self.assertEqual(cl.heading_key(heading), "bullets", heading)
        self.assertEqual(cl.heading_key("Search terms"), "search_terms")
        self.assertEqual(cl.heading_key("搜索词"), "search_terms")
        self.assertEqual(cl.heading_key("商品描述"), "description")
        self.assertIsNone(cl.heading_key("Listing 文案"))

    def test_section_ends_at_next_heading_of_same_or_higher_level(self):
        text = "### Title\n\nBrewlane Ceramic Dripper\n\n## 图片需求单\n\nnot a title line\n"
        result = check(text)
        self.assertEqual([c["level"] for c in entries(result, "T0")], ["PASS"])

    def test_more_than_one_line(self):
        text = ("### Title\n\nBrewlane Ceramic Dripper\nSecond line\n\n"
                "### Item Highlights\n\nSpiral ribs\nSingle hole\n\n"
                "### Search Terms\n\npourover cone\nmanual brewer\n")
        result = check(text)
        for cid in ("T0", "H0", "S2"):
            self.assertIn("应为一行", entries(result, cid, "FAIL")[0]["message"], cid)
        self.assertEqual(entries(result, "S2", "FAIL")[0]["measured"], "2 行")

    def test_comments_and_code_fences_are_ignored(self):
        text = ("### Title\n\n<!-- 24 characters -->\nBrewlane Ceramic Dripper <!-- draft 2 -->\n<!--\n"
                "### Bullet Points\n-->\n\n```\n### Search Terms\nnot a real section\n```\n")
        doc = cl.Document(text)
        self.assertEqual(list(doc.sections), ["title"])
        field = cl.extract_field(doc, "title")
        self.assertEqual((field.values, field.untidy), (["Brewlane Ceramic Dripper"], [False]))

    def test_value_wrapping_is_stripped(self):
        for raw in ("`Brewlane Ceramic Dripper`", '"Brewlane Ceramic Dripper"', "> Brewlane Ceramic Dripper",
                    "**Brewlane Ceramic Dripper**"):
            field = cl.extract_field(cl.Document("### Title\n\n%s\n" % raw), "title")
            self.assertEqual(field.values, ["Brewlane Ceramic Dripper"], raw)

    def test_copy_inside_a_code_fence_is_called_out(self):
        result = check("### Title\n\n```\nBrewlane Ceramic Dripper\n```\n")
        self.assertIn("代码块", entries(result, "B4", "FAIL")[0]["message"])

    def test_params_section(self):
        text = package(title="Brewlane Ceramic Dripper",
                       params={"marketplace": "DE", "language": "de-DE", "brand": "`Brewlane`",
                               "banned_terms": "glass, steel，plastic", "title_limit_exempt": "yes"})
        params = check(text)["params"]
        self.assertEqual(params, {"marketplace": "DE", "language": "de-DE", "brand": "Brewlane",
                                  "banned_terms": ["glass", "steel", "plastic"], "title_limit_exempt": True})
        defaults = check(package(title="Brewlane Ceramic Dripper"))["params"]
        self.assertEqual((defaults["language"], defaults["brand"], defaults["banned_terms"]), ("en-US", "", []))


class TempDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="check-listing-test-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, text, newline="\n"):
        path = os.path.join(self.tmp, name)
        with open(path, "wb") as handle:
            handle.write(text.replace("\n", newline).encode("utf-8"))
        return path

    def copy(self, name):
        path = os.path.join(self.tmp, name)
        shutil.copyfile(fixture(name), path)
        return path


LONG_TITLE = "Brewlane Ceramic Pour Over Coffee Dripper Set with Scoop and Paper Filter Holder, White"


class CliTest(TempDirTest):
    def test_default_output_layout(self):
        code, out, _err = run_cli(fixture("pass-full.md"), "--full")
        self.assertEqual(code, 0)
        lines = out.rstrip("\n").split("\n")
        self.assertRegex(lines[0], r"^结果：0 项不通过，1 项提醒 ｜ 文案指纹 [0-9a-f]{8} ｜ 规则核对日期 %s$" % cl.RULES_AS_OF)
        self.assertEqual(lines[1], "")
        self.assertEqual(lines[2], "| 级别 | 位置 | 检查项 | 实测 | 要求 |")
        self.assertEqual(lines[-1], "本脚本只查长度、字符、重复和表格是否齐全；不判断宣称真假、类目特殊规则和图片视频。")
        levels = [line.split("|")[1].strip() for line in lines[4:-2]]
        self.assertTrue(levels and set(levels) <= {"FAIL", "WARN", "INFO", "PASS", "SKIP"}, levels)

    def test_output_has_no_emoji_even_when_the_copy_does(self):
        code, out, _err = run_cli(fixture("fail-lengths-chars.md"))
        self.assertEqual(code, 1)
        self.assertIsNone(cl.EMOJI_RE.search(out))
        self.assertIn("U+2615", out)

    def test_json_output_shape(self):
        code, out, _err = run_cli(fixture("pass-full.md"), "--full", "--json")
        result = json.loads(out)  # stdout must be JSON and nothing else
        self.assertEqual(sorted(result), sorted(["script_version", "rules_as_of", "file", "mode", "params",
                                                 "fingerprint", "summary", "checks"]))
        self.assertEqual((result["script_version"], result["rules_as_of"], result["mode"]),
                         ("2.0.0", cl.RULES_AS_OF, "full"))
        self.assertRegex(result["fingerprint"], r"^[0-9a-f]{8}$")
        self.assertEqual(sorted(result["summary"]), ["fail", "info", "warn"])
        for entry in result["checks"]:
            self.assertEqual(sorted(entry), ["field", "id", "level", "limit", "measured", "message"])
            self.assertIn(entry["level"], ("FAIL", "WARN", "INFO", "PASS", "SKIP"))

    def test_several_files(self):
        code, out, _err = run_cli(fixture("pass-full.md"), fixture("variation.md"))
        self.assertEqual(code, 1, "the worst file decides the exit code")
        self.assertEqual(out.count("文件："), 2)
        code, out, _err = run_cli(fixture("pass-full.md"), fixture("variation.md"), "--json")
        results = [json.loads(line) for line in out.splitlines()]
        self.assertEqual([r["summary"]["fail"] for r in results], [0, 1])

    def test_stdin(self):
        text = package(title="Brewlane Ceramic Dripper", params={"brand": "Brewlane"})
        code, out, err = run_cli("-", stdin=text.encode("utf-8"))
        self.assertEqual(code, 0, err)
        self.assertIn("结果：0 项不通过", out)
        code, out, err = run_cli("-", "--write-report", stdin=text.encode("utf-8"))
        self.assertEqual((code, out), (2, ""))
        self.assertIn("--write-report", err)

    def test_title_limit_exempt(self):
        self.assertGreater(len(LONG_TITLE), cl.TITLE_MAX_CHARS)
        path = self.write("long.md", package(title=LONG_TITLE))
        code, result = run_json(path)
        self.assertEqual((code, [c["level"] for c in entries(result, "T1")]), (1, ["FAIL"]))
        code, result = run_json(path, "--title-limit-exempt")
        self.assertEqual((code, [c["level"] for c in entries(result, "T1")]), (0, ["INFO"]))
        self.assertTrue(result["params"]["title_limit_exempt"])
        in_file = self.write("long2.md", package(title=LONG_TITLE, params={"title_limit_exempt": "yes"}))
        code, result = run_json(in_file)
        self.assertEqual((code, [c["level"] for c in entries(result, "T1")]), (0, ["INFO"]))

    def test_exempt_title_does_not_block_highlights(self):
        text = package(title=LONG_TITLE, highlights="Spiral ribs, single hole base")
        self.assertEqual(len(entries(check(text), "H2", "WARN")), 1)
        self.assertEqual(entries(check(text, title_limit_exempt=True), "H2", "WARN"), [])

    def test_flags_override_the_params_section(self):
        path = self.write("p.md", package(title="Brewlane Ceramic Dripper",
                                          params={"brand": "Brewlane", "banned_terms": "ceramic", "language": "en-US"}))
        code, result = run_json(path)
        self.assertEqual((code, ids(result, "FAIL")), (1, ["G1"]))
        code, result = run_json(path, "--brand", "Otherbrand", "--banned", "glass, steel", "--lang", "de-DE")
        self.assertEqual(code, 0)
        self.assertEqual(result["params"]["brand"], "Otherbrand")
        self.assertEqual(result["params"]["banned_terms"], ["glass", "steel"])
        self.assertEqual(result["params"]["language"], "de-DE")
        self.assertEqual(len(entries(result, "T7", "WARN")), 1)

    def test_exit_code_2(self):
        notes = self.write("notes.md", "# Notes\n\n## Ideas\n\nNothing the checker knows about.\n")
        code, out, err = run_cli(notes)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("没找到能检查的小节标题", err)
        code, result = run_json(notes)
        self.assertEqual(code, 2)
        self.assertIn("error", result)
        only_params = self.write("params.md", package(params={"brand": "Brewlane"}))
        self.assertEqual(run_cli(only_params)[0], 2, "a file with nothing to check must not look like a pass")
        self.assertEqual(run_cli(os.path.join(self.tmp, "missing.md"))[0], 2)
        self.assertEqual(run_cli(self.tmp)[0], 2, "a directory is not a readable file")
        self.assertEqual(run_cli()[0], 2)
        self.assertEqual(run_cli(notes, "--no-such-flag")[0], 2)
        latin = os.path.join(self.tmp, "latin1.md")
        with open(latin, "wb") as handle:
            handle.write("### Title\n\nCaf\xe9 Dripper\n".encode("latin-1"))
        self.assertEqual(run_cli(latin)[0], 2)

    def test_a_bug_in_the_script_is_exit_2_not_a_fake_fail(self):
        original = cl.check_text
        cl.check_text = lambda *args, **kwargs: 1 / 0
        try:
            with contextlib.redirect_stderr(io.StringIO()) as err, contextlib.redirect_stdout(io.StringIO()) as out:
                code = cl.main([fixture("pass-full.md")])
        finally:
            cl.check_text = original
        self.assertEqual((code, out.getvalue()), (2, ""))
        self.assertIn("脚本内部出错", err.getvalue())

    def test_runs_from_any_directory_and_handles_bom_and_crlf(self):
        text = package(title="Brewlane Ceramic Dripper", search_terms="pourover cone")
        path = os.path.join(self.tmp, "bom.md")
        with open(path, "wb") as handle:
            handle.write(b"\xef\xbb\xbf" + text.replace("\n", "\r\n").encode("utf-8"))
        code, result = run_json("bom.md", cwd=self.tmp)
        self.assertEqual(code, 0)
        self.assertEqual(result["fingerprint"], check(text)["fingerprint"])
        self.assertEqual(ids(result, "WARN"), [])


class WriteReportTest(TempDirTest):
    def test_idempotent_and_touches_nothing_else(self):
        path = self.copy("pass-full.md")
        original = read(path)
        _code, before = run_json(path, "--full")
        code, out, _err = run_cli(path, "--full", "--write-report")
        self.assertEqual(code, 0)
        first = read(path)
        self.assertNotEqual(first, original)
        run_cli(path, "--full", "--write-report")
        self.assertEqual(read(path), first, "second run must not change the file")

        _code, after = run_json(path, "--full")
        self.assertEqual(after["fingerprint"], before["fingerprint"])
        self.assertEqual(after["summary"], before["summary"])

        head, rest = original.split("## 机器检查结果\n", 1)
        tail = rest[rest.index("## 人工判断检查"):]
        self.assertTrue(first.startswith(head + "## 机器检查结果\n"))
        self.assertTrue(first.endswith(tail))
        section = first[len(head):len(first) - len(tail)]
        self.assertNotIn("由脚本写入，不要手填", section)
        expected = "## 机器检查结果\n\n由 check_listing.py 写入，勿手改\n\n" + out.rstrip("\n") + "\n\n"
        self.assertEqual(section, expected)

    def test_appends_the_section_when_the_heading_is_missing(self):
        path = self.copy("partial-title-only.md")
        original = read(path)
        self.assertEqual(run_cli(path, "--write-report")[0], 0)
        first = read(path)
        self.assertTrue(first.startswith(original))
        self.assertEqual(first.count("## 机器检查结果"), 1)
        self.assertTrue(first.endswith(cl.FOOTER + "\n"))
        run_cli(path, "--write-report")
        self.assertEqual(read(path), first)
        self.assertEqual(run_json(path)[1]["fingerprint"], check(original)["fingerprint"])

    def test_report_with_failures_is_still_idempotent(self):
        path = self.copy("fail-lengths-chars.md")
        self.assertEqual(run_cli(path, "--write-report")[0], 1)
        first = read(path)
        self.assertEqual(run_cli(path, "--write-report")[0], 1)
        self.assertEqual(read(path), first)
        template = self.write("template.md", read(TEMPLATE))
        run_cli(template, "--write-report")
        first = read(template)
        run_cli(template, "--write-report")
        self.assertEqual(read(template), first)
        self.assertIn("X6", first)

    def test_braces_quoted_in_the_report_are_not_counted_as_leftovers(self):
        path = self.write("braces.md", package(title="Brewlane {{color}} Dripper"))
        run_cli(path, "--write-report")
        first = read(path)
        self.assertIn("{{", first.split("## 机器检查结果")[1], "the B4 row quotes the braces it found")
        run_cli(path, "--write-report")
        self.assertEqual(read(path), first)
        self.assertEqual([c["level"] for c in entries(check(first), "X6")], ["PASS"])

    def test_crlf_and_bom_survive(self):
        path = os.path.join(self.tmp, "crlf.md")
        with open(path, "wb") as handle:
            handle.write(b"\xef\xbb\xbf" + read(fixture("pass-full.md")).replace("\n", "\r\n").encode("utf-8"))
        self.assertEqual(run_cli(path, "--full", "--write-report")[0], 0)
        with open(path, "rb") as handle:
            data = handle.read()
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""), "no bare LF may appear in a CRLF file")
        self.assertIn(cl.REPORT_MARK.encode("utf-8"), data)
        run_cli(path, "--full", "--write-report")
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), data)

    def test_write_report_function_leaves_other_sections_alone(self):
        text = read(fixture("fail-structure.md"))
        result = check(text)
        updated = cl.write_report(text, result)
        self.assertTrue(updated.startswith(text))
        self.assertEqual(cl.write_report(updated, check(updated)), updated)


if __name__ == "__main__":
    unittest.main(verbosity=2)
