"""Parse MOF 一般会計予算 PDFs (fetched by jfl.fetch.mof_budget) into tidy rows.

The PDFs are text-based tables in 億円. Each table line is a label (MOF spaces out
the characters: 「社 会 保 障 関 係 費」) followed by figures:

    gaisan.pdf  p1 歳入, p3 主要経費別 歳出   前年度予算額 | 概算額 | 増減 | 伸率
    tax.pdf     税目別                        前年度当初 | 前年度補正後 | 概算額 | …
    frame.pdf   国債費 内訳                   前年度 | 本年度 | 増減
    social_security.pdf 「社会保障関係費（主要経費別）」 前年度 | 本年度 | 増減

We keep the budget-year column and the previous year's 当初 figure. Labels are
matched exactly against the lists below; an unknown or missing line stops the
build, so a change in MOF's categories is noticed rather than silently dropped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

from jfl.fetch.mic import compact, era_to_fy

NUM = r"△?\s?[0-9][0-9,]*"
LINE = re.compile(rf"^(?P<label>.+?)\s+(?P<nums>(?:\(?\s?{NUM}\s?\)?\s*)+)(?:\s+△?[0-9.]+)?$")


@dataclass
class Row:
    statement: str  # revenue | expenditure | tax | social_security | debt_service
    item_ja: str
    value_oku_yen: float
    prev_oku_yen: float | None  # previous year's initial budget (前年度当初)
    order: int
    file: str
    page: int


def _num(s: str) -> float:
    s = s.replace(",", "").replace(" ", "")
    return -float(s[1:]) if s.startswith("△") else float(s)


def _figures(line: str) -> tuple[str, list[float]] | None:
    """Split 「社 会 保 障 関 係 費 382,938 390,559 7,621 2.0」 into label and figures."""
    # 「うち」 lines wrap figures in parentheses: 「（ 14,221）（ 14,378）」.
    tokens = re.sub(r"[(（](?=\s?[0-9△])|(?<=[0-9])\s?[)）]", " ", line).split()
    nums: list[float] = []
    # Walk from the right while tokens are numbers (percent columns included).
    i = len(tokens)
    while i > 0:
        t = tokens[i - 1]
        if re.fullmatch(r"△?[0-9][0-9,]*(\.[0-9]+)?", t):
            nums.insert(0, _num(t) if "." not in t else float(t.replace("△", "-")))
            i -= 1
        elif t == "△" and nums:  # 「△ 750」 split into two tokens
            nums[0] = -nums[0]
            i -= 1
        elif t in ("－", "-", "―") and i < len(tokens):  # 「－」 = no amount last year
            nums.insert(0, float("nan"))
            i -= 1
        else:
            break
    if not nums or i == 0:
        return None
    label = compact(" ".join(tokens[:i]))
    return label, nums


def _lines(pdf_path: Path, page_filter) -> list[tuple[int, str]]:
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if page_filter(text):
                out.extend((pno, ln) for ln in text.splitlines())
    return out


def fiscal_year(pdf_path: Path) -> int:
    """From the document title (「令和８年度一般会計歳入歳出概算」), never the folder name."""
    with pdfplumber.open(pdf_path) as pdf:
        text = compact(pdf.pages[0].extract_text() or "")
    fy = era_to_fy(text)
    if fy is None:
        raise ValueError(f"{pdf_path}: no fiscal year in the title")
    return fy


# ------------------------------------------------------------------ line lists
# (item as printed, with spaces removed) in MOF's order.

REVENUE = ["租税及印紙収入", "その他収入", "公債金", "⑴公債金", "⑵特例公債金", "合計"]
EXPENDITURE = [
    "社会保障関係費",
    "文教及び科学振興費",
    "うち科学技術振興費",
    "国債費",
    "恩給関係費",
    "地方交付税交付金等",
    "防衛関係費",
    "公共事業関係費",
    "経済協力費",
    "中小企業対策費",
    "エネルギー対策費",
    "食料安定供給関係費",
    "その他の事項経費",
    "予備費",
    "合計",
]
SOCIAL_SECURITY = [
    "社会保障関係費（Ｃ）",
    "年金給付費",
    "医療給付費",
    "介護給付費",
    "少子化対策費",
    "生活扶助等社会福祉費",
    "保健衛生対策費",
    "雇用労災対策費",
]
DEBT_SERVICE = ["国債費", "うち債務償還費（交付国債分を除く）", "うち利払費"]


def _strip_number(label: str) -> str:
    """「１．租税及印紙収入」 → 「租税及印紙収入」."""
    return re.sub(r"^[0-9０-９]+[.．]", "", label)


def _pick(
    lines,
    wanted: list[str],
    statement: str,
    col: int,
    prev_col: int | None,
    file: str,
    rename=lambda s: s,
    stop: str | None = None,
) -> list[Row]:
    rows: dict[str, Row] = {}
    for pno, ln in lines:
        parsed = _figures(ln)
        if not parsed:
            continue
        label, nums = parsed
        label = rename(_strip_number(label))
        if label in wanted and label not in rows and len(nums) > col:
            prev = nums[prev_col] if prev_col is not None else None
            rows[label] = Row(
                statement,
                label,
                nums[col],
                None if prev != prev else prev,
                wanted.index(label),
                file,
                pno,
            )
            if stop and label == stop:
                break
    missing = [w for w in wanted if w not in rows]
    if missing:
        raise ValueError(f"{file}: {statement} lines not found: {missing}")
    return sorted(rows.values(), key=lambda r: r.order)


def parse(raw_dir: Path) -> tuple[int, list[Row]]:
    """All tables for one budget year folder (data/raw/mof-budget/fy<year>/)."""
    gaisan = raw_dir / "gaisan.pdf"
    fy = fiscal_year(gaisan)
    for name in ("tax.pdf", "frame.pdf"):
        if fiscal_year(raw_dir / name) != fy:
            raise ValueError(f"{raw_dir / name}: fiscal year differs from gaisan.pdf (FY{fy})")

    rows: list[Row] = []
    # p1: 歳入 lines come first, then 歳出 lines with the same 合計 label; stop at 合計.
    p1 = _lines(
        gaisan,
        lambda t: (
            "歳入歳出概算" in compact(t)
            and "所管別" not in compact(t)
            and "主要経費別" not in compact(t)
        ),
    )
    rows += _pick(p1, REVENUE, "revenue", 1, 0, gaisan.name, stop="合計")

    p3 = _lines(gaisan, lambda t: "主要経費別内訳" in compact(t))
    rows += _pick(p3, EXPENDITURE, "expenditure", 1, 0, gaisan.name)

    tax = _lines(raw_dir / "tax.pdf", lambda t: True)
    rows += _parse_tax(tax)

    frame = _lines(raw_dir / "frame.pdf", lambda t: True)
    rows += _pick(frame, DEBT_SERVICE, "debt_service", 1, 0, "frame.pdf", stop="うち利払費")

    ss = _lines(
        raw_dir / "social_security.pdf", lambda t: "社会保障関係費（主要経費別）" in compact(t)
    )
    rows += _pick(
        ss, SOCIAL_SECURITY, "social_security", 1, 0, "social_security.pdf", stop="雇用労災対策費"
    )
    return fy, rows


def _parse_tax(lines) -> list[Row]:
    """Every 税目 line up to 一般会計分計, in MOF's order. Columns: 当初 | 補正後 | 概算額 | …"""
    rows: list[Row] = []
    for pno, ln in lines:
        parsed = _figures(ln)
        if not parsed:
            continue
        label, nums = parsed
        if len(nums) < 3 or label in ("(A)(B)(C)(C－A)(C－B)",):
            continue
        # 「（所得税計）」 is a subtotal printed in parentheses; 「…（仮称）」 keeps its own.
        m = re.fullmatch(r"[(（]([^()（）]*)[)）]", label)
        label = m.group(1) if m else label
        prev = nums[0]
        rows.append(
            Row("tax", label, nums[2], None if prev != prev else prev, len(rows), "tax.pdf", pno)
        )
        if label == "一般会計分計":
            return rows
    raise ValueError("tax.pdf: 一般会計分計 not found")
