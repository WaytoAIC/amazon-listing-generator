#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanical checker for an Amazon listing package written in markdown.

It parses the deliverable defined by assets/listing-package-template.md and
checks lengths, characters, repeats and table completeness. It does not judge
whether claims are true, category-specific rules, or images and video.

Usage:
    python3 check_listing.py FILE [FILE ...] [--full] [--write-report] [--json]
                             [--brand X] [--banned "a, b"] [--lang en-US]
                             [--title-limit-exempt] [--version]

Exit codes: 0 = no FAIL; 1 = at least one FAIL; 2 = usage error, unreadable
file, or nothing checkable found in the file.

Python 3.8+, standard library only.
"""
import argparse
import hashlib
import json
import re
import sys
import traceback
import unicodedata

SCRIPT_VERSION = "2.0.0"

# --- Limits. Must equal the table "机器可读限值" in references/platform-rules.md
# (tests/run_tests.py verifies this). ---------------------------------------
RULES_AS_OF = "2026-09-18"
TITLE_MAX_CHARS = 75
ITEM_HIGHLIGHTS_MAX_CHARS = 125
BULLET_MIN_COUNT = 3
BULLET_MIN_CHARS = 10
BULLET_MAX_CHARS = 255
SEARCH_TERMS_MAX_BYTES = 249
DESCRIPTION_MAX_CHARS = 2000

FAIL, WARN, INFO, PASS, SKIP = "FAIL", "WARN", "INFO", "PASS", "SKIP"

FOOTER = "本脚本只查长度、字符、重复和表格是否齐全；不判断宣称真假、类目特殊规则和图片视频。"
REPORT_MARK = "由 check_listing.py 写入，勿手改"
NON_EN_NOTE = "非英语站点，词级检查仅供参考"
TABLE_HEADER = "| 级别 | 位置 | 检查项 | 实测 | 要求 |"

# --- Headings -------------------------------------------------------------
HEADING_ALIASES = {
    "title": ("title", "标题", "商品标题"),
    "highlights": ("item highlights", "商品亮点"),
    "bullets": ("bullet points", "bullets", "五点", "商品要点"),
    "description": ("product description", "description", "商品描述"),
    "search_terms": ("search terms", "后台搜索词", "搜索词"),
    "qa_table": ("必答问题表",),
    "claims_table": ("宣称依据表",),
    "todo": ("上架前待办",),
    "variation_table": ("变体差异表",),
    "keyword_table": ("关键词分配表",),
    "attr_table": ("后台属性表",),
    "params": ("检查参数",),
    "report": ("机器检查结果",),
}
ALIAS_TO_KEY = {alias: key for key, names in HEADING_ALIASES.items() for alias in names}
SECTION_LABEL = {
    "title": "Title",
    "highlights": "Item Highlights",
    "bullets": "Bullet Points",
    "description": "Product Description",
    "search_terms": "Search Terms",
    "qa_table": "必答问题表",
    "claims_table": "宣称依据表",
    "todo": "上架前待办",
    "variation_table": "变体差异表",
    "keyword_table": "关键词分配表",
    "attr_table": "后台属性表",
    "params": "检查参数",
    "report": "机器检查结果",
}
COPY_KEYS = ("title", "highlights", "bullets", "description", "search_terms")
# Sections the script actually inspects. A file with none of them is a usage error.
CHECKABLE_KEYS = COPY_KEYS + ("qa_table", "claims_table", "todo", "variation_table", "keyword_table")

# --- Word lists -----------------------------------------------------------
STOP_WORDS = frozenset(
    "a an the and or for with of in on to by at from as is are be this that it its "
    "your you not no into up out per".split()
)
TITLE_FORBIDDEN_CHARS = "!$?_{}^¬¦"
TITLE_MARK_CHARS = "™®©"
BULLET_FORBIDDEN_CHARS = "™®€…†‡¢£¥©±~"
TITLE_PROMO_PHRASES = (
    "best seller", "#1", "top rated", "free shipping", "on sale",
    "100% quality guaranteed", "100% guaranteed", "hot item",
)
TITLE_AMBIGUOUS_WORDS = ("best", "new", "sale", "free", "cheap", "cheapest")
SPELLED_NUMBERS = (
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve",
)
BULLET_PROHIBITED_PHRASES = (
    "eco friendly", "environmentally friendly", "anti bacterial", "anti microbial",
    "made from bamboo", "contains bamboo", "made from soy", "contains soy",
    "full refund", "money back", "unconditional guarantee", "if not satisfied",
    "satisfaction guaranteed",
)
SEARCH_TERM_SUBJECTIVE = ("new", "sale", "best", "cheapest", "cheap", "amazing", "latest", "hot")
CAUTION_TERMS = (
    "guaranteed", "guarantee", "cure", "cures", "treat", "treats", "prevent", "prevents",
    "fda", "medical grade", "certified", "warranty", "#1",
)
# Cell values that mean "nothing here".
DASH_VALUES = frozenset(("", "—", "——", "–", "-", "--", "/"))
NOT_ANSWERED_VALUES = DASH_VALUES | frozenset(("无", "不写"))
NO_EVIDENCE_VALUES = DASH_VALUES | frozenset(("无", "暂无", "没有", "n/a", "na", "none", "tbd"))

# --- Regexes --------------------------------------------------------------
TOKEN_RE = re.compile(r"[a-z0-9]+(?:['’-][a-z0-9]+)*")
TOKEN_RE_ANY_LANG = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*")
NUMERIC_TOKEN_RE = re.compile(r"[0-9]+(?:['’-][0-9]+)*")
PLACEHOLDER_ONLY_RE = re.compile(r"^\{\{.*\}\}$", re.S)
ASIN_RE = re.compile(r"\bB0[A-Z0-9]{8}\b")
ASIN_ANYCASE_RE = re.compile(r"\bB0[A-Z0-9]{8}\b", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL_RE = re.compile(
    r"(?:https?://|www\.)\S+|\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.(?:com|net|org|co)\b(?:\.[a-z]{2}\b)?",
    re.I,
)
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^<>]*>")
# Markdown emphasis or code marks left inside a copy line (whole-line wrapping is stripped earlier).
MARKDOWN_MARK_RES = (
    ("**", re.compile(r"\*\*")),
    ("__", re.compile(r"(?<![A-Za-z0-9])__|__(?![A-Za-z0-9])")),
    ("`", re.compile(r"`")),
)
HTML_BR_RE = re.compile(r"<\s*/?\s*br\s*/?\s*>", re.I)
PLACEHOLDER_WORD_RES = (
    ("N/A", re.compile(r"(?<![A-Za-z0-9])N/A(?![A-Za-z0-9])", re.I)),
    ("NA", re.compile(r"(?<![A-Za-z0-9/])NA(?![A-Za-z0-9/])")),
    ("TBD", re.compile(r"\bTBD\b", re.I)),
    ("TBA", re.compile(r"\bTBA\b", re.I)),
    ("copy pending", re.compile(r"\bcopy\s+pending\b", re.I)),
    ("not applicable", re.compile(r"\bnot\s+applicable\b", re.I)),
    ("to be decided", re.compile(r"\bto\s+be\s+decided\b", re.I)),
)
# Code points are written as numbers so the source never holds invisible characters.
# CJK scripts, CJK punctuation and full-width forms. Curly quotes are NOT here:
# Chinese and English typographic quotes share code points, so G4 reports them.
CJK_RANGES = (
    (0x1100, 0x11FF),    # Hangul Jamo
    (0x2E80, 0x2FDF),    # CJK radicals
    (0x3000, 0x30FF),    # CJK punctuation, Hiragana, Katakana
    (0x3100, 0x318F),    # Bopomofo, Hangul compatibility Jamo
    (0x31A0, 0x4DBF),    # strokes, enclosed and compatibility forms, Extension A
    (0x4E00, 0x9FFF),    # CJK unified ideographs
    (0xA960, 0xA97F),    # Hangul Jamo extended
    (0xAC00, 0xD7AF),    # Hangul syllables
    (0xF900, 0xFAFF),    # CJK compatibility ideographs
    (0xFE30, 0xFE4F),    # CJK compatibility forms
    (0xFF00, 0xFFEF),    # half-width and full-width forms
    (0x20000, 0x2FA1F),  # CJK Extension B and later
    (0x30000, 0x3134F),  # CJK Extension G
)
EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),  # pictographs, emoticons, transport, flags, supplemental symbols
    (0x2600, 0x27BF),    # miscellaneous symbols and dingbats
    (0x231A, 0x231B), (0x2328, 0x2328), (0x23CF, 0x23CF), (0x23E9, 0x23F3), (0x23F8, 0x23FA),
    (0x2B05, 0x2B07), (0x2B1B, 0x2B1C), (0x2B50, 0x2B50), (0x2B55, 0x2B55),
    (0xFE0F, 0xFE0F),    # emoji variation selector
    (0x200D, 0x200D),    # zero width joiner inside emoji sequences
    (0xE0020, 0xE007F),  # tag characters inside flag sequences
)
# (code point, what to do instead, name shown in the report)
TYPOGRAPHIC_CHARS = (
    (0x2019, "换成 '", "’"), (0x2018, "换成 '", "‘"), (0x201C, '换成 "', "“"), (0x201D, '换成 "', "”"),
    (0x2013, "换成 -", "–"), (0x2014, "换成 -", "—"),
    (0x00A0, "换成普通空格", "不换行空格 U+00A0"), (0x202F, "换成普通空格", "窄空格 U+202F"),
    (0x2009, "换成普通空格", "细空格 U+2009"), (0x200B, "删掉", "零宽空格 U+200B"),
    (0xFEFF, "删掉", "零宽字符 U+FEFF"),
)
# Separators treated as equal inside a banned term: whitespace, hyphen-minus,
# U+2010 hyphen and U+2011 non-breaking hyphen.
TERM_SEPARATORS = r"\s\-" + chr(0x2010) + chr(0x2011)


def _char_class(ranges):
    return "[%s]" % "".join("%s-%s" % (re.escape(chr(a)), re.escape(chr(b))) for a, b in ranges)


CJK_RE = re.compile(_char_class(CJK_RANGES))
EMOJI_RE = re.compile(_char_class(EMOJI_RANGES))


# --- Text helpers ---------------------------------------------------------
def nfc(text):
    return unicodedata.normalize("NFC", text)


def char_len(text):
    """Length in NFC-normalised code points."""
    return len(nfc(text))


def byte_len(text):
    """Length in UTF-8 bytes (spaces and punctuation included)."""
    return len(nfc(text).encode("utf-8"))


def byte_len_official(text):
    """UTF-8 bytes without whitespace and punctuation (how Amazon says it counts)."""
    kept = [c for c in nfc(text) if not c.isspace() and unicodedata.category(c)[0] not in "PZ"]
    return len("".join(kept).encode("utf-8"))


def is_placeholder_only(text):
    return bool(PLACEHOLDER_ONLY_RE.match(text.strip()))


def is_blank_value(text):
    """Empty, or still an untouched {{...}} placeholder."""
    stripped = text.strip()
    return not stripped or is_placeholder_only(stripped)


def strip_wrapping(text):
    """Remove surrounding backticks, quotes or ** from a value."""
    value = text.strip()
    pairs = (("`", "`"), ('"', '"'), ("'", "'"), ("“", "”"), ("‘", "’"), ("**", "**"))
    changed = True
    while changed and value:
        changed = False
        for left, right in pairs:
            inner = value[len(left):len(value) - len(right)]
            if (len(value) >= len(left) + len(right) and value.startswith(left)
                    and value.endswith(right) and left not in inner and right not in inner):
                value, changed = inner, True
                break
    return value


def tokenize(text, english=True):
    """Lowercase word tokens."""
    regex = TOKEN_RE if english else TOKEN_RE_ANY_LANG
    return regex.findall(nfc(text).lower())


def content_tokens(text, english=True):
    """Tokens that count for repeat/overlap checks: no stop-words, no bare numbers."""
    return [t for t in tokenize(text, english) if t not in STOP_WORDS and not NUMERIC_TOKEN_RE.fullmatch(t)]


def singular(token):
    """Very small s/es heuristic, good enough to pair 'cup' with 'cups'."""
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("es") and token[:-2].endswith(("s", "x", "z", "ch", "sh")):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def _is_cjk(ch):
    return bool(CJK_RE.match(ch))


_TERM_CACHE = {}


def term_regex(term):
    """Case-insensitive, word-boundary regex for a term.

    Space, hyphen and no separator are interchangeable between the parts, so
    "leak proof" also finds "leak-proof" and "leakproof". It never matches
    inside a longer word ("treat" does not hit "treatment").
    """
    if term in _TERM_CACHE:
        return _TERM_CACHE[term]
    parts = [p for p in re.split("[%s]+" % TERM_SEPARATORS, nfc(term).strip()) if p]
    regex = None
    if parts:
        body = ("[%s]*" % TERM_SEPARATORS).join(re.escape(p) for p in parts)
        first, last = parts[0][0], parts[-1][-1]
        head = r"(?<![^\W_])" if first.isalnum() and not _is_cjk(first) else ""
        tail = r"(?![^\W_])" if last.isalnum() and not _is_cjk(last) else ""
        regex = re.compile(head + body + tail, re.I)
    _TERM_CACHE[term] = regex
    return regex


def find_terms(text, terms):
    """Return [(term, span), ...] for every listed term found in text."""
    hits = []
    for term in terms:
        regex = term_regex(term)
        if regex is None:
            continue
        for match in regex.finditer(text):
            hits.append((term, match.span()))
    return hits


def term_names(hits):
    """Unique term names, in the order first seen."""
    return unique(term for term, _span in hits)


def blank_spans(text, spans):
    """Replace the given spans with spaces so later checks do not report them twice."""
    chars = list(text)
    for start, end in spans:
        for i in range(start, min(end, len(chars))):
            chars[i] = " "
    return "".join(chars)


def count_chars(text, chars):
    """Return [(char, count), ...] for the listed characters present in text."""
    return [(c, text.count(c)) for c in chars if c in text]


def fmt_counts(pairs):
    return "、".join("%s ×%d" % (name, n) for name, n in pairs)


def shorten(text, limit=60):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


# --- Markdown parsing -------------------------------------------------------
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
BULLET_RE = re.compile(r"^\s*(\d+[.)]|[-*])\s+")
BLOCKQUOTE_RE = re.compile(r"^\s*>\s?")
PARAM_RE = re.compile(r"^\s*(?:[-*+]\s+)?([A-Za-z_]+)\s*[:：]\s*(.*)$")
PARAM_KEYS = ("marketplace", "language", "brand", "banned_terms", "title_limit_exempt")
EMPTY_PARAM_VALUES = DASH_VALUES | frozenset(("无", "没有", "none", "n/a"))


def visible_lines(lines):
    """Copy of lines with fenced code blocks set to None and HTML comments removed."""
    out = list(lines)
    fence, fence_start = None, -1
    for i, line in enumerate(lines):
        match = FENCE_RE.match(line)
        if fence is None:
            if match:
                fence, fence_start = match.group(1), i
                out[i] = None
        else:
            out[i] = None
            if (match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence)
                    and not match.group(2).strip()):
                fence = None
    if fence is not None:
        # Unclosed fence: hiding the rest of the file would silently skip sections.
        for i in range(fence_start + 1, len(lines)):
            out[i] = lines[i]
    in_comment = False
    for i, line in enumerate(out):
        if line is None:
            continue
        kept, pos, touched = [], 0, in_comment
        while pos <= len(line):
            if in_comment:
                end = line.find("-->", pos)
                if end < 0:
                    break
                pos, in_comment = end + 3, False
            else:
                start = line.find("<!--", pos)
                if start < 0:
                    kept.append(line[pos:])
                    break
                kept.append(line[pos:start])
                pos, in_comment, touched = start + 4, True, True
        out[i] = "".join(kept).rstrip() if touched else line
    return out


def heading_key(text):
    """Map a heading text to a known section key, or None."""
    name = nfc(text).strip()
    name = re.sub(r"[*`]", "", name)
    name = re.sub(r"^(?:\d+|[一二三四五六七八九十]+)[.)、．]\s*", "", name)
    name = re.sub(r"\s+", " ", name).strip().rstrip(":：").strip().lower()
    if name in ALIAS_TO_KEY:
        return ALIAS_TO_KEY[name]
    bare = re.sub(r"\s*[（(][^（）()]*[）)]$", "", name).strip()
    return ALIAS_TO_KEY.get(bare)


class Section(object):
    def __init__(self, start, end, lines, had_fence):
        self.start = start      # index of the heading line
        self.end = end          # index of the first line after the section
        self.lines = lines      # visible, non-blank, non-heading content lines
        self.had_fence = had_fence


class Document(object):
    def __init__(self, text):
        self.raw_lines = [ln.rstrip("\r") for ln in text.split("\n")]
        self.visible = visible_lines(self.raw_lines)
        self.sections = {}
        self.duplicates = []
        headings = []
        for i, line in enumerate(self.visible):
            match = HEADING_RE.match(line) if line is not None else None
            if match:
                headings.append((i, len(match.group(1)), heading_key(match.group(2))))
        for n, (index, level, key) in enumerate(headings):
            if key is None:
                continue
            end = len(self.raw_lines)
            for index2, level2, key2 in headings[n + 1:]:
                # A known heading always starts a new section, whatever its level.
                if level2 <= level or key2 is not None:
                    end = index2
                    break
            if key in self.sections:
                if key not in self.duplicates:
                    self.duplicates.append(key)
                continue
            body = range(index + 1, end)
            lines = [self.visible[i] for i in body
                     if self.visible[i] is not None and self.visible[i].strip()
                     and not HEADING_RE.match(self.visible[i])]
            had_fence = any(self.visible[i] is None for i in body)
            self.sections[key] = Section(index, end, lines, had_fence)

    def has(self, key):
        return key in self.sections


def split_row(line):
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    return [cell.replace("\\|", "|").strip() for cell in re.split(r"(?<!\\)\|", text)]


def clean_header(text):
    return re.sub(r"[*`]", "", nfc(text)).strip().lower()


def parse_table(lines):
    """First markdown table in lines -> (headers, rows); each row is a dict by header."""
    for i in range(len(lines) - 1):
        if "|" in lines[i] and "-" in lines[i + 1] and TABLE_SEP_RE.match(lines[i + 1]):
            headers = [clean_header(h) for h in split_row(lines[i])]
            rows = []
            for line in lines[i + 2:]:
                if "|" not in line:
                    break
                cells = split_row(line)
                cells += [""] * (len(headers) - len(cells))
                rows.append(dict(zip(headers, (nfc(c) for c in cells))))
            return headers, rows
    return [], []


def data_rows(rows):
    """Drop rows that are still template rows: every cell except 编号 is blank or {{...}}."""
    return [row for row in rows
            if not all(is_blank_value(v) for h, v in row.items() if h != "编号")]


def find_column(headers, name):
    """Header equal to name, else the first header containing it, else None."""
    name = name.lower()
    if name in headers:
        return name
    for header in headers:
        if name in header:
            return header
    return None


def cell_value(row, column):
    """Cell text with placeholders treated as empty."""
    value = strip_wrapping(row.get(column, "")) if column else ""
    return "" if is_blank_value(value) else value.strip()


def parse_params(section):
    params = {}
    for line in (section.lines if section else []):
        match = PARAM_RE.match(line)
        if match and match.group(1).lower() in PARAM_KEYS:
            value = strip_wrapping(match.group(2))
            if is_blank_value(value) or value.strip().lower() in EMPTY_PARAM_VALUES:
                value = ""
            params[match.group(1).lower()] = nfc(value.strip())
    return params


def split_terms(text):
    return [t.strip() for t in re.split(r"[,，;；\n]", text or "") if t.strip()]


def is_yes(text):
    return (text or "").strip().lower() in ("yes", "y", "true", "1", "是")


class Field(object):
    """One copy field: the values to check plus notes about what was left out."""

    def __init__(self, key):
        self.key = key
        self.label = SECTION_LABEL[key]
        self.present = False
        self.values = []        # cleaned text, one entry per checked line / bullet
        self.untidy = []        # parallel to values: leading/trailing spaces were found
        self.positions = []     # bullets only: 1-based bullet number of each value
        self.placeholders = 0   # lines that are nothing but {{...}}
        self.other_lines = 0    # bullets only: lines without a list marker
        self.line_count = 0     # real (non-placeholder) lines found
        self.had_fence = False

    @property
    def text(self):
        """The field as one string (what goes into the fingerprint)."""
        if self.key == "search_terms":
            return " ".join(self.values)
        if self.key in ("title", "highlights"):
            return self.values[0] if self.values else ""
        return "\n".join(self.values)

    @property
    def filled(self):
        return bool(self.values)

    def add(self, raw):
        outer = nfc(raw)
        inner = strip_wrapping(outer.strip())
        self.values.append(inner.strip())
        self.untidy.append(outer != outer.strip() or inner != inner.strip())


def extract_field(doc, key):
    field = Field(key)
    section = doc.sections.get(key)
    if section is None:
        return field
    field.present = True
    field.had_fence = section.had_fence
    number = 0
    for line in section.lines:
        line = BLOCKQUOTE_RE.sub("", line, 1)
        if key == "bullets":
            match = BULLET_RE.match(line)
            if not match:
                field.other_lines += 1
                continue
            number += 1
            line = line[match.end():]
        if is_placeholder_only(line):
            field.placeholders += 1
            continue
        field.line_count += 1
        field.add(line)
        if key == "bullets":
            field.positions.append(number)
    if key in ("title", "highlights") and len(field.values) > 1:
        # Only the first line is checked; T0/H0 reports the extra lines.
        del field.values[1:], field.untidy[1:]
    return field


def fingerprint(fields):
    parts = [fields[key].text.strip() for key in COPY_KEYS]
    return hashlib.sha1(nfc("\n\n".join(parts)).encode("utf-8")).hexdigest()[:8]


# --- Results ----------------------------------------------------------------
class Report(object):
    """Collects check results. Every check that runs leaves at least one entry."""

    def __init__(self, english=True):
        self.english = english
        self.checks = []

    def add(self, cid, field, level, message, measured="", limit="", word_level=False):
        if word_level and not self.english and level in (FAIL, WARN):
            level = WARN
            message = "%s（%s）" % (message, NON_EN_NOTE)
        self.checks.append({"id": cid, "field": field, "level": level, "measured": str(measured),
                            "limit": str(limit), "message": message})
        return level

    def judge(self, cid, field, bad, level, name, measured="", limit="", hint="", word_level=False):
        """Record `level` when `bad` is truthy, PASS otherwise. Returns the level recorded."""
        if bad:
            message = "%s：%s" % (name, hint) if hint else name
            return self.add(cid, field, level, message, measured, limit, word_level)
        return self.add(cid, field, PASS, name, measured, limit)

    def count(self, level):
        return sum(1 for c in self.checks if c["level"] == level)


class Context(object):
    def __init__(self, params, full):
        self.params = params
        self.full = full
        self.brand = params["brand"]
        self.banned = params["banned_terms"]
        self.exempt = params["title_limit_exempt"]
        language = params["language"].lower()
        self.english = language.startswith("en")
        self.cjk_ok = language.startswith(("ja", "zh"))


def unique(items):
    seen = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen


def repeated_tokens(tokens, minimum):
    """[(token, count)] for tokens seen at least `minimum` times, in first-seen order."""
    counts = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return [(t, n) for t, n in counts.items() if n >= minimum]


def plural_groups(tokens):
    """{stem: {form: count}} for stems that appear in more than one form."""
    groups = {}
    for token in tokens:
        forms = groups.setdefault(singular(token), {})
        forms[token] = forms.get(token, 0) + 1
    return {stem: forms for stem, forms in groups.items() if len(forms) > 1}


def contact_hits(text, with_asin):
    """URLs, e-mail addresses and (optionally) ASIN-like tokens found in text."""
    emails = EMAIL_RE.findall(text)
    rest = EMAIL_RE.sub(" ", text)
    hits = ["邮箱 " + e for e in emails] + ["网址 " + u for u in URL_RE.findall(rest)]
    if with_asin:
        hits += ["ASIN " + a for a in ASIN_RE.findall(text)]
    return unique(hits)


# --- Checks: shape of each copy field -------------------------------------------
ONE_LINE_IDS = {"title": "T0", "highlights": "H0", "search_terms": "S2"}


def check_field_shape(rep, field):
    """Placeholder / empty / one-line checks. Returns True when there is text to check."""
    label = field.label
    if not field.filled:
        if field.placeholders:
            message, measured = "占位符未填", "%d 行占位符" % field.placeholders
        elif field.had_fence:
            message, measured = "内容为空：写在代码块里的内容脚本不读，去掉代码块围栏再查", "0 行"
        elif field.other_lines:
            message, measured = "没有找到条目：每条要以 1. 或 - 开头", "0 条"
        else:
            message, measured = "内容为空", "0 行"
        rep.add("B4", label, FAIL, message, measured, "填好，或整节删掉")
        return False
    if field.placeholders:
        rep.add("B4", label, FAIL, "还有占位符未填", "%d 行占位符" % field.placeholders, "填好或删掉")
    if field.key in ONE_LINE_IDS:
        extra = "其余检查按合并成一行算" if field.key == "search_terms" else "其余检查只看第一行"
        rep.judge(ONE_LINE_IDS[field.key], label, field.line_count > 1, FAIL, "%s 应为一行" % label,
                  "%d 行" % field.line_count, "1 行", hint=extra)
    if field.key == "bullets" and field.other_lines:
        rep.add("B0", label, INFO, "有些行不是以 1. 或 - 开头，没有当作五点检查",
                "%d 行" % field.other_lines, "每条以 1. 或 - 开头")
    return True


# --- Checks: Title ------------------------------------------------------------------
def check_title(rep, field, ctx):
    """Returns True when T1 failed (needed by H2)."""
    label, title = field.label, field.text
    length = char_len(title)
    over = length > TITLE_MAX_CHARS
    rep.judge("T1", label, over, INFO if ctx.exempt else FAIL, "标题长度", "%d 字符" % length,
              "不超过 %d 字符" % TITLE_MAX_CHARS, hint="已声明不受标题长度限制，仅提示" if ctx.exempt else "")

    found = count_chars(title, TITLE_FORBIDDEN_CHARS)
    rep.judge("T2", label, found, FAIL, "标题禁用符号", fmt_counts(found),
              "不用 " + " ".join(TITLE_FORBIDDEN_CHARS), hint="品牌名带这些字符时写进品牌字段，不写进标题")

    tokens = content_tokens(title, ctx.english)
    repeated = repeated_tokens(tokens, 3)
    rep.judge("T3", label, repeated, FAIL, "标题同一个词的次数", fmt_counts(repeated),
              "同一个词最多 2 次，品牌名也算", word_level=True)

    over_used = [t for t, _n in repeated]
    pairs = []
    for forms in plural_groups(tokens).values():
        total = sum(forms.values())
        if total > 2 and not any(f in over_used for f in forms):
            pairs.append(("/".join(forms), total))
    rep.judge("T3b", label, pairs, WARN, "标题单复数合计次数", fmt_counts(pairs),
              "单数和复数合计最多 2 次", word_level=True)

    promo = find_terms(title, TITLE_PROMO_PHRASES)
    rep.judge("T4", label, promo, FAIL, "标题促销语", "、".join(term_names(promo)), "不写促销语和自夸的话")

    rest_tokens = tokenize(blank_spans(title, [span for _t, span in promo]), ctx.english)
    ambiguous = [w for w in TITLE_AMBIGUOUS_WORDS if w in rest_tokens]
    rep.judge("T4b", label, ambiguous, WARN, "标题疑似促销或自夸的词", "、".join(ambiguous),
              "确认不是促销、自夸再保留", word_level=True)

    brand_tokens = set(tokenize(ctx.brand, False))
    shouting = [w for w in re.findall(r"[A-Za-z]{5,}", title) if w.isupper() and w.lower() not in brand_tokens]
    all_upper = title.isupper()
    rep.judge("T5", label, all_upper or len(shouting) >= 2, WARN, "标题大写",
              "整个标题全大写" if all_upper else "、".join(shouting), "每个词首字母大写，不全大写")

    numbers = [m.group(0) for m in re.finditer(r"\b(?:%s)\b" % "|".join(SPELLED_NUMBERS), title, re.I)]
    rep.judge("T6", label, numbers, WARN, "标题数字写法", "、".join(numbers), "用阿拉伯数字")

    if ctx.brand:
        brand_regex = term_regex(ctx.brand)  # tolerant of case and of space / hyphen differences
        starts = bool(brand_regex.match(title)) if brand_regex else title.casefold().startswith(ctx.brand.casefold())
        rep.judge("T7", label, not starts, WARN, "标题以品牌名开头", shorten(title, 30), "以 %s 开头" % ctx.brand)
    else:
        rep.add("T7", label, SKIP, "没给品牌名，没查标题是否以品牌名开头")

    marks = count_chars(title, TITLE_MARK_CHARS)
    rep.judge("T8", label, marks, WARN, "标题商标符号", fmt_counts(marks), "不写 ™ ® ©")
    return over and not ctx.exempt


# --- Checks: Item Highlights ----------------------------------------------------------
def check_highlights(rep, field, title_field, t1_failed, ctx):
    label, text = field.label, field.text
    length = char_len(text)
    rep.judge("H1", label, length > ITEM_HIGHLIGHTS_MAX_CHARS, FAIL, "Item Highlights 长度",
              "%d 字符" % length, "不超过 %d 字符" % ITEM_HIGHLIGHTS_MAX_CHARS)

    reasons = []
    if text.endswith("."):
        reasons.append("以句号结尾")
    if re.search(r"\.\s+[A-Z]", text):
        reasons.append("句号后接大写开头")
    if any(len(phrase.split()) > 10 for phrase in text.split(",")):
        reasons.append("有超过 10 个词的短语")
    rep.judge("H3", label, reasons, WARN, "Item Highlights 写成短语", "、".join(reasons), "写成逗号分隔的短语")

    if not title_field.filled:
        rep.add("H2", label, SKIP, "没有标题，没查“标题先达标才能添加”和与标题的重复")
        return
    rep.judge("H2", label, t1_failed, WARN, "标题先达标才能添加 Item Highlights",
              "标题 %d 字符" % char_len(title_field.text), "标题不超过 %d 字符" % TITLE_MAX_CHARS)
    title_tokens = set(content_tokens(title_field.text, ctx.english))
    shared = unique(t for t in content_tokens(text, ctx.english) if t in title_tokens)
    rep.judge("H4", label, shared, WARN, "Item Highlights 与标题的重复词", "、".join(shared),
              "一个词只占一个位置", word_level=True)


# --- Checks: Bullet Points --------------------------------------------------------------
def check_bullets(rep, field, ctx):
    label = field.label
    count = len(field.values)
    rep.judge("B1", label, count < BULLET_MIN_COUNT, FAIL, "五点条数", "%d 条" % count,
              "至少 %d 条" % BULLET_MIN_COUNT)
    rep.judge("B1b", label, count != 5, WARN, "五点写满 5 条", "%d 条" % count, "建议写满 5 条")

    def each(cid, level, name, limit, finder, hint=""):
        found = False
        for position, value in zip(field.positions, field.values):
            measured = finder(value)
            if measured:
                found = True
                rep.judge(cid, "Bullet %d" % position, True, level, name, measured, limit, hint)
        if not found:
            rep.judge(cid, label, False, level, name, "", limit)

    def length_problem(value):
        length = char_len(value)
        return "%d 字符" % length if not BULLET_MIN_CHARS <= length <= BULLET_MAX_CHARS else ""

    def ending_problem(value):
        reasons = []
        if value[:1].islower():
            reasons.append("小写字母开头")
        if value.endswith((".", "!", "。")):
            reasons.append("结尾有标点 " + value[-1])
        return "、".join(reasons)

    each("B2", FAIL, "单条五点长度", "%d 到 %d 字符" % (BULLET_MIN_CHARS, BULLET_MAX_CHARS), length_problem)
    each("B3", FAIL, "五点禁用字符", "不用 " + " ".join(BULLET_FORBIDDEN_CHARS),
         lambda v: fmt_counts(count_chars(v, BULLET_FORBIDDEN_CHARS)))
    each("B5", FAIL, "五点里的 ASIN、网址或邮箱", "不写 ASIN、链接和联系方式",
         lambda v: "、".join(contact_hits(v, with_asin=True)))
    each("B6", FAIL, "五点里官方禁止的说法", "不写环保、抗菌、竹或大豆成分、退款保证这类说法",
         lambda v: "、".join(term_names(find_terms(v, BULLET_PROHIBITED_PHRASES))))

    groups = {}
    for position, value in zip(field.positions, field.values):
        groups.setdefault(" ".join(value.lower().split()), []).append(position)
    twins = [" = ".join("Bullet %d" % p for p in ps) for ps in groups.values() if len(ps) > 1]
    rep.judge("B7", label, twins, FAIL, "五点各条不重复", "；".join(twins), "各条内容不重复")

    each("B8", WARN, "五点开头和结尾", "大写字母开头，结尾不加标点", ending_problem)


# --- Checks: Product Description ----------------------------------------------------------
def check_description(rep, field, ctx):
    label, text = field.label, field.text
    length = char_len(text)
    rep.judge("D1", label, length > DESCRIPTION_MAX_CHARS, WARN, "商品描述长度", "%d 字符" % length,
              "不超过 %d 字符" % DESCRIPTION_MAX_CHARS)
    tags = unique(t for t in HTML_TAG_RE.findall(text) if not HTML_BR_RE.fullmatch(t))
    rep.judge("D2", label, tags, FAIL, "商品描述里的 HTML 标签", "、".join("`%s`" % t for t in tags[:5]),
              "不用 HTML，只有换行 `<br>` 例外")
    contacts = contact_hits(text, with_asin=False)
    rep.judge("D3", label, contacts, FAIL, "商品描述里的网址或邮箱", "、".join(contacts), "不写网址和联系方式")
    asins = unique(ASIN_RE.findall(text))
    rep.judge("B5", label, asins, FAIL, "商品描述里的 ASIN", "、".join(asins), "不写 ASIN")


# --- Checks: Search Terms -------------------------------------------------------------------
def check_search_terms(rep, field, fields, ctx):
    label, text = field.label, field.text
    total = byte_len(text)
    rep.judge("S1", label, total > SEARCH_TERMS_MAX_BYTES, FAIL, "Search Terms 长度", "%d 字节" % total,
              "不超过 %d 字节，空格和标点也算" % SEARCH_TERMS_MAX_BYTES)
    rep.add("S1", label, INFO, "去掉空格和标点后的长度（官方计长不算空格和标点）",
            "%d 字节" % byte_len_official(text), "仅供参考")

    hits = []
    if ctx.brand and term_regex(ctx.brand) is not None and term_regex(ctx.brand).search(text):
        hits.append("品牌名 " + ctx.brand)
    hits += ["ASIN " + a for a in unique(ASIN_ANYCASE_RE.findall(text))]
    rep.judge("S3", label, hits, FAIL, "Search Terms 里的品牌名和 ASIN", "、".join(hits),
              "不写品牌名和 ASIN" + ("" if ctx.brand else "（没给品牌名，只查了 ASIN）"))

    all_tokens = tokenize(text, ctx.english)
    subjective = [w for w in SEARCH_TERM_SUBJECTIVE if w in all_tokens]
    rep.judge("S4", label, subjective, WARN, "Search Terms 里的时效词和主观词", "、".join(subjective),
              "不写 new、best、cheap 这类词")

    problems = []
    if any(c.isupper() for c in text):
        problems.append("有大写字母")
    marks = unique(c for c in text if unicodedata.category(c)[0] in "PS" and c not in "-'’"
                   and not EMOJI_RE.match(c))
    if marks:
        problems.append("有标点 " + " ".join(marks[:8]))
    rep.judge("S5", label, problems, WARN, "Search Terms 格式", "、".join(problems),
              "全小写，空格分隔，只留连字符和撇号")

    tokens = content_tokens(text, ctx.english)
    doubled = repeated_tokens(tokens, 2)
    rep.judge("S6", label, doubled, WARN, "Search Terms 内部重复的词", fmt_counts(doubled), "每个词只写一次",
              word_level=True)

    front = set()
    for key in ("title", "highlights", "bullets"):
        front.update(content_tokens(fields[key].text, ctx.english))
    wasted = unique(t for t in tokens if t in front)
    rep.judge("S7", label, wasted, WARN, "Search Terms 与前台文案的重复词", "、".join(wasted),
              "标题、Item Highlights、五点里有的词不用再写", hint="浪费字节，不是违规", word_level=True)

    pairs = ["/".join(forms) for forms in plural_groups(tokens).values()]
    rep.judge("S8", label, pairs, WARN, "Search Terms 单复数同时出现", "、".join(pairs), "单数和复数只留一个",
              word_level=True)


# --- Checks: across all copy (B4, G1-G6) ---------------------------------------------------------
def copy_units(fields):
    """[(location, field key, text, untidy)] for every filled piece of copy."""
    units = []
    for key in COPY_KEYS:
        field = fields[key]
        if not field.filled:
            continue
        if key == "bullets":
            for position, value, untidy in zip(field.positions, field.values, field.untidy):
                units.append(("Bullet %d" % position, key, value, untidy))
        else:
            units.append((field.label, key, field.text, any(field.untidy)))
    return units


def check_copy_wide(rep, fields, ctx):
    units = copy_units(fields)
    if not units:
        return
    everywhere = "全部文案"

    def each(cid, level, name, limit, finder, hint="", word_level=False):
        found = False
        for location, key, text, untidy in units:
            measured = finder(key, text, untidy)
            if measured:
                found = True
                extra = hint(key) if callable(hint) else hint
                rep.judge(cid, location, True, level, name, measured, limit, extra, word_level)
        if not found:
            rep.judge(cid, everywhere, False, level, name, "", limit)

    def placeholders(_key, text, _untidy):
        hits = ["{{ ×%d" % text.count("{{")] if "{{" in text else []
        hits += [name for name, regex in PLACEHOLDER_WORD_RES if regex.search(text)]
        return "、".join(hits)

    def banned(_key, text, _untidy):
        return "、".join(term_names(find_terms(text, ctx.banned)))

    def caution(key, text, _untidy):
        # Do not repeat what T4 (title) or B6 (bullets) already reported as FAIL.
        already = {"title": TITLE_PROMO_PHRASES, "bullets": BULLET_PROHIBITED_PHRASES}.get(key, ())
        rest = blank_spans(text, [span for _t, span in find_terms(text, already)])
        return "、".join(term_names(find_terms(rest, CAUTION_TERMS)))

    def cjk(_key, text, _untidy):
        found = CJK_RE.findall(text)
        return "%s（共 %d 个）" % (" ".join(unique(found)[:6]), len(found)) if found else ""

    def typographic(_key, text, _untidy):
        return "、".join("%s ×%d（%s）" % (name, text.count(chr(code)), advice)
                        for code, advice, name in TYPOGRAPHIC_CHARS if chr(code) in text)

    def spacing(_key, text, untidy):
        reasons = ["行首或行尾有空格"] if untidy else []
        doubles = len(re.findall(r" {2,}|\t", text))
        if doubles:
            reasons.append("连续空格 ×%d" % doubles)
        return "、".join(reasons)

    def markdown_marks(_key, text, _untidy):
        found = [(mark, len(regex.findall(text))) for mark, regex in MARKDOWN_MARK_RES]
        return fmt_counts([(mark, n) for mark, n in found if n])

    def emoji(_key, text, _untidy):
        found = EMOJI_RE.findall(text)
        return "%s（共 %d 个）" % (" ".join("U+%04X" % ord(c) for c in unique(found)[:6]), len(found)) if found else ""

    each("B4", FAIL, "占位文字", "不留双花括号、N/A、TBD 这类占位文字", placeholders)
    if ctx.banned:
        each("G1", FAIL, "用户禁用词", "不出现：" + "、".join(ctx.banned), banned)
    else:
        rep.add("G1", everywhere, SKIP, "没给用户禁用词，没查")
    each("G2", WARN, "需要依据的词", "对照宣称依据表，拿不出依据就删", caution, hint="需要有依据才可保留",
         word_level=True)
    if ctx.cjk_ok:
        rep.add("G3", everywhere, SKIP, "日语或中文站点，没查中日韩字符和全角符号")
    else:
        each("G3", FAIL, "中日韩字符和全角符号", "只用半角字符", cjk)
    each("G4", WARN, "弯引号、长横线、特殊空格", "只用键盘上的直引号、短横线和普通空格", typographic,
         hint=lambda key: "在 Search Terms 里弯引号和长横线每个占 3 字节，直引号和短横线只占 1 字节"
         if key == "search_terms" else "")
    each("G5", WARN, "多余的空格", "词之间一个空格，行首行尾不留空格", spacing)
    each("G6", FAIL, "表情符号", "不用表情符号", emoji)
    each("G7", WARN, "文案里的 Markdown 记号", "删掉；会被原样贴进后台，也算长度", markdown_marks)


# --- Checks: tables and structure (X*) ------------------------------------------------------------
REQUIRED_IN_FULL = ("title", "highlights", "bullets", "search_terms", "keyword_table", "qa_table",
                    "claims_table", "todo")
MISSING_ID = {"title": "X1", "highlights": "X1", "bullets": "X1", "search_terms": "X1", "keyword_table": "X1",
              "qa_table": "X2", "claims_table": "X3", "todo": "X4", "description": "D1", "variation_table": "X5"}
MISSING_MESSAGE = "文件里没有这个小节"


def check_missing_sections(rep, doc, ctx):
    for key in CHECKABLE_KEYS:
        if doc.has(key):
            continue
        required = ctx.full and key in REQUIRED_IN_FULL
        if required and key == "highlights":
            # Item Highlights is still rolling out by product type, so a missing section only warns.
            rep.add("X1", SECTION_LABEL[key], WARN, "没有 Item Highlights 小节", "没有",
                    "类目支持就补上；个别商品类型暂不支持，可以不写")
            continue
        rep.add(MISSING_ID[key], SECTION_LABEL[key], FAIL if required else SKIP,
                "缺少必需的小节" if required else MISSING_MESSAGE, "没有", "完整检查时必须有" if required else "")


def row_name(row, column, index):
    return cell_value(row, column) or "第 %d 行" % (index + 1)


def evidence_kind(value):
    text = value.strip().lower()
    if text.startswith("部分") or text in ("partial", "partly"):
        return "部分"
    if text.startswith(("无", "没有")) or text in ("no", "none"):
        return "无"
    if text.startswith("有") or text == "yes":
        return "有"
    return ""


def table_is_empty(rep, cid, label, rows, ctx):
    """Record whether the table has data rows. Returns True when there is nothing to check."""
    if rows:
        rep.add(cid, label, PASS, "表里有数据行", "%d 行" % len(rows), "至少 1 行")
        return False
    if ctx.full:
        rep.add(cid, label, FAIL, "表里没有数据行", "0 行", "至少 1 行")
    else:
        rep.add(cid, label, SKIP, "表里还没有数据行，没查")
    return True


def check_keyword_table(rep, doc, ctx):
    rows = data_rows(parse_table(doc.sections["keyword_table"].lines)[1])
    table_is_empty(rep, "X1", SECTION_LABEL["keyword_table"], rows, ctx)


def check_qa_table(rep, doc, ctx):
    label = SECTION_LABEL["qa_table"]
    headers, rows = parse_table(doc.sections["qa_table"].lines)
    rows = data_rows(rows)
    if table_is_empty(rep, "X2", label, rows, ctx):
        return
    names = ("编号", "有无依据", "实际由哪句回答", "判定")
    cols = {name: find_column(headers, name) for name in names}
    lost = [name for name in names[1:] if cols[name] is None]
    if lost:
        rep.add("X2", label, FAIL, "表头被改过，找不到这些列", "、".join(lost), "不要改表头")
        return
    table = [(row_name(row, cols["编号"], i), evidence_kind(cell_value(row, cols["有无依据"])),
              cell_value(row, cols["实际由哪句回答"]), cell_value(row, cols["判定"])) for i, row in enumerate(rows)]

    # The table is filled in two passes. Rows without evidence already get 判定 = 不写 in the
    # first pass, so only another verdict shows that the second pass has started.
    if ctx.full or any(verdict not in ("", "不写") for _n, _k, _a, verdict in table):
        unjudged = [name for name, kind, _a, verdict in table if kind in ("有", "部分") and not verdict]
        rep.judge("X2b", label, unjudged, FAIL, "有依据的问题要填判定", "、".join(unjudged),
                  "有无依据是 有 / 部分 的行都要填判定")
    else:
        rep.add("X2b", label, SKIP, "判定列还没开始填（写完文案再填），这一项先不查")
    answered = [name for name, kind, answer, _v in table if kind == "无" and answer not in NOT_ANSWERED_VALUES]
    rep.judge("X2c", label, answered, FAIL, "没依据的问题不回答", "、".join(answered),
              "有无依据是 无 的行，“实际由哪句回答”留空或写 不写")
    uncovered = [name for name, _k, _a, verdict in table if verdict == "未覆盖"]
    rep.judge("X2d", label, uncovered, WARN, "判定为未覆盖的问题", "、".join(uncovered), "补进文案，或改成 不写 并说明")
    unknown = [name for name, kind, _a, _v in table if not kind]
    rep.judge("X2e", label, unknown, WARN, "有无依据的取值", "、".join(unknown), "只填 有 / 部分 / 无")


def check_claims_table(rep, doc, ctx):
    label = SECTION_LABEL["claims_table"]
    headers, rows = parse_table(doc.sections["claims_table"].lines)
    rows = data_rows(rows)
    if table_is_empty(rep, "X3", label, rows, ctx):
        return
    column = "依据" if "依据" in headers else None
    if column is None:
        rep.add("X3", label, FAIL, "表头被改过，找不到这一列", "依据", "不要改表头")
        return
    id_column = find_column(headers, "编号")
    bare = [row_name(row, id_column, i) for i, row in enumerate(rows)
            if cell_value(row, column).lower() in NO_EVIDENCE_VALUES]
    rep.judge("X3", label, bare, FAIL, "每条宣称都有依据", "、".join(bare), "每条宣称都写依据；没核实的写 待核实")


def check_todo(rep, doc, ctx):
    label = SECTION_LABEL["todo"]
    lines = doc.sections["todo"].lines
    rows = data_rows(parse_table(lines)[1])
    notes = [ln for ln in lines if "|" not in ln and not is_blank_value(ln)]
    if rows or notes:
        rep.add("X4", label, PASS, "上架前待办已填", "%d 行事项" % len(rows), "列出事项；没有就写 无")
    elif ctx.full:
        rep.add("X4", label, FAIL, "上架前待办没填", "0 行事项", "列出事项；没有就写 无")
    else:
        rep.add("X4", label, SKIP, "上架前待办还没填，没查")


def check_variation_table(rep, doc, ctx):
    label = SECTION_LABEL["variation_table"]
    headers, rows = parse_table(doc.sections["variation_table"].lines)
    rows = data_rows(rows)
    if not rows:
        rep.add("X5", label, SKIP, "变体差异表没有数据行，没查")
        return
    name_column = find_column(headers, "子体")
    rules = (
        ("title", "子体标题长度", char_len, TITLE_MAX_CHARS, "字符", INFO if ctx.exempt else FAIL),
        ("item highlights", "子体 Item Highlights 长度", char_len, ITEM_HIGHLIGHTS_MAX_CHARS, "字符", FAIL),
        ("search terms", "子体 Search Terms 长度", byte_len, SEARCH_TERMS_MAX_BYTES, "字节", FAIL),
    )
    columns = [(find_column(headers, rule[0]), rule) for rule in rules]
    lost = [rule[0] for column, rule in columns if column is None]
    if lost:
        rep.add("X5", label, FAIL, "表头被改过，找不到这些列", "、".join(lost), "不要改表头")
    found = False
    for i, row in enumerate(rows):
        location = "%s · %s" % (label, row_name(row, name_column, i))
        for column, (_header, name, measure, maximum, unit, level) in columns:
            value = cell_value(row, column)
            if value and measure(value) > maximum:
                found = True
                rep.add("X5", location, level, name, "%d %s" % (measure(value), unit), "不超过 %d %s" % (maximum, unit))
    if not found and not lost:
        rep.add("X5", label, PASS, "各子体的标题、Item Highlights、Search Terms 长度", "%d 个子体" % len(rows))


def check_leftovers(rep, doc):
    skip = set()
    for key in COPY_KEYS + ("params", "report"):
        section = doc.sections.get(key)
        if section is not None:
            skip.update(range(section.start, section.end))
    hits = [(i + 1, line.count("{{")) for i, line in enumerate(doc.raw_lines) if i not in skip and "{{" in line]
    total = sum(n for _line, n in hits)
    where = "、".join(str(line) for line, _n in hits[:5])
    measured = "%d 处（在第 %s 行%s）" % (total, where, "等" if len(hits) > 5 else "") if total else "0 处"
    rep.judge("X6", "文案以外", total, WARN, "还有占位符没填", measured, "填好，或把没用到的小节整节删掉")
    if doc.duplicates:
        rep.add("X7", "整份文件", WARN, "同名小节出现多次，只检查了第一处",
                "、".join(SECTION_LABEL[k] for k in doc.duplicates), "每个小节只留一个")


# --- Running all checks on one document -------------------------------------------------------------
class NothingToCheck(Exception):
    """The text has none of the headings this script knows how to check."""


def resolve_params(file_params, overrides):
    """Command-line flags win over the 检查参数 section."""
    brand = overrides.get("brand")
    if brand is None:
        brand = file_params.get("brand", "")
    banned = overrides.get("banned")
    if banned is None:
        banned = file_params.get("banned_terms", "")
    return {
        "marketplace": file_params.get("marketplace", ""),
        "language": (overrides.get("lang") or file_params.get("language", "") or "en-US").strip(),
        "brand": nfc(brand.strip()),
        "banned_terms": split_terms(nfc(banned)),
        "title_limit_exempt": (bool(overrides.get("title_limit_exempt"))
                               or is_yes(file_params.get("title_limit_exempt"))),
    }


def check_text(text, file_label="-", full=False, overrides=None):
    """Check one package. Returns the result dict that --json prints."""
    doc = Document(text)
    if not any(doc.has(key) for key in CHECKABLE_KEYS):
        raise NothingToCheck(file_label)
    params = resolve_params(parse_params(doc.sections.get("params")), overrides or {})
    ctx = Context(params, full)
    rep = Report(ctx.english)
    fields = dict((key, extract_field(doc, key)) for key in COPY_KEYS)

    check_missing_sections(rep, doc, ctx)
    ready = dict((key, fields[key].present and check_field_shape(rep, fields[key])) for key in COPY_KEYS)
    t1_failed = check_title(rep, fields["title"], ctx) if ready["title"] else False
    if ready["highlights"]:
        check_highlights(rep, fields["highlights"], fields["title"], t1_failed, ctx)
    if ready["bullets"]:
        check_bullets(rep, fields["bullets"], ctx)
    if ready["description"]:
        check_description(rep, fields["description"], ctx)
    if ready["search_terms"]:
        check_search_terms(rep, fields["search_terms"], fields, ctx)
    check_copy_wide(rep, fields, ctx)
    for key, check in (("keyword_table", check_keyword_table), ("qa_table", check_qa_table),
                       ("claims_table", check_claims_table), ("todo", check_todo),
                       ("variation_table", check_variation_table)):
        if doc.has(key):
            check(rep, doc, ctx)
    check_leftovers(rep, doc)

    return {
        "script_version": SCRIPT_VERSION,
        "rules_as_of": RULES_AS_OF,
        "file": file_label,
        "mode": "full" if full else "partial",
        "params": params,
        "fingerprint": fingerprint(fields),
        "summary": {"fail": rep.count(FAIL), "warn": rep.count(WARN), "info": rep.count(INFO)},
        "checks": rep.checks,
    }


# --- Output ---------------------------------------------------------------------------------------
def summary_line(result):
    summary = result["summary"]
    return "结果：%d 项不通过，%d 项提醒 ｜ 文案指纹 %s ｜ 规则核对日期 %s" % (
        summary["fail"], summary["warn"], result["fingerprint"], result["rules_as_of"])


def table_row(*cells):
    cleaned = [" ".join(str(c).split()).replace("|", "\\|") or "—" for c in cells]
    return "| " + " | ".join(cleaned) + " |"


def table_lines(result):
    checks = result["checks"]
    lines = [TABLE_HEADER, "|---|---|---|---|---|"]
    for level in (FAIL, WARN, INFO):
        for c in checks:
            if c["level"] == level:
                lines.append(table_row(level, c["field"], "%s %s" % (c["id"], c["message"]), c["measured"], c["limit"]))
    if not result["summary"]["fail"] and not result["summary"]["warn"]:
        lines.append(table_row(PASS, "已检查的小节", "没有发现问题", "", ""))
    skipped = [c for c in checks if c["level"] == SKIP]
    missing = [c["field"] for c in skipped if c["message"] == MISSING_MESSAGE]
    if missing:
        lines.append(table_row(SKIP, "、".join(missing), "文件里没有这些小节，没查", "", ""))
    for c in skipped:
        if c["message"] != MISSING_MESSAGE:
            lines.append(table_row(SKIP, c["field"], "%s %s" % (c["id"], c["message"]), c["measured"], c["limit"]))
    return lines


def render_report(result):
    return "\n".join([summary_line(result), ""] + table_lines(result) + ["", FOOTER])


def write_report(text, result):
    """Return `text` with the body of the 机器检查结果 section replaced (or the section appended).

    Nothing outside that section is touched.
    """
    eol = "\r\n" if "\r\n" in text else "\n"
    block = [REPORT_MARK, "", summary_line(result), ""] + table_lines(result) + ["", FOOTER]
    section = Document(text).sections.get("report")
    if section is None:
        base = text if not text or text.endswith("\n") else text + eol
        return base + eol + "## " + SECTION_LABEL["report"] + eol + eol + eol.join(block) + eol
    cr = eol[:-1]
    lines = text.split("\n")
    body = [cr] + [line + cr for line in block]
    tail = lines[section.end:]
    return "\n".join(lines[:section.start + 1] + body + ([cr] + tail if tail else [""]))


# --- Command line -----------------------------------------------------------------------------------
class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, "用法错误：%s\n加 -h 看完整用法\n" % message)


def build_parser():
    parser = Parser(
        prog="check_listing.py",
        add_help=False,
        description="检查 Listing 交付包（markdown）的长度、字符、重复和表格是否齐全。"
                    "退出码：0 没有不通过项；1 有不通过项；2 用法错误、文件读不了或没有可检查的小节。",
    )
    parser.add_argument("files", nargs="+", metavar="FILE", help="交付包文件；写 - 表示从标准输入读")
    parser.add_argument("-h", "--help", action="help", help="显示这段说明")
    parser.add_argument("--full", action="store_true", help="完整检查：必需的小节缺了就算不通过")
    parser.add_argument("--write-report", action="store_true", help="把结果写进文件的“机器检查结果”小节")
    parser.add_argument("--json", action="store_true", help="只输出 JSON，每个文件一行")
    parser.add_argument("--brand", metavar="X", help="品牌名，覆盖文件里的检查参数")
    parser.add_argument("--banned", metavar='"a, b"', help="用户禁用词，逗号分隔，覆盖文件里的检查参数")
    parser.add_argument("--lang", metavar="en-US", help="文案语言，覆盖文件里的检查参数")
    parser.add_argument("--title-limit-exempt", action="store_true", help="标题长度不受限（如媒体类商品），超长只提示")
    parser.add_argument("--version", action="version", help="显示脚本版本和规则核对日期",
                        version="check_listing.py %s (rules_as_of %s)" % (SCRIPT_VERSION, RULES_AS_OF))
    return parser


def setup_streams():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def read_input(path):
    """Return (text, had_bom). Raises OSError or UnicodeDecodeError."""
    if path == "-":
        stream = getattr(sys.stdin, "buffer", None)
        data = stream.read() if stream is not None else sys.stdin.read().encode("utf-8")
    else:
        with open(path, "rb") as handle:
            data = handle.read()
    bom = b"\xef\xbb\xbf"
    if data.startswith(bom):
        return data[len(bom):].decode("utf-8"), True
    return data.decode("utf-8"), False


def main(argv=None):
    setup_streams()
    args = build_parser().parse_args(argv)
    if args.write_report and "-" in args.files:
        sys.stderr.write("用法错误：从标准输入读（-）时不能用 --write-report，请给文件路径\n")
        return 2
    overrides = {"brand": args.brand, "banned": args.banned, "lang": args.lang,
                 "title_limit_exempt": args.title_limit_exempt}
    exit_code = 0
    blocks = []

    def problem(path, message):
        sys.stderr.write("错误：%s：%s\n" % (path, message))
        if args.json:
            blocks.append(json.dumps({"script_version": SCRIPT_VERSION, "rules_as_of": RULES_AS_OF,
                                      "file": path, "error": message}, ensure_ascii=False))

    for path in args.files:
        try:
            text, had_bom = read_input(path)
        except OSError as error:
            problem(path, "读不了这个文件（%s）" % (error.strerror or error))
            exit_code = 2
            continue
        except UnicodeDecodeError:
            problem(path, "文件不是 UTF-8 编码，读不了")
            exit_code = 2
            continue
        try:
            result = check_text(text, path, args.full, overrides)
        except NothingToCheck:
            problem(path, "没找到能检查的小节标题（如 ### Title、## 必答问题表），请按模板的标题来写")
            exit_code = 2
            continue
        except Exception as error:  # a bug in this script must never look like a checked file
            sys.stderr.write(traceback.format_exc())
            problem(path, "脚本内部出错，没有完成检查（%s: %s）" % (type(error).__name__, error))
            exit_code = 2
            continue
        if args.write_report:
            updated = write_report(text, result)
            if updated != text:
                try:
                    with open(path, "wb") as handle:
                        handle.write((b"\xef\xbb\xbf" if had_bom else b"") + updated.encode("utf-8"))
                except OSError as error:
                    problem(path, "写不进这个文件（%s）" % (error.strerror or error))
                    exit_code = 2
                    continue
            sys.stderr.write("已写入：%s 的“%s”小节\n" % (path, SECTION_LABEL["report"]))
        if args.json:
            blocks.append(json.dumps(result, ensure_ascii=False))
        else:
            header = ["文件：%s" % path, ""] if len(args.files) > 1 else []
            blocks.append("\n".join(header) + render_report(result))
        if result["summary"]["fail"]:
            exit_code = max(exit_code, 1)
    if blocks:
        sys.stdout.write(("\n" if args.json else "\n\n").join(blocks) + "\n")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
