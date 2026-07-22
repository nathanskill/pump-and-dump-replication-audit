#!/usr/bin/env python3
"""Render the manuscript markdown draft to a clean academic-style PDF.

Supports the markdown subset used by manuscript_draft_v0.1.md:
#/##/### headings, paragraphs, pipe tables, **bold**, *italic*, `code`.
Local tooling only; not part of the research pipeline.
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

BASE = Path(__file__).resolve().parent
SRC = BASE / "manuscript_draft_v0.1.md"
OUT = BASE / "manuscript_draft_v0.1.pdf"

S = {
    "title": ParagraphStyle("title", fontName="Times-Bold", fontSize=15.5,
                            leading=19.5, spaceAfter=5),
    "author": ParagraphStyle("author", fontName="Times-Roman", fontSize=10.5,
                             leading=13.5, spaceAfter=2),
    "note": ParagraphStyle("note", fontName="Times-Italic", fontSize=8.8,
                           leading=11.5, textColor=colors.HexColor("#555555"),
                           spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="Times-Bold", fontSize=12,
                         leading=14.5, spaceBefore=10, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="Times-Bold", fontSize=10.5,
                         leading=13, spaceBefore=7, spaceAfter=3),
    "body": ParagraphStyle("body", fontName="Times-Roman", fontSize=9.6,
                           leading=12.6, alignment=TA_JUSTIFY, spaceAfter=4.5),
    "slot": ParagraphStyle("slot", fontName="Times-Italic", fontSize=9.6,
                           leading=12.6, textColor=colors.HexColor("#8a4b00"),
                           spaceAfter=4.5),
    "li": ParagraphStyle("li", fontName="Times-Roman", fontSize=9.6,
                         leading=12.6, leftIndent=12, bulletIndent=3,
                         spaceAfter=3),
    "cell": ParagraphStyle("cell", fontName="Times-Roman", fontSize=8.6,
                           leading=10.8),
    "cellh": ParagraphStyle("cellh", fontName="Times-Bold", fontSize=8.6,
                            leading=10.8),
}


def inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8.4">\1</font>', text)
    return text


def flush_table(rows: list[list[str]], story: list) -> None:
    if not rows:
        return
    data = []
    for i, row in enumerate(rows):
        style = S["cellh"] if i == 0 else S["cell"]
        data.append([Paragraph(inline(cell), style) for cell in row])
    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(Spacer(1, 2))
    story.append(table)
    story.append(Spacer(1, 4))


def main() -> None:
    lines = SRC.read_text().splitlines()
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="Replication Attempt and Evaluation-Sensitivity Audit — draft v0.1",
        author="Zhennan (Nathan) Yu",
    )
    story: list = []
    table_rows: list[list[str]] = []
    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if set("".join(cells)) <= {"-", ":", " ", ""}:
                continue
            table_rows.append(cells)
            continue
        flush_table(table_rows, story)
        table_rows = []
        if not stripped:
            continue
        if stripped.startswith("### "):
            story.append(Paragraph(inline(stripped[4:]), S["h3"]))
        elif stripped.startswith("## "):
            story.append(Paragraph(inline(stripped[3:]), S["h2"]))
        elif stripped.startswith("# "):
            story.append(Paragraph(inline(stripped[2:]), S["title"]))
        elif re.match(r"^\d+\.\s", stripped) and "References" not in "".join(
            x.getPlainText() for x in story[-1:] if hasattr(x, "getPlainText")
        ):
            story.append(Paragraph(inline(stripped), S["li"]))
        elif stripped.startswith("- "):
            story.append(Paragraph(inline(stripped[2:]), S["li"], bulletText="–"))
        elif stripped.startswith("`[") and stripped.endswith("]`"):
            story.append(Paragraph(inline(stripped.strip("`")), S["slot"]))
        elif stripped.startswith("**Zhennan"):
            story.append(Paragraph(inline(stripped), S["author"]))
        elif stripped.startswith("*DRAFT"):
            story.append(Paragraph(inline(stripped.strip("*")), S["note"]))
        else:
            story.append(Paragraph(inline(stripped), S["body"]))
    flush_table(table_rows, story)
    doc.build(story)
    print(f"PDF written: {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
