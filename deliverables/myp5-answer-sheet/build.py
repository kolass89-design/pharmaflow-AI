# -*- coding: utf-8 -*-
"""
Build a print-quality answer sheet / mark scheme PDF for the
MYP 5 Mathematics eAssessment-style question bank.

    python3 build.py

Output: MYP5-eAssessment-Answer-Sheet.pdf (same folder)
"""

import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle, Flowable)

from content_bcd import SECTIONS_BCD
from content_rest import SECTIONS_REST, APPENDICES
from marks_from_paper import PART_MARKS

HERE = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------- fonts
FONT_DIR = os.path.join(HERE, "fonts")
FONTS = {
    "Body":       "OpenSans-Regular.ttf",
    "Body-It":    "OpenSans-Italic.ttf",
    "Body-Semi":  "OpenSans-SemiBold.ttf",
    "Body-Bold":  "OpenSans-Bold.ttf",
    "Body-Light": "OpenSans-Light.ttf",
    "Display":    "SourceSerif4-Regular.ttf",
    "Display-Semi": "SourceSerif4-Semibold.ttf",
    "Display-It": "SourceSerif4-It.ttf",
}
for name, fname in FONTS.items():
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, fname)))
# symbol fallback: a few mathematical glyphs are absent from Open Sans / Source Serif
pdfmetrics.registerFont(TTFont("Sym", os.path.join(FONT_DIR, "DejaVuSans.ttf")))
pdfmetrics.registerFontFamily("Sym", normal="Sym", bold="Sym", italic="Sym", boldItalic="Sym")
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                              italic="Body-It", boldItalic="Body-Bold")

# --------------------------------------------------------------------------- palette
NAVY      = HexColor("#0E2A47")
NAVY_DEEP = HexColor("#0A1F36")
INK       = HexColor("#22303C")
MUTED     = HexColor("#5F7182")
FAINT     = HexColor("#8A9AA8")
GOLD      = HexColor("#B98A2E")
GOLD_LITE = HexColor("#D9B764")
TEAL      = HexColor("#0F7B6C")
RULE      = HexColor("#DEE5EC")
PAPER     = HexColor("#F6F8FB")
CREAM     = HexColor("#FBF6E9")
C_B       = HexColor("#3F6FA8")
C_C       = HexColor("#1C7A55")
C_D       = HexColor("#C07A12")
CRIT_COL  = {"B": C_B, "C": C_C, "D": C_D}
CRIT_TINT = {"B": HexColor("#EDF2F8"), "C": HexColor("#EAF4EF"), "D": HexColor("#FBF3E4")}

PAGE_W, PAGE_H = A4
LM = RM = 48
TM, BM = 66, 58
CW = PAGE_W - LM - RM

# --------------------------------------------------------------------------- styles
def S(name, **kw):
    base = dict(fontName="Body", fontSize=9.2, leading=12.7, textColor=INK,
                spaceBefore=0, spaceAfter=0, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, **base)

st_sol      = S("sol", spaceAfter=1.6)
st_sol_last = S("solLast", spaceAfter=0)
st_part     = S("part", fontName="Body-Bold", fontSize=9.4, textColor=NAVY)
st_ans      = S("ans", fontName="Body-Semi", fontSize=9.1, leading=12.2, textColor=NAVY)
st_mb       = S("mb", fontName="Body-It", fontSize=7.7, leading=10.2, textColor=MUTED)
st_note     = S("note", fontName="Body-It", fontSize=8.5, leading=11.8, textColor=HexColor("#44576A"))
st_tasktitle= S("tasktitle", fontName="Display-Semi", fontSize=15.2, leading=18, textColor=NAVY)
st_meta     = S("meta", fontName="Body", fontSize=8.0, leading=10, textColor=MUTED)
st_chip     = S("chip", fontName="Body-Bold", fontSize=6.5, leading=7.6,
                textColor=colors.white, alignment=TA_CENTER)
st_marks    = S("marks", fontName="Body-Bold", fontSize=13, leading=14, textColor=NAVY, alignment=TA_RIGHT)
st_markslbl = S("markslbl", fontName="Body-Semi", fontSize=5.6, leading=7,
                textColor=FAINT, alignment=TA_RIGHT)
st_th       = S("th", fontName="Body-Bold", fontSize=8.0, leading=10.2, textColor=NAVY)
st_th_c     = S("thc", fontName="Body-Bold", fontSize=8.0, leading=10.2, textColor=NAVY, alignment=TA_CENTER)
st_td       = S("td", fontName="Body", fontSize=8.2, leading=10.6)
st_td_c     = S("tdc", fontName="Body", fontSize=8.2, leading=10.6, alignment=TA_CENTER)
st_colhdr   = S("colhdr", fontName="Body-Semi", fontSize=6.4, leading=8, textColor=FAINT)
st_colhdr_r = S("colhdrr", fontName="Body-Semi", fontSize=6.4, leading=8, textColor=FAINT, alignment=TA_RIGHT)

# section divider
st_kicker   = S("kicker", fontName="Body-Bold", fontSize=7.4, leading=9, textColor=GOLD_LITE)
st_seckick  = S("seckick", fontName="Body-Bold", fontSize=7.6, leading=9.5, textColor=GOLD)
st_sectitle = S("sectitle", fontName="Display-Semi", fontSize=27, leading=30, textColor=colors.white)
st_secintro = S("secintro", fontName="Body", fontSize=9.4, leading=13.6,
                textColor=HexColor("#CBD8E4"))
st_secnum   = S("secnum", fontName="Display", fontSize=64, leading=64,
                textColor=HexColor("#1E4166"), alignment=TA_RIGHT)

# front matter / appendix
st_h2       = S("h2", fontName="Display-Semi", fontSize=17, leading=21, textColor=NAVY, spaceAfter=6)
st_body     = S("body", fontSize=9.4, leading=14.2, spaceAfter=6.4, alignment=TA_JUSTIFY)
st_body_c   = S("bodyc", fontSize=9.4, leading=14.2, spaceAfter=6.4)
st_bullet   = S("bullet", fontSize=9.3, leading=13.6, spaceAfter=5.2,
                leftIndent=11, bulletIndent=1, alignment=TA_JUSTIFY)
st_lead     = S("lead", fontName="Body-Light", fontSize=11.6, leading=16.4, textColor=MUTED, spaceAfter=12)
st_cardh    = S("cardh", fontName="Body-Bold", fontSize=8.0, leading=10, textColor=GOLD)
st_cardline = S("cardline", fontName="Body", fontSize=8.2, leading=12.0, textColor=INK)
st_tocnum   = S("tocnum", fontName="Display-Semi", fontSize=11, leading=14, textColor=GOLD)
st_toctitle = S("toctitle", fontName="Display-Semi", fontSize=10.6, leading=14, textColor=NAVY)
st_tocsub   = S("tocsub", fontName="Body", fontSize=7.8, leading=10, textColor=MUTED)
st_tocpage  = S("tocpage", fontName="Body-Semi", fontSize=9, leading=12, textColor=NAVY, alignment=TA_RIGHT)


# --------------------------------------------------------------------------- helpers
def esc(text):
    return (text.replace("&", "&amp;").replace("&amp;lt;", "&lt;").replace("&amp;gt;", "&gt;"))


SYMBOLS = "→∠≫⊥■△✓✗∡"


def m(text):
    """Escape bare comparison operators, keep markup, substitute missing glyphs."""
    text = (text.replace("⁻¹", "<super>−1</super>")
                .replace("⁻ˣ", "<super>−x</super>")
                .replace("ˣ", "<super>x</super>")
                .replace("ᵗ", "<super>t</super>")
                .replace("⅓", "(1/3)"))
    text = re.sub(r"(?<=[\w\)\]])\s<\s(?=[\w\(−\-])", " &lt; ", text)
    text = re.sub(r"(?<=[\w\)\]])\s>\s(?=[\w\(−\-])", " &gt; ", text)
    text = text.replace("≫", "&gt;&gt;")
    # wrap remaining symbols that Open Sans lacks in the fallback font
    for ch in SYMBOLS:
        if ch in text:
            text = text.replace(ch, '<font name="Sym">%s</font>' % ch)
    return text


def P(text, style):
    return Paragraph(m(text), style)


def chip_row(criteria):
    cells = []
    for c in criteria:
        lab = "CRITERION " + c
        cells.append(Paragraph(lab, st_chip))
    widths = []
    for c in criteria:
        widths.append(pdfmetrics.stringWidth("CRITERION " + c, "Body-Bold", 6.5) + 13)
    t = Table([cells], colWidths=widths, rowHeights=[13])
    style = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LEFTPADDING", (0, 0), (-1, -1), 0),
             ("RIGHTPADDING", (0, 0), (-1, -1), 0),
             ("TOPPADDING", (0, 0), (-1, -1), 0),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]
    for i, c in enumerate(criteria):
        style += [("BACKGROUND", (i, 0), (i, 0), CRIT_COL[c]),
                  ("LEFTPADDING", (i, 0), (i, 0), 4),
                  ("RIGHTPADDING", (i, 0), (i, 0), 4)]
        if i:
            style += [("LEFTPADDING", (i, 0), (i, 0), 4)]
    t.setStyle(TableStyle(style))
    t.hAlign = "LEFT"
    return t


def answer_box(text, width=CW - 88):
    bar = Table([[""]], colWidths=[2.6], rowHeights=[None])
    bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TEAL),
                             ("TOPPADDING", (0, 0), (-1, -1), 0),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                             ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    body = Paragraph("<font color='#0F7B6C'><b>Answer</b></font>&nbsp;&nbsp;&nbsp;" + m(text), st_ans)
    t = Table([[bar, body]], colWidths=[2.6, width - 2.6])
    t.setStyle(TableStyle([
        ("BACKGROUND", (1, 0), (1, 0), HexColor("#EFF6F3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 0), (0, 0), 0), ("BOTTOMPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 6), ("RIGHTPADDING", (1, 0), (1, 0), 5),
        ("TOPPADDING", (1, 0), (1, 0), 3.2), ("BOTTOMPADDING", (1, 0), (1, 0), 3.6),
    ]))
    t.hAlign = "LEFT"
    return t


def note_box(text, width=CW):
    label = Paragraph("<font color='#B98A2E'><b>EXAMINER NOTE</b></font>&nbsp;&nbsp;"
                      "<font color='#44576A'>" + m(text) + "</font>", st_note)
    t = Table([["", label]], colWidths=[2.6, width - 2.6])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), GOLD),
        ("BACKGROUND", (1, 0), (1, 0), HexColor("#FDFAF2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 0), (0, 0), 0), ("BOTTOMPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 7), ("RIGHTPADDING", (1, 0), (1, 0), 7),
        ("TOPPADDING", (1, 0), (1, 0), 4.5), ("BOTTOMPADDING", (1, 0), (1, 0), 5),
    ]))
    return t


def data_table(spec, width):
    """Nested table used inside a solution cell / appendix."""
    total = sum(float(w.strip("%")) for w in spec["widths"])
    widths = [width * float(w.strip("%")) / total for w in spec["widths"]]
    ncols = len(widths)
    heavy = [False] * ncols
    for col in range(1, ncols):
        vals = [str(r[col]) for r in spec["rows"]]
        heavy[col] = any(len(v) > 22 for v in vals)
    head = [Paragraph(esc(h), st_th_c if (i and not heavy[i]) else st_th)
            for i, h in enumerate(spec["head"])]
    rows = []
    for r in spec["rows"]:
        rows.append([Paragraph(esc(c), st_td if (i == 0 or heavy[i]) else st_td_c)
                     for i, c in enumerate(r)])
    data = [head] + rows
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#EFF3F8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, HexColor("#D3DEE9")),
        ("LINEBELOW", (0, 1), (-1, -2), 0.4, RULE),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#D3DEE9")),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#F9FBFD")))
    t.setStyle(TableStyle(style))
    return t


# --------------------------------------------------------------------------- flowables
class SectionDivider(Flowable):
    """Full-width banded section opener."""
    def __init__(self, num, kicker, title, intro, width=CW):
        Flowable.__init__(self)
        self.num, self.kicker, self.title, self.intro, self.width = num, kicker, title, intro, width
        self.para = Paragraph(m(intro), st_secintro)
        self.height = 140
        self.tsize = 24.0

    def wrap(self, aw, ah):
        _, th = self.para.wrap(self.width - 44, 500)
        self.intro_h = th
        # shrink the title until the numeral fits comfortably on the same line
        right = 24 + (62 if len(str(self.num)) > 1 else 40)
        avail = self.width - 22 - right - 10
        while self.tsize > 15 and pdfmetrics.stringWidth(self.title, "Display-Semi", self.tsize) > avail:
            self.tsize -= 0.5
        self.height = 22 + 9 + 9 + 26 + 8 + 16 + th + 22
        return self.width, self.height

    def draw(self):
        c = self.canv
        h = self.height
        c.saveState()
        c.setFillColor(NAVY)
        c.rect(0, 0, self.width, h, stroke=0, fill=1)
        c.setFillColor(GOLD)
        c.rect(0, h - 2.6, self.width, 2.6, stroke=0, fill=1)

        # kicker
        c.setFillColor(GOLD_LITE)
        c.setFont("Body-Bold", 7.0)
        c.drawString(22, h - 30, self.kicker.upper().replace("&", "AND"))

        # title + oversized numeral on the same baseline
        base = h - 30 - 9 - 26 + 6
        c.setFillColor(colors.white)
        c.setFont("Display-Semi", self.tsize)
        c.drawString(22, base, self.title)
        c.setFillColor(HexColor("#22486E"))
        c.setFont("Display", 46)
        c.drawRightString(self.width - 20, base - 2, str(self.num))

        # gold rule
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.1)
        c.line(22, base - 12, 74, base - 12)

        # intro
        self.para.drawOn(c, 22, 22)
        c.restoreState()


class Recorder(Flowable):
    """Zero-size flowable that records the page and adds a PDF bookmark."""
    def __init__(self, key, label=None, level=0):
        Flowable.__init__(self)
        self.key, self.label, self.level = key, label, level

    def wrap(self, aw, ah):
        return 0, 0

    def draw(self):
        SECTION_PAGES[self.key] = self.canv.getPageNumber()
        if self.label:
            self.canv.bookmarkPage(self.key)
            self.canv.addOutlineEntry(self.label, self.key, level=self.level, closed=False)


class Rule(Flowable):
    def __init__(self, width, thickness=0.7, color=RULE, space=0):
        Flowable.__init__(self)
        self.width, self.thickness, self.color, self.space = width, thickness, color, space
        self.height = space

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.height / 2, self.width, self.height / 2)


# --------------------------------------------------------------------------- task table
PART_W, MARK_W = 36, 52
SOL_W = CW - PART_W - MARK_W


def task_block(task):
    crit = task["criteria"]
    accent = CRIT_COL[crit[0]]
    tint = CRIT_TINT[crit[0]]

    head_left = [chip_row(crit), Spacer(1, 6),
                 Paragraph("%s&nbsp;&nbsp;%s" % (task["id"], esc(task["title"])), st_tasktitle),
                 Spacer(1, 3),
                 Paragraph("Difficulty: %s&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;%s"
                           % (esc(task["diff"]), esc(task["stem"])), st_meta)]
    marks_cell = [Paragraph(str(task["marks"]), st_marks),
                  Paragraph("MARKS", st_markslbl)]
    head_right = Table([[marks_cell]], colWidths=[MARK_W - 12])
    head_right.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                                    ("ALIGN", (0, 0), (-1, -1), "RIGHT")]))
    head_inner = Table([[head_left, head_right]],
                       colWidths=[CW - 18 - MARK_W, MARK_W - 6])
    head_inner.setStyle(TableStyle([("VALIGN", (0, 0), (0, 0), "TOP"),
                                    ("VALIGN", (1, 0), (1, 0), "TOP"),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))

    data = [[head_inner, "", ""],
            [Paragraph("PART", st_colhdr), Paragraph("WORKED SOLUTION AND MARKING GUIDE", st_colhdr),
             Paragraph("MARKS", st_colhdr_r)]]

    for part in task["parts"]:
        cell = []
        for line in part.get("work", []):
            cell.append(P(line, st_sol))
        if part.get("tbl"):
            cell.append(Spacer(1, 4))
            cell.append(data_table(part["tbl"], SOL_W - 26))
            cell.append(Spacer(1, 4))
        if part.get("ans"):
            cell.append(Spacer(1, 2))
            cell.append(answer_box(part["ans"], SOL_W - 16))
        if part.get("mb"):
            cell.append(Spacer(1, 3))
            cell.append(Paragraph("<font color='#B98A2E'><b>Marking</b></font>&nbsp;&nbsp;" + m(part["mb"]), st_mb))
        data.append([Paragraph(part["p"], st_part), cell,
                     Paragraph(str(part["m"]), st_marks)])

    t = Table(data, colWidths=[PART_W, SOL_W, MARK_W], repeatRows=2,
              splitByRow=1, splitInRow=1)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), tint),
        ("LINEABOVE", (0, 0), (-1, 0), 2.4, accent),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, HexColor("#D7E0E9")),
        ("TOPPADDING", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 9),
        ("LEFTPADDING", (0, 0), (-1, 0), 11),
        ("RIGHTPADDING", (0, 0), (-1, 0), 8),
        # column header row
        ("BACKGROUND", (0, 1), (-1, 1), HexColor("#FBFCFE")),
        ("TOPPADDING", (0, 1), (-1, 1), 9),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
        ("LEFTPADDING", (0, 1), (-1, 1), 6),
        ("RIGHTPADDING", (0, 1), (-1, 1), 6),
        ("LINEBELOW", (0, 1), (-1, 1), 0.4, RULE),
        # body
        ("TOPPADDING", (0, 2), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 2), (-1, -1), 7),
        ("LEFTPADDING", (0, 2), (0, -1), 6),
        ("RIGHTPADDING", (0, 2), (0, -1), 2),
        ("LEFTPADDING", (1, 2), (1, -1), 6),
        ("RIGHTPADDING", (1, 2), (1, -1), 10),
        ("LEFTPADDING", (2, 2), (2, -1), 0),
        ("RIGHTPADDING", (2, 2), (2, -1), 8),
        ("LINEBELOW", (0, 2), (-1, -2), 0.4, RULE),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, HexColor("#C9D4DF")),
    ]
    t.setStyle(TableStyle(style))
    t.hAlign = "LEFT"
    return t


# --------------------------------------------------------------------------- cover
def draw_cover(canv, doc):
    c = canv
    W, H = PAGE_W, PAGE_H
    c.saveState()
    c.setFillColor(NAVY_DEEP)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # faint geometric motif (dots + triangles), bottom-right
    c.saveState()
    c.setFillColor(HexColor("#173A5C"))
    cx, cy = W - 96, 268
    for ring in range(1, 4):
        n = 6 * ring
        r = ring * 9
        for i in range(n):
            import math
            a = 2 * math.pi * i / n + ring * 0.26
            c.circle(cx + r * math.cos(a), cy + r * math.sin(a), 1.35, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#173A5C"))
    c.setLineWidth(1.1)
    for i in range(3):
        x0 = W - 156 + i * 24
        y0 = 96
        c.line(x0, y0, x0 + 12, y0 + 21)
        c.line(x0 + 12, y0 + 21, x0 + 24, y0)
        c.line(x0, y0, x0 + 24, y0)
    c.restoreState()

    # frame
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.9)
    c.rect(26, 26, W - 52, H - 52, stroke=1, fill=0)
    c.setStrokeColor(HexColor("#2A4A6B"))
    c.setLineWidth(0.4)
    c.rect(31, 31, W - 62, H - 62, stroke=1, fill=0)

    c.setFillColor(GOLD_LITE)
    c.setFont("Body-Bold", 8)
    c.drawString(58, H - 92, "M Y P   5   ·   M A T H E M A T I C S")

    c.setFillColor(colors.white)
    c.setFont("Display", 43)
    c.drawString(56, H - 168, "Worked Answers")
    c.setFillColor(GOLD_LITE)
    c.setFont("Display-It", 33)
    c.drawString(58, H - 212, "and Mark Scheme")

    c.setStrokeColor(GOLD)
    c.setLineWidth(1.4)
    c.line(58, H - 240, 150, H - 240)

    c.setFillColor(HexColor("#C9D7E4"))
    c.setFont("Body", 11.6)
    c.drawString(58, H - 272, "MYP 5 eAssessment-Style Question Bank")
    c.setFillColor(HexColor("#8FA5BA"))
    c.setFont("Body", 9.6)
    c.drawString(58, H - 292, "Criteria B, C and D  ·  Complete solutions with mark allocation")

    # criteria cards
    y = H - 400
    rows = [("B", "Investigating Patterns", "generalise, test, justify"),
            ("C", "Communicating", "represent, reason, explain"),
            ("D", "Applying Mathematics", "model, calculate, evaluate")]
    for letter, head, sub in rows:
        c.setFillColor(CRIT_COL[letter])
        c.rect(58, y, 3, 34, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Display-Semi", 12.6)
        c.drawString(72, y + 18, head)
        c.setFillColor(HexColor("#8FA5BA"))
        c.setFont("Body", 8.4)
        c.drawString(72, y + 6, sub)
        c.setFillColor(HexColor("#3A5A79"))
        c.setFont("Display-Semi", 26)
        c.drawRightString(W - 68, y + 4, letter)
        y -= 62

    # stats band
    c.setStrokeColor(HexColor("#2A4A6B"))
    c.setLineWidth(0.7)
    c.line(58, 232, W - 58, 232)
    stats = [("43", "tasks covered"), ("537", "marks allocated"), ("100%", "worked solutions")]
    x = 58
    for big, small in stats:
        c.setFillColor(colors.white)
        c.setFont("Display-Semi", 20)
        c.drawString(x, 196, big)
        c.setFillColor(HexColor("#8FA5BA"))
        c.setFont("Body", 7.6)
        c.drawString(x, 182, small)
        x += 150

    c.setFillColor(HexColor("#7C90A6"))
    c.setFont("Body", 7.8)
    c.drawString(58, 120, "Teacher and student edition  ·  Answers aligned to the printed question bank")
    c.setFillColor(HexColor("#57708A"))
    c.setFont("Body-Semi", 7.8)
    c.drawString(58, 104, "Prepared October 2026  ·  56-page question bank  ·  Sections 2 to 13")
    c.restoreState()


def draw_body(canv, doc):
    c = canv
    c.saveState()
    label = section_for_page(c.getPageNumber())
    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.line(LM, PAGE_H - 44, PAGE_W - RM, PAGE_H - 44)
    if label:
        c.setFillColor(NAVY)
        c.setFont("Body-Semi", 7.2)
        c.drawString(LM, PAGE_H - 38, label.upper())
    c.setFillColor(FAINT)
    c.setFont("Body-Semi", 7.2)
    c.drawRightString(PAGE_W - RM, PAGE_H - 38, "MYP 5 MATHEMATICS  ·  ANSWER SHEET & MARK SCHEME")
    # footer
    c.setStrokeColor(RULE)
    c.line(LM, 42, PAGE_W - RM, 42)
    c.setFillColor(FAINT)
    c.setFont("Body", 7.2)
    c.drawString(LM, 30, "Worked Answer Sheet & Mark Scheme  ·  Criteria B, C and D  ·  43 tasks  ·  537 marks")
    c.setFillColor(GOLD)
    c.rect(PAGE_W - RM - 34, 30.5, 26, 1.1, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Body-Semi", 8.2)
    c.drawRightString(PAGE_W - RM, 29, "%02d" % c.getPageNumber())
    c.restoreState()


SECTION_PAGES = {}


def section_for_page(page):
    best = None
    for (key, p, label) in SECTION_INDEX:
        if p and p <= page:
            if best is None or p >= best[1]:
                best = (key, p, label)
    return best[2] if best else None


SECTION_INDEX = []  # (key, page, label)


# --------------------------------------------------------------------------- front matter
def front_matter():
    flow = []

    # ---------- page 2 : how to use
    flow += [NextPageTemplate("body"), PageBreak()]
    flow += [Paragraph("How to use this answer sheet", st_h2)]
    flow += [Paragraph(
        "This document is the companion to the 56-page <b>MYP 5 Mathematics eAssessment-style question bank</b>. "
        "It gives a complete worked solution, a boxed final answer and a short marking note for every part of "
        "every task — 43 tasks and 537 marks in total.", st_lead)]

    flow += [Paragraph("What each block contains", st_body_c)]
    legend = Table([
        [Paragraph("<b>Part</b>", st_td), Paragraph("The part label exactly as it appears in the question bank.", st_td)],
        [Paragraph("<b>Worked solution</b>", st_td), Paragraph("A model method with the reasoning written out — the standard a Criterion C answer should reach.", st_td)],
        [Paragraph("<b>Answer</b>", st_td), Paragraph("The final result, boxed, with units where they matter.", st_td)],
        [Paragraph("<b>Marking</b>", st_td), Paragraph("How the marks in the right-hand column are earned, and where candidates usually lose them.", st_td)],
        [Paragraph("<b>Examiner note</b>", st_td), Paragraph("The insight that separates a secure answer from a routine one — the difference between level 6 and level 8.", st_td)],
    ], colWidths=[92, CW - 92], repeatRows=0)
    legend.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), HexColor("#F4F7FA")),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#DCE4EC")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ]))
    flow += [legend, Spacer(1, 16)]

    flow += [Paragraph("Three ways to use it", st_body_c)]
    ways = [("Student, after attempting", "Cover the answer boxes with a sheet of paper, compare methods, then read the marking note to see where the marks sat."),
            ("Teacher, when marking", "The marking note gives the split for each part; the total in the header matches the question bank exactly."),
            ("Revision", "Work backwards from the examiner notes: they list the mistakes that most often cost marks in each topic.")]
    for head, body in ways:
        flow.append(Paragraph("<font color='#0E2A47'><b>%s.</b></font> %s" % (head, body), st_bullet))

    flow += [Spacer(1, 10)]
    flow += [Paragraph("Assessment blueprint", st_body_c)]
    rows = [["Sec.", "Focus", "Criterion", "Tasks", "Marks", "Share"]]
    total = 0
    for sec in ALL_SECTIONS:
        mk = sum(t["marks"] for t in sec["tasks"])
        total += mk
        ids = ", ".join(t["id"] for t in sec["tasks"])
        rows.append([str(sec["num"]), sec["title"], sec["kicker"].title(), ids, str(mk), ""])
    share_data = []
    for r in rows[1:]:
        share_data.append(r)
    table_rows = [rows[0]]
    for r in share_data:
        pct = float(r[4]) / total * 100
        table_rows.append(r[:5] + ["%.1f%%" % pct])
    table_rows.append(["", "Total", "", "43 tasks", str(total), "100%"])
    bt = Table([[Paragraph(esc(c), st_td) for c in r] for r in table_rows],
               colWidths=[34, 178, 90, 100, 42, 55], repeatRows=1)
    bstyle = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("BACKGROUND", (0, 0), (-1, 0), NAVY),
              ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
              ("BOX", (0, 0), (-1, -1), 0.6, HexColor("#CBD6E0")),
              ("TOPPADDING", (0, 0), (-1, -1), 3.6),
              ("BOTTOMPADDING", (0, 0), (-1, -1), 3.8),
              ("ALIGN", (0, 0), (0, -1), "CENTER"),
              ("ALIGN", (4, 0), (5, -1), "CENTER"),
              ("LEFTPADDING", (1, 0), (3, -1), 6),
              ("BACKGROUND", (0, len(table_rows) - 1), (-1, len(table_rows) - 1), HexColor("#F1F5F9")),
              ("LINEABOVE", (0, len(table_rows) - 1), (-1, len(table_rows) - 1), 0.8, NAVY)]
    for i in range(1, len(table_rows)):
        if i % 2 == 0:
            bstyle.append(("BACKGROUND", (0, i), (-1, i), HexColor("#FAFBFD")))
    bt.setStyle(TableStyle(bstyle))
    data = bt._cellvalues
    data[0] = [Paragraph("<font color='white'>%s</font>" % esc(c), st_th) for c in rows[0]]
    bt._cellvalues = data
    flow += [bt]

    # ---------- page 3 : contents
    flow += [PageBreak()]
    flow += [Paragraph("Contents", st_h2)]
    flow += [Paragraph("Every section of the question bank, with its tasks and the page where its solutions begin.",
                       st_lead)]
    toc_rows = []
    for sec in ALL_SECTIONS:
        key = "S%s" % sec["num"]
        n = len(sec["tasks"])
        mk = sum(t["marks"] for t in sec["tasks"])
        label = "Section %s" % sec["num"]
        sub = "%s  ·  %d task%s  ·  %d marks" % (sec["kicker"].title(), n, "" if n == 1 else "s", mk)
        page = SECTION_PAGES.get(key, "")
        toc_rows.append([Paragraph(label, st_tocnum),
                         [Paragraph(esc(sec["title"]), st_toctitle), Paragraph(esc(sub), st_tocsub)],
                         Paragraph(str(page) if page else "·", st_tocpage)])
    for app in APPENDICES:
        key = "A%s" % app["num"]
        page = SECTION_PAGES.get(key, "")
        toc_rows.append([Paragraph("App. %s" % app["num"], st_tocnum),
                         [Paragraph(esc(app["title"]), st_toctitle),
                          Paragraph(esc(app["kicker"].title()), st_tocsub)],
                         Paragraph(str(page) if page else "·", st_tocpage)])
    toc = Table(toc_rows, colWidths=[62, CW - 62 - 34, 34])
    tstyle = [("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("TOPPADDING", (0, 0), (-1, -1), 6.2),
              ("BOTTOMPADDING", (0, 0), (-1, -1), 6.2),
              ("LEFTPADDING", (0, 0), (-1, -1), 0),
              ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE)]
    toc.setStyle(TableStyle(tstyle))
    flow += [toc, Spacer(1, 14)]
    flow += [Paragraph(
        "<font color='#5F7182'>Page numbers refer to this answer sheet, not to the question bank. "
        "The task codes (B1, C4, D7, M2 …) are identical in both documents.</font>", st_mb)]
    return flow


# --------------------------------------------------------------------------- appendix renderers
def coverage_block():
    """Table showing which tasks practise each criterion as the main or supporting skill."""
    rows = []
    for letter, name in (("B", "Investigating patterns"), ("C", "Communicating"), ("D", "Applying mathematics")):
        main, support, marks = [], [], 0
        for sec in ALL_SECTIONS:
            for t in sec["tasks"]:
                if t["criteria"][0] == letter:
                    main.append(t["id"])
                    marks += t["marks"]
                elif letter in t["criteria"][1:]:
                    support.append(t["id"])
        rows.append([Paragraph("%s — %s" % (letter, name), st_td),
                     Paragraph(esc(", ".join(main)), st_td),
                     Paragraph(esc(", ".join(support)), st_td),
                     Paragraph(str(marks), st_td_c)])
    data = [[Paragraph("Criterion", st_th), Paragraph("Main criterion", st_th),
             Paragraph("Supporting criterion", st_th), Paragraph("Marks", st_th_c)]] + rows
    t = Table(data, colWidths=[132, 150, 158, 42])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#EFF3F8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#D3DEE9")),
        ("ALIGN", (3, 0), (3, -1), "CENTER"),
    ]))
    return t


def answerkey_block():
    rows = []
    for sec in ALL_SECTIONS:
        rows.append(["#sec", "SECTION %s  ·  %s" % (sec["num"], sec["title"].upper()), ""])
        for t in sec["tasks"]:
            ans = "  ".join("<b>%s</b> %s" % (p["p"], p["ans"]) for p in t["parts"] if p.get("ans"))
            rows.append([t["id"], "<font color='#0E2A47'><b>%s</b></font>&nbsp; %s" % (
                esc(t["title"]), ""), m(ans)])
    data = []
    for r in rows:
        if r[0] == "#sec":
            data.append([Paragraph("<font color='white'>%s</font>" % esc(r[1]), st_th), "", ""])
        else:
            data.append([Paragraph(r[0], st_part), "", Paragraph(r[2], st_td)])
    t = Table(data, colWidths=[34, CW - 34 - 34, 34], repeatRows=0)
    return t


def answerkey_block():
    rows = []
    for sec in ALL_SECTIONS:
        rows.append(("sec", "SECTION %s  ·  %s" % (sec["num"], sec["title"].upper())))
        for t in sec["tasks"]:
            ans = "&nbsp;&nbsp;&nbsp;".join("<b>%s</b>&nbsp;%s" % (p["p"], p["ans"])
                                            for p in t["parts"] if p.get("ans"))
            rows.append(("task", (t["id"], t["title"], ans)))
    data = []
    for kind, val in rows:
        if kind == "sec":
            data.append([Paragraph("<font color='white'>%s</font>" % esc(val), st_th), ""])
        else:
            tid, title, ans = val
            left = Paragraph("<font color='#0E2A47'><b>%s</b></font>&nbsp;&nbsp;%s" % (tid, esc(title)), st_td)
            data.append([left, Paragraph(ans, st_td)])
    t = Table(data, colWidths=[132, CW - 132], repeatRows=0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 4.0),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 4.4),
             ("LEFTPADDING", (0, 0), (-1, -1), 6),
             ("RIGHTPADDING", (0, 0), (-1, -1), 6),
             ("LINEBELOW", (0, 0), (-1, -2), 0.35, HexColor("#E4EAF0")),
             ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#D3DEE9"))]
    for i, (kind, val) in enumerate(rows):
        if kind == "sec":
            style += [("BACKGROUND", (0, i), (-1, i), NAVY),
                      ("SPAN", (0, i), (-1, i)),
                      ("TOPPADDING", (0, i), (-1, i), 6),
                      ("BOTTOMPADDING", (0, i), (-1, i), 6)]
        elif i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#FAFBFD")))
    t.setStyle(TableStyle(style))
    return t


def appendix_block(block):
    out = []
    if block["kind"] == "answerkey":
        out.append(answerkey_block())
        return out
    if block["kind"] == "coverage":
        out.append(coverage_block())
        out.append(Spacer(1, 8))
        return out
    if block["kind"] == "paras":
        for t in block["items"]:
            out.append(Paragraph(m(t), st_body))
    elif block["kind"] == "table":
        spec = {"widths": block["widths"], "head": block["head"], "rows": block["rows"]}
        tbl = data_table(spec, CW)
        if len(block["rows"]) <= 6:
            out.append(KeepTogether([tbl]))
        else:
            out.append(tbl)
        out.append(Spacer(1, 8))
    elif block["kind"] == "numbered":
        rows = []
        for i, t in enumerate(block["items"], 1):
            rows.append([Paragraph("%02d" % i, st_tocnum), Paragraph(m(t), st_body)])
        tb = Table(rows, colWidths=[34, CW - 34])
        tb.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("TOPPADDING", (0, 0), (-1, -1), 2),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("LINEBELOW", (0, 0), (-1, -2), 0.35, HexColor("#E8EDF2"))]))
        out.append(tb)
    elif block["kind"] == "grid":
        cards = []
        for item in block["items"]:
            inner = [Paragraph(esc(item["h"].upper()), st_cardh), Spacer(1, 3)]
            for line in item["rows"]:
                inner.append(Paragraph("·&nbsp;&nbsp;" + esc(line), st_cardline))
            t = Table([[inner]], colWidths=[CW / 2 - 12])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F8FAFC")),
                ("LINEABOVE", (0, 0), (-1, 0), 1.6, GOLD),
                ("BOX", (0, 0), (-1, -1), 0.4, HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ]))
            cards.append(t)
        rows = []
        for i in range(0, len(cards), 2):
            pair = cards[i:i + 2]
            if len(pair) == 1:
                pair.append("")
            rows.append(pair)
        grid = Table(rows, colWidths=[CW / 2 - 4, CW / 2 - 4])
        grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                  ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                                  ("TOPPADDING", (0, 0), (-1, -1), 0),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        out.append(grid)
    return out


# --------------------------------------------------------------------------- document
class Doc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        BaseDocTemplate.__init__(self, filename, pagesize=A4,
                                 leftMargin=LM, rightMargin=RM,
                                 topMargin=TM, bottomMargin=BM,
                                 title="MYP 5 Mathematics — Worked Answer Sheet and Mark Scheme",
                                 author="MYP 5 Mathematics",
                                 subject="eAssessment-style question bank: Criteria B, C and D",
                                 **kw)
        frame = Frame(LM, BM, CW, PAGE_H - TM - BM, id="body",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        cover_frame = Frame(LM, BM, CW, PAGE_H - TM - BM, id="cover")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover_frame], onPage=draw_cover),
            PageTemplate(id="body", frames=[frame], onPage=draw_body),
        ])

    def afterFlowable(self, flowable):
        if isinstance(flowable, Recorder):
            SECTION_PAGES[flowable.key] = self.page


def story():
    flow = []
    # cover content is drawn by the template; just a spacer
    flow += [Spacer(1, 10), NextPageTemplate("body")]

    flow += front_matter()

    for sec in ALL_SECTIONS:
        flow += [CondPageBreak(270)]
        flow += [Recorder("S%s" % sec["num"])]
        flow += [Recorder("H%s" % sec["num"],
                          "Section %s  %s" % (sec["num"], sec["title"]), level=0)]
        flow += [SectionDivider(sec["num"], sec["kicker"], sec["title"], sec["intro"]), Spacer(1, 14)]
        for task in sec["tasks"]:
            flow += [Recorder("T%s" % task["id"], "%s  %s" % (task["id"], task["title"]), level=1)]
            flow += [task_block(task), Spacer(1, 12)]
            if task.get("note"):
                flow += [note_box(task["note"]), Spacer(1, 18)]

    for app in APPENDICES:
        flow += [PageBreak(), Recorder("A%s" % app["num"])]
        flow += [Recorder("H%s" % app["num"],
                          "Appendix %s  %s" % (app["num"], app["title"]), level=0)]
        flow += [SectionDivider(app["num"], app["kicker"], app["title"], app["intro"]), Spacer(1, 12)]
        for block in app["blocks"]:
            flow += appendix_block(block)
        after = app.get("after", [])
        if after:
            group = []
            for block in after:
                if isinstance(block, str):
                    group.append(Paragraph(m(block), st_body))
                else:
                    group += appendix_block(block)
            flow += [KeepTogether(group)]
    return flow


ALL_SECTIONS = SECTIONS_BCD + SECTIONS_REST

# attach the printed mark allocation to every part and sanity-check the totals
for _sec in ALL_SECTIONS:
    for _task in _sec["tasks"]:
        _marks = PART_MARKS[_task["id"]]
        if len(_marks) != len(_task["parts"]):
            raise SystemExit("mark/part mismatch in %s: %d marks, %d parts"
                             % (_task["id"], len(_marks), len(_task["parts"])))
        if sum(_marks) != _task["marks"]:
            raise SystemExit("total mismatch in %s: %d vs %d"
                             % (_task["id"], sum(_marks), _task["marks"]))
        for _part, _m in zip(_task["parts"], _marks):
            _part["m"] = _m


def build(path, page_map=None):
    global SECTION_PAGES
    SECTION_PAGES = dict(page_map or {})
    doc = Doc(path)
    doc.build(story())
    return dict(SECTION_PAGES), doc.page


def main():
    out = os.path.join(HERE, "MYP5-eAssessment-Answer-Sheet.pdf")
    pages1, total1 = build("/tmp/_pass1.pdf", {})
    SECTION_INDEX.clear()
    labels = {}
    for sec in ALL_SECTIONS:
        labels["S%s" % sec["num"]] = "Section %s · %s" % (sec["num"], sec["title"])
    for app in APPENDICES:
        labels["A%s" % app["num"]] = "Appendix %s · %s" % (app["num"], app["title"])
    for k, p in pages1.items():
        if labels.get(k):
            SECTION_INDEX.append((k, p, labels[k]))
    pages2, total2 = build(out, pages1)
    print("built", out, "pages:", total2)
    for k in sorted(pages1, key=lambda x: pages1[x]):
        print("  %-5s p.%s" % (k, pages1[k]))


if __name__ == "__main__":
    main()
