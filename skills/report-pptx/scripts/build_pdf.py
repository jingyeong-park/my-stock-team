# -*- coding: utf-8 -*-
"""report-pptx PDF 렌더러: spec JSON -> 디자인된 PDF.

사용법: python build_pdf.py <spec.json> <output.pdf>

build_pptx.py와 동일한 spec·디자인(KB 옐로우 #FFBC00, 맑은 고딕, 16:9)으로
PDF를 직접 생성한다. PowerPoint/LibreOffice가 없는 환경용.
"""
import json
import sys
from pathlib import Path

from fpdf import FPDF

# 16:9 (PPTX와 동일 비율, mm)
PAGE_W, PAGE_H = 338.67, 190.5
KB_YELLOW = (255, 188, 0)
DARK = (58, 58, 58)
GRAY = (140, 140, 140)
LIGHT = (245, 245, 245)
WHITE = (255, 255, 255)
MARGIN = 14.0
MAX_TABLE_ROWS = 8
MAX_CHART_POINTS = 120

FORBIDDEN = [
    "매수 추천", "매도 추천", "강력 매수", "강력 매도",
    "사야 합니다", "팔아야 합니다", "사야 한다", "팔아야 한다",
    "목표주가", "목표가 ", "적정주가",
]
DISCLAIMER = "본 자료는 학습용 분석이며 투자 권유가 아닙니다."


class Report(FPDF):
    def __init__(self):
        super().__init__(orientation="L", unit="mm", format=(PAGE_H, PAGE_W))
        self.set_auto_page_break(False)
        self.add_font("malgun", "", r"C:\Windows\Fonts\malgun.ttf")
        self.add_font("malgun", "B", r"C:\Windows\Fonts\malgunbd.ttf")
        self.total_pages = 7

    def t(self, size, bold=False, color=DARK):
        self.set_font("malgun", "B" if bold else "", size)
        self.set_text_color(*color)

    def rect_fill(self, x, y, w, h, color):
        self.set_fill_color(*color)
        self.rect(x, y, w, h, "F")

    def title_bar(self, title):
        self.rect_fill(MARGIN, 11, 3.3, 11.5, KB_YELLOW)
        self.t(20, bold=True)
        self.set_xy(MARGIN + 7, 9.5)
        self.cell(0, 14, title)

    def footer_bar(self, page_no):
        self.t(7.5, color=GRAY)
        self.set_xy(MARGIN, PAGE_H - 11)
        self.cell(0, 6, DISCLAIMER)
        self.set_xy(PAGE_W - MARGIN - 20, PAGE_H - 11)
        self.cell(20, 6, f"{page_no} / {self.total_pages}", align="R")

    def bullets(self, x, y, w, items, size=11, gap=3.5, color=DARK):
        self.set_xy(x, y)
        for b in items:
            self.t(size, color=color)
            self.set_x(x)
            self.multi_cell(w, size * 0.62, "•  " + b)
            self.ln(gap)
        return self.get_y()


def draw_table(pdf, x, y, w, columns, rows):
    omitted = 0
    if len(rows) > MAX_TABLE_ROWS:
        omitted = len(rows) - MAX_TABLE_ROWS
        rows = rows[:MAX_TABLE_ROWS]
    size = 11 if len(rows) <= 5 else 9
    row_h = size * 0.62 + 4.5
    col_w = [w * 0.34] + [(w * 0.66) / (len(columns) - 1)] * (len(columns) - 1)
    # 헤더
    pdf.set_xy(x, y)
    pdf.t(size, bold=True)
    pdf.set_fill_color(*KB_YELLOW)
    for j, col in enumerate(columns):
        pdf.cell(col_w[j], row_h, str(col), border=0, align="C", fill=True)
    # 본문
    for i, row in enumerate(rows):
        pdf.set_xy(x, y + row_h * (i + 1))
        pdf.set_fill_color(*(WHITE if i % 2 == 0 else LIGHT))
        pdf.t(size)
        for j in range(len(columns)):
            val = str(row[j]) if j < len(row) else ""
            pdf.cell(col_w[j], row_h, val, border=0,
                     align="L" if j == 0 else "R", fill=True)
    y_end = y + row_h * (len(rows) + 1)
    if omitted:
        pdf.t(8, color=GRAY)
        pdf.set_xy(x, y_end + 1)
        pdf.cell(0, 5, f"※ 지면 관계상 {omitted}행 생략")
        y_end += 6
    return y_end


def draw_chart(pdf, x, y, w, h, chart):
    cats = list(chart["categories"])
    values = list(chart["series"][0]["values"])
    name = chart["series"][0].get("name", "")
    if len(values) > MAX_CHART_POINTS:
        step = max(1, len(values) // MAX_CHART_POINTS)
        idx = list(range(0, len(values), step))
        if idx[-1] != len(values) - 1:
            idx.append(len(values) - 1)
        cats = [cats[i] for i in idx]
        values = [values[i] for i in idx]
    vmin, vmax = min(values), max(values)
    pad = (vmax - vmin) * 0.08 or 1
    vmin, vmax = vmin - pad, vmax + pad
    # 플롯 영역
    pdf.rect_fill(x, y, w, h, LIGHT)
    # y축 그리드 + 라벨 (4분할)
    pdf.set_draw_color(220, 220, 220)
    pdf.set_line_width(0.2)
    pdf.t(7, color=GRAY)
    for k in range(5):
        gy = y + h - (h * k / 4)
        pdf.line(x, gy, x + w, gy)
        val = vmin + (vmax - vmin) * k / 4
        pdf.set_xy(x - 23, gy - 2)
        pdf.cell(21, 4, f"{val:,.0f}", align="R")
    # 라인
    pts = []
    n = len(values)
    for i, v in enumerate(values):
        px = x + (w * i / (n - 1 if n > 1 else 1))
        py = y + h - h * (v - vmin) / (vmax - vmin)
        pts.append((px, py))
    pdf.set_draw_color(*KB_YELLOW)
    pdf.set_line_width(0.9)
    for a, b in zip(pts, pts[1:]):
        pdf.line(a[0], a[1], b[0], b[1])
    # x축 라벨 (처음/중간/끝)
    pdf.t(7, color=GRAY)
    for frac, align in ((0, "L"), (0.5, "C"), (1, "R")):
        i = int(frac * (n - 1))
        pdf.set_xy(x if align != "R" else x + w - 30,
                   y + h + 1.5)
        if align == "C":
            pdf.set_x(x + w / 2 - 15)
        pdf.cell(30, 4, str(cats[i]), align=align)
    if name:
        pdf.t(8, color=GRAY)
        pdf.set_xy(x, y - 5)
        pdf.cell(0, 4, name)


# ---------- 페이지 ----------

def page_cover(pdf, spec):
    pdf.add_page()
    pdf.rect_fill(0, 0, 9, PAGE_H, KB_YELLOW)
    pdf.rect_fill(9, PAGE_H - 16, PAGE_W - 9, 16, LIGHT)
    pdf.t(34, bold=True)
    pdf.set_xy(26, 66)
    pdf.cell(0, 16, f"{spec['ticker_name']} 리서치 리포트")
    pdf.t(13, color=GRAY)
    code = spec.get("ticker_code", "")
    if code:
        pdf.set_xy(26, 86)
        pdf.cell(0, 8, f"종목코드 {code}")
    pdf.set_xy(26, 95)
    pdf.cell(0, 8, f"작성일 {spec['date']}")
    pdf.t(9, color=GRAY)
    pdf.set_xy(26, PAGE_H - 13)
    pdf.cell(0, 8, f"Stock Team 협업 리서치  |  {DISCLAIMER}")


def page_overview(pdf, spec):
    pdf.add_page()
    pdf.title_bar("종목 개요")
    pdf.bullets(MARGIN + 7, 35, PAGE_W - 2 * MARGIN - 14,
                spec["overview"]["bullets"][:7], size=12.5, gap=5)
    pdf.footer_bar(2)


def page_financials(pdf, spec):
    pdf.add_page()
    pdf.title_bar("재무 요약")
    fin = spec["financials"]
    y = draw_table(pdf, MARGIN + 7, 33, PAGE_W - 2 * MARGIN - 14,
                   fin["columns"], fin["rows"])
    y = pdf.bullets(MARGIN + 7, y + 8, PAGE_W - 2 * MARGIN - 14,
                    fin.get("bullets", [])[:4], size=10.5, gap=2.5)
    if fin.get("note"):
        pdf.t(8, color=GRAY)
        pdf.set_xy(MARGIN + 7, min(y + 2, PAGE_H - 22))
        pdf.cell(0, 5, fin["note"])
    pdf.footer_bar(3)


def page_price(pdf, spec):
    pdf.add_page()
    pdf.title_bar("가격 / 추세")
    price = spec["price"]
    chart = price.get("chart")
    if chart and chart.get("categories") and chart.get("series"):
        draw_chart(pdf, MARGIN + 24, 40, 150, 105, chart)
        bx, bw = MARGIN + 24 + 158, PAGE_W - MARGIN - (MARGIN + 24 + 158) - 4
    else:
        bx, bw = MARGIN + 7, PAGE_W - 2 * MARGIN - 14
    pdf.bullets(bx, 38, bw, price.get("bullets", [])[:7], size=9.5, gap=3)
    if price.get("source"):
        pdf.t(8, color=GRAY)
        pdf.set_xy(MARGIN + 7, PAGE_H - 22)
        pdf.cell(0, 5, price["source"])
    pdf.footer_bar(4)


def page_news(pdf, spec):
    pdf.add_page()
    pdf.title_bar("뉴스 · 시장 심리")
    news = spec["news"]
    x, w = MARGIN + 7, PAGE_W - 2 * MARGIN - 14
    yy = 32
    for item in news["bullets"][:5]:
        pdf.t(11)
        pdf.set_xy(x, yy)
        pdf.multi_cell(w, 7, "•  " + item["text"])
        yy = pdf.get_y() + 0.5
        pdf.t(8, color=GRAY)
        pdf.set_xy(x + 6, yy)
        pdf.cell(0, 4.5, item.get("source", ""))
        yy += 8
    if news.get("sentiment"):
        pdf.rect_fill(x, PAGE_H - 34, w, 13, KB_YELLOW)
        pdf.t(11.5, bold=True)
        pdf.set_xy(x + 5, PAGE_H - 34)
        pdf.cell(0, 13, "시장 심리  |  " + news["sentiment"])
    pdf.footer_bar(5)


def page_risks(pdf, spec):
    pdf.add_page()
    pdf.title_bar("리스크")
    x, w = MARGIN + 7, PAGE_W - 2 * MARGIN - 14
    yy = 32
    for i, r in enumerate(spec["risks"][:3]):
        pdf.rect_fill(x, yy + 0.5, 8, 8, KB_YELLOW)
        pdf.t(11, bold=True)
        pdf.set_xy(x, yy + 0.5)
        pdf.cell(8, 8, str(i + 1), align="C")
        pdf.t(12.5, bold=True)
        pdf.set_xy(x + 12, yy)
        pdf.cell(0, 9, r["title"])
        pdf.t(9.5)
        pdf.set_xy(x + 12, yy + 9.5)
        pdf.multi_cell(w - 12, 5.8, "근거: " + r.get("basis", ""))
        pdf.t(9.5, color=GRAY)
        pdf.set_x(x + 12)
        pdf.multi_cell(w - 12, 5.8, "영향: " + r.get("impact", ""))
        yy = pdf.get_y() + 7
    pdf.footer_bar(6)


def page_summary(pdf, spec):
    pdf.add_page()
    pdf.title_bar("종합")
    summ = spec["summary"]
    x = 40
    pdf.rect_fill(x, 76, 30, 2.3, KB_YELLOW)
    pdf.t(17, bold=True)
    pdf.set_xy(x, 84)
    pdf.multi_cell(PAGE_W - 2 * x, 11, summ["line"])
    yy = pdf.get_y() + 6
    pdf.bullets(x, yy, PAGE_W - 2 * x, summ.get("bullets", [])[:3],
                size=10.5, gap=2.5, color=GRAY)
    pdf.footer_bar(7)


# ---------- 가드레일 ----------

def _walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)


def check_forbidden(spec):
    return [(p, s[:80]) for s in _walk_strings(spec) for p in FORBIDDEN if p in s]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) != 3:
        print("사용법: python build_pdf.py <spec.json> <output.pdf>")
        sys.exit(1)
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

    hits = check_forbidden(spec)
    if hits:
        print("[금지 표현 검출] 아래 내용을 수정한 뒤 다시 실행하세요:")
        for pat, ctx in hits:
            print(f"  - '{pat}' in: {ctx}...")
        sys.exit(2)

    pdf = Report()
    page_cover(pdf, spec)
    page_overview(pdf, spec)
    page_financials(pdf, spec)
    page_price(pdf, spec)
    page_news(pdf, spec)
    page_risks(pdf, spec)
    page_summary(pdf, spec)

    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))
    print(f"OK: {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
