# -*- coding: utf-8 -*-
"""
把 报告.md 转成排版好的 Word（报告.docx）。

用法： python 作业/可视化/做DOCX.py
输出： 作业/报告.docx

处理：标题 / 段落 / 粗体 / 行内代码 / 列表 / 引用 / 表格 / 代码块 / 图片；
     A4、宋体正文、微软雅黑标题、页眉页脚与页码、表头重复、图注。
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.stdout.reconfigure(encoding='utf-8')

R = Path(__file__).resolve().parent.parent
MD = R / '报告.md'
OUT = R / '报告.docx'
IMG = R / '图集'

INK = RGBColor(0x11, 0x18, 0x27)
SUB = RGBColor(0x4B, 0x55, 0x63)
DIM = RGBColor(0x6B, 0x72, 0x80)
ACC = RGBColor(0x1D, 0x4E, 0xD8)
BODY_FONT = '宋体'
HEAD_FONT = '微软雅黑'
MONO = 'Consolas'

doc = Document()

# ── 页面 ──
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = Cm(2.2)
sec.bottom_margin = Cm(2.2)
sec.left_margin = Cm(2.4)
sec.right_margin = Cm(2.4)
sec.different_first_page_header_footer = True
CONTENT_W = 21 - 2.4 * 2  # 16.2 cm


def set_run_font(run, size=None, bold=None, color=None, mono=False, head=False):
    f = run.font
    if size is not None:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if color is not None:
        f.color.rgb = color
    f.name = MONO if mono else (HEAD_FONT if head else 'Times New Roman')
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:ascii'), MONO if mono else ('微软雅黑' if head else 'Times New Roman'))
    rFonts.set(qn('w:hAnsi'), MONO if mono else ('微软雅黑' if head else 'Times New Roman'))
    rFonts.set(qn('w:eastAsia'), MONO if mono else (HEAD_FONT if head else BODY_FONT))


# ── 样式 ──
normal = doc.styles['Normal']
normal.font.size = Pt(10.5)
normal.font.name = 'Times New Roman'
normal._element.rPr.rFonts.set(qn('w:eastAsia'), BODY_FONT)
normal.paragraph_format.line_spacing = 1.45
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

for name, size, color, before, after in [
    ('Heading 1', 20, INK, 6, 10),
    ('Heading 2', 15.5, INK, 18, 8),
    ('Heading 3', 12.5, INK, 12, 5),
]:
    st = doc.styles[name]
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = color
    st.font.name = HEAD_FONT
    st._element.rPr.rFonts.set(qn('w:eastAsia'), HEAD_FONT)
    st.paragraph_format.space_before = Pt(before)
    st.paragraph_format.space_after = Pt(after)
    st.paragraph_format.keep_with_next = True


def para(text='', style=None, size=10.5, bold=False, color=INK, align=None,
         before=0, after=6, line=1.45, indent=0, first=0, mono=False, head=False):
    p = doc.add_paragraph(style=style)
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    pf.left_indent = Cm(indent)
    pf.first_line_indent = Cm(first)
    if align is not None:
        p.alignment = align
    if text:
        r = p.add_run(text)
        set_run_font(r, size, bold, color, mono, head)
    return p


def shade(p, fill='F6F8FA'):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    pPr.append(shd)


def left_border(p, color='1D4ED8', sz='18'):
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single')
    left.set(qn('w:sz'), sz)
    left.set(qn('w:space'), '8')
    left.set(qn('w:color'), color)
    pBdr.append(left)
    pPr.append(pBdr)


TOKEN = re.compile(r'(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))')


def cn_quotes(t):
    out = []
    open_q = True
    for ch in t:
        if ch == chr(34):
            out.append('“' if open_q else '”')
            open_q = not open_q
        else:
            out.append(ch)
    return ''.join(out)




def add_inline(p, text, size=10.5, color=INK, bold=False):
    pos = 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            r = p.add_run(cn_quotes(text[pos:m.start()]))
            set_run_font(r, size, bold, color)
        tok = m.group(0)
        if tok.startswith('**'):
            add_inline(p, tok[2:-2], size, color, bold=True)
        elif tok.startswith('`'):
            r = p.add_run(tok[1:-1])
            set_run_font(r, size - 0.5, bold, RGBColor(0x1F, 0x4E, 0xD8), mono=True)
        else:
            label = re.match(r'\[([^\]]+)\]', tok).group(1)
            r = p.add_run(label)
            set_run_font(r, size, bold, color)
        pos = m.end()
    if pos < len(text):
        r = p.add_run(cn_quotes(text[pos:]))
        set_run_font(r, size, bold, color)


def body_para(text):
    p = para()
    add_inline(p, text)
    return p


def bullet(text, num=None):
    p = para(indent=0.55, first=-0.55, after=3)
    marker = f'{num}. ' if num else '• '
    r = p.add_run(marker)
    set_run_font(r, 10.5, False, SUB)
    add_inline(p, text)
    return p


def quote(lines):
    p = para(indent=0.35, after=4, line=1.35)
    left_border(p)
    for i, line in enumerate(lines):
        if i:
            p.add_run().add_break()
        add_inline(p, line, size=9.5, color=SUB)


def code_block(lines):
    p = para(after=8, line=1.15, indent=0.15, align=WD_ALIGN_PARAGRAPH.LEFT)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    shade(p)
    p.paragraph_format.keep_together = True
    for i, line in enumerate(lines):
        line = (line.replace('├──', '|--').replace('└──', '`--')
                    .replace('│', '|').replace('─', '-'))
        if i:
            p.add_run().add_break()
        r = p.add_run(line if line else ' ')
        set_run_font(r, 8.5, False, RGBColor(0x1F, 0x29, 0x37), mono=True)


def set_cell_bg(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    tcPr.append(shd)


def set_table_borders(table):
    tblPr = table._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        el = OxmlElement(f'w:{edge}')
        el.set(qn('w:val'), 'single')
        el.set(qn('w:sz'), '4')
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), 'D0D5DD')
        borders.append(el)
    tblPr.append(borders)
    mar = OxmlElement('w:tblCellMar')
    for side, w in [('top', 30), ('left', 70), ('bottom', 30), ('right', 70)]:
        el = OxmlElement(f'w:{side}')
        el.set(qn('w:w'), str(w))
        el.set(qn('w:type'), 'dxa')
        mar.append(el)
    tblPr.append(mar)


def add_table(rows):
    header = [c.strip() for c in rows[0].strip().strip('|').split('|')]
    body = []
    for line in rows[1:]:
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < len(header):
            cells += [''] * (len(header) - len(cells))
        body.append(cells[:len(header)])
    table = doc.add_table(rows=1, cols=len(header))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    tblPr = table._tbl.tblPr
    for el in tblPr.findall(qn('w:tblW')):
        tblPr.remove(el)
    tblW = OxmlElement('w:tblW')
    tblW.set(qn('w:type'), 'dxa')
    tblW.set(qn('w:w'), str(int(CONTENT_W / 2.54 * 1440)))
    tblPr.append(tblW)
    layouts = tblPr.findall(qn('w:tblLayout'))
    for el in layouts[1:]:
        tblPr.remove(el)
    hdr = table.rows[0]
    hdr._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
    for j, h in enumerate(header):
        cell = hdr.cells[j]
        cell.text = ''
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        add_inline(p, h, size=9, bold=True)
        set_cell_bg(cell, 'EEF2F7')
    for row in body:
        tr = table.add_row()
        tr._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        for j, v in enumerate(row):
            cell = tr.cells[j]
            cell.text = ''
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.2
            add_inline(p, v, size=9)
    # 按内容长度分配列宽（中文按 2 个字符宽）
    def dlen(x):
        return sum(2 if ord(ch) > 127 else 1 for ch in re.sub(r'\*\*|`', '', x))

    maxlen = [max([dlen(r[j]) for r in [header] + body] + [4]) for j in range(len(header))]
    total = sum(maxlen)
    widths = []
    for ml in maxlen:
        min_w = 1.0 if ml <= 3 else 2.0
        widths.append(max(min_w, CONTENT_W * ml / total))
    scale = min(1.0, CONTENT_W / sum(widths))
    widths = [w * scale for w in widths]
    for j, w in enumerate(widths):
        table.columns[j].width = Cm(w)
        for row in table.rows:
            row.cells[j].width = Cm(w)

    # 整张表尽量不跨页
    for row in table.rows[:-1]:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True

    para(after=2)
    return table


def add_figure(name, caption, width=15.6):
    path = IMG / name
    if not path.exists():
        para(f'（缺少图片 {name}）', size=9, color=SUB)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(width))
    cap = para(caption, size=9, color=DIM, align=WD_ALIGN_PARAGRAPH.CENTER, after=10)
    cap.paragraph_format.keep_with_next = False


# ── 页眉页脚 ──
def add_field(paragraph, code):
    run = paragraph.add_run()
    fld1 = OxmlElement('w:fldChar')
    fld1.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = f' {code} '
    fld2 = OxmlElement('w:fldChar')
    fld2.set(qn('w:fldCharType'), 'end')
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)
    set_run_font(run, 8.5, False, DIM)


# 页眉：短标题
hp = sec.header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
hr = hp.add_run('开源软件生态中的「基础设施层」及其供养结构')
set_run_font(hr, 8.5, False, DIM)

# 页脚：日期 + 页码
fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = fp.add_run('2026-11-16　｜　第 ')
set_run_font(r, 8.5, False, DIM)
add_field(fp, 'PAGE')
r = fp.add_run(' 页 / 共 ')
set_run_font(r, 8.5, False, DIM)
add_field(fp, 'NUMPAGES')
r = fp.add_run(' 页')
set_run_font(r, 8.5, False, DIM)


# ── 封面 ──
lines = MD.read_text(encoding='utf-8').splitlines()
i = 0
cover_title = '开源软件生态中的「基础设施层」及其供养结构'
while i < len(lines) and not lines[i].strip():
    i += 1
if i < len(lines) and lines[i].startswith('# '):
    cover_title = lines[i][2:].strip()
    i += 1

meta = []
while i < len(lines) and (not lines[i].strip() or lines[i].startswith('>')):
    if lines[i].startswith('>'):
        meta.append(lines[i][1:].strip())
    i += 1
meta = [m for m in meta if m]
repo = next((m.split('：')[-1].strip() for m in meta if '代码仓库' in m), '')

para(before=100, after=10, size=11, color=SUB, text='大数据原理与应用 · 中期项目')
cover_title = cover_title.replace('"基础设施层"', '「基础设施层」')
p = para(after=6, align=WD_ALIGN_PARAGRAPH.LEFT, line=1.15)
if '「' in cover_title:
    a, b = cover_title.split('「', 1)
    r = p.add_run(a)
    set_run_font(r, 26, True, INK, head=True)
    r.add_break()
    r = p.add_run('「' + b)
    set_run_font(r, 26, True, INK, head=True)
else:
    r = p.add_run(cover_title)
    set_run_font(r, 26, True, INK, head=True)
p = para(after=6, align=WD_ALIGN_PARAGRAPH.LEFT)
r = p.add_run('多源数据融合分析报告')
set_run_font(r, 15, False, ACC, head=True)
para(after=24, size=10.5, color=SUB,
     text='7 个独立数据源　｜　132 个月度快照　｜　3 个核心问题 + 1 个双源对照')
if repo:
    p = para(after=4, size=9.5, color=DIM)
    add_inline(p, repo, size=9.5, color=DIM)
para(after=4, size=9.5, color=DIM, text='2026-11-16　｜　单人为组')
doc.add_page_break()

# ── 正文 ──
FIG = {
    '## 4. 跨源关联': ('图7-数据血缘关联图.png', '附图 A　多源数据血缘：7 个源 → 5 种连接 → 融合层', 15.2),
    '### 5.1 结构的基本形状': ('图1-依赖集中度.png', '可视化图 1　90% 的依赖边集中在多少比例的包里（2015–2025）', 15.6),
    '### 5.2 时间分析：基础设施层在扩张还是稀释': ('图2-底基扩张稀释.png', '可视化图 2　底基包数在扩张，份额在稀释', 15.0),
    '### 5.3 网络分析与数据挖掘：一个必须报告的负面结果': ('图8-领域分块-76块.png', '附图 B　探索性聚类：76 个领域块（Q = 0.79，未进入结论）', 14.5),
    '### 5.4 Q1：基础设施层由谁供养': ('图4-底基由谁供养.png', '可视化图 4　底基由谁供养（入边加权）', 15.6),
    '### 5.5 Q2：公司的影响力来自自有账号还是员工': ('图5-公司影响力.png', '可视化图 5　公司影响力：账号级计数与三种口径', 15.6),
    '### 5.7 Q4（双源对照）：两个生态的结构差异': ('图6-两生态对照.png', '可视化图 6　两个生态的 top-k 累计占边曲线', 15.0),
    '## 6. 可视化': ('图3-谁在支撑运行时.png', '可视化图 3　入度 top-24 与技术层', 12.0),
}

current_key = None


def flush_figure():
    if current_key in FIG:
        name, cap, w = FIG[current_key]
        add_figure(name, cap, w)


while i < len(lines):
    line = lines[i]
    s = line.rstrip()
    stripped = s.strip()

    if not stripped:
        i += 1
        continue

    if s.startswith('## ') or s.startswith('### '):
        flush_figure()
        level = 2 if s.startswith('## ') else 3
        current_key = s
        text = s[level + 1:].strip()
        h = doc.add_heading(level=level)
        r = h.add_run(text)
        set_run_font(r, 15.5 if level == 2 else 12.5, True, INK, head=True)
        if level == 2:
            pPr = h._p.get_or_add_pPr()
            pBdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'), 'single')
            bottom.set(qn('w:sz'), '6')
            bottom.set(qn('w:space'), '4')
            bottom.set(qn('w:color'), 'D0D5DD')
            pBdr.append(bottom)
            pPr.append(pBdr)
        i += 1
        continue

    if stripped == '---':
        p = para(after=8)
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '4')
        bottom.set(qn('w:space'), '1')
        bottom.set(qn('w:color'), 'E5E7EB')
        pBdr.append(bottom)
        pPr.append(pBdr)
        i += 1
        continue

    if s.startswith('```'):
        i += 1
        block = []
        while i < len(lines) and not lines[i].startswith('```'):
            block.append(lines[i])
            i += 1
        i += 1
        code_block(block)
        continue

    if s.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:\-\|]+\|$', lines[i + 1].strip()):
        rows = [s]
        j = i + 2
        while j < len(lines) and lines[j].startswith('|'):
            rows.append(lines[j])
            j += 1
        add_table(rows)
        i = j
        continue

    if s.startswith('>'):
        block = []
        while i < len(lines) and lines[i].startswith('>'):
            t = lines[i][1:].strip()
            if t:
                block.append(t)
            else:
                block.append('')
            i += 1
        while block and block[-1] == '':
            block.pop()
        quote(block)
        continue

    m = re.match(r'^(\d+)\.\s+(.*)$', s)
    if m:
        bullet(m.group(2), num=m.group(1))
        i += 1
        continue

    if re.match(r'^[-*]\s+', s):
        bullet(re.sub(r'^[-*]\s+', '', s))
        i += 1
        continue

    # 普通段落：合并连续非空行
    buf = [s]
    i += 1
    while i < len(lines):
        nxt = lines[i]
        ns = nxt.strip()
        if (not ns or nxt.startswith('#') or nxt.startswith('|') or nxt.startswith('```')
                or nxt.startswith('>') or ns == '---'
                or re.match(r'^\d+\.\s', nxt) or re.match(r'^[-*]\s', nxt)):
            break
        buf.append(nxt.rstrip())
        i += 1
    body_para(''.join(buf) if len(buf) == 1 else '\n'.join(buf))

flush_figure()

# 文档属性
doc.core_properties.title = cover_title
doc.core_properties.author = 'lzt'
doc.core_properties.subject = '大数据原理与应用 · 中期项目'

doc.save(OUT)
print(f'已写 {OUT}  ({OUT.stat().st_size/1024:.0f} KB)')
