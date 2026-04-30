from __future__ import annotations

import re
import subprocess
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "implementation-and-testing-guide.md"
DOCX_TARGET = ROOT / "docs" / "implementation-and-testing-guide.docx"
PDF_TARGET = ROOT / "docs" / "implementation-and-testing-guide.pdf"


def build_docx() -> None:
    subprocess.run(
        [
            "pandoc",
            str(SOURCE),
            "--from",
            "gfm",
            "--standalone",
            "--toc",
            "--output",
            str(DOCX_TARGET),
        ],
        check=True,
        cwd=ROOT,
    )


def pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="GuideTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            textColor=colors.HexColor("#163a63"),
            alignment=TA_CENTER,
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuideSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#56697d"),
            alignment=TA_CENTER,
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuideH1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#163a63"),
            spaceBefore=14,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuideH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1b4d7a"),
            spaceBefore=12,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuideBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#142230"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuideCode",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=8.8,
            leading=11,
            leftIndent=14,
            rightIndent=14,
            borderPadding=10,
            backColor=colors.HexColor("#eef3f8"),
            textColor=colors.HexColor("#10233b"),
            spaceBefore=6,
            spaceAfter=8,
        )
    )
    return styles


def clean_inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def parse_table(lines: list[str], start: int):
    rows: list[list[str]] = []
    idx = start
    while idx < len(lines) and lines[idx].strip().startswith("|"):
        line = lines[idx].strip().strip("|")
        parts = [part.strip() for part in line.split("|")]
        rows.append(parts)
        idx += 1
    if len(rows) >= 2 and all(set(cell) <= {"-"} or cell == "" for cell in rows[1]):
        rows.pop(1)
    return rows, idx


def build_pdf() -> None:
    styles = pdf_styles()
    story = []
    lines = SOURCE.read_text(encoding="utf-8").splitlines()

    story.append(Paragraph("HybridAIAutomation", styles["GuideTitle"]))
    story.append(
        Paragraph(
            "Implementation and Step-by-Step Testing Guide",
            styles["GuideSubtitle"],
        )
    )

    idx = 0
    in_code_block = False
    code_lines: list[str] = []

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        if idx == 0 and stripped.startswith("# "):
            idx += 1
            continue

        if stripped.startswith("```"):
            if in_code_block:
                story.append(Preformatted("\n".join(code_lines), styles["GuideCode"]))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            idx += 1
            continue

        if in_code_block:
            code_lines.append(line)
            idx += 1
            continue

        if not stripped:
            story.append(Spacer(1, 0.08 * inch))
            idx += 1
            continue

        if stripped.startswith("# "):
            story.append(Paragraph(clean_inline(stripped[2:]), styles["GuideH1"]))
            idx += 1
            continue

        if stripped.startswith("## "):
            if stripped.startswith("## 7.") or stripped.startswith("## 8.") or stripped.startswith("## 9."):
                story.append(PageBreak())
            story.append(Paragraph(clean_inline(stripped[3:]), styles["GuideH1"]))
            idx += 1
            continue

        if stripped.startswith("### "):
            story.append(Paragraph(clean_inline(stripped[4:]), styles["GuideH2"]))
            idx += 1
            continue

        if stripped.startswith("|"):
            rows, idx = parse_table(lines, idx)
            table_data = [
                [Paragraph(clean_inline(cell), styles["GuideBody"]) for cell in row]
                for row in rows
            ]
            table = Table(table_data, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce7f2")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#163a63")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#b7c7d8")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 0.12 * inch))
            continue

        if stripped.startswith("- "):
            items = []
            while idx < len(lines) and lines[idx].strip().startswith("- "):
                item_text = lines[idx].strip()[2:]
                items.append(
                    ListItem(Paragraph(clean_inline(item_text), styles["GuideBody"]))
                )
                idx += 1
            story.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    start="circle",
                    leftIndent=18,
                )
            )
            story.append(Spacer(1, 0.06 * inch))
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if numbered:
            items = []
            while idx < len(lines):
                match = re.match(r"^(\d+)\.\s+(.*)", lines[idx].strip())
                if not match:
                    break
                items.append(
                    ListItem(Paragraph(clean_inline(match.group(2)), styles["GuideBody"]))
                )
                idx += 1
            story.append(
                ListFlowable(
                    items,
                    bulletType="1",
                    leftIndent=18,
                )
            )
            story.append(Spacer(1, 0.06 * inch))
            continue

        story.append(Paragraph(clean_inline(stripped), styles["GuideBody"]))
        idx += 1

    doc = SimpleDocTemplate(
        str(PDF_TARGET),
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="HybridAIAutomation Implementation and Testing Guide",
        author="OpenAI Codex",
    )
    doc.build(story)


def main() -> None:
    build_docx()
    build_pdf()


if __name__ == "__main__":
    main()
