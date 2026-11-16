# -*- coding: utf-8 -*-
"""
生成课堂展示 PPT（简洁版，12 页）

用法： python 作业/可视化/做PPT.py
输出： 作业/中期展示.pptx（可用环境变量 PPT_OUT 改名）

设计：白底、单一强调色、无表格线、每页一个观点；
      图片来自 作业/图集/（先跑 可视化/导出图.py）。
"""
import os
import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

sys.stdout.reconfigure(encoding='utf-8')

R = Path(__file__).resolve().parent.parent
IMGDIR = R / '图集'
OUT = R / os.environ.get('PPT_OUT', '中期展示.pptx')

# ── 设计系统 ──
INK = RGBColor(0x11, 0x18, 0x27)
SUB = RGBColor(0x4B, 0x55, 0x63)
DIM = RGBColor(0x9C, 0xA3, 0xAF)
ACC = RGBColor(0x25, 0x63, 0xEB)
GREEN = RGBColor(0x05, 0x96, 0x69)
RED = RGBColor(0xDC, 0x26, 0x26)
SLATE = RGBColor(0x47, 0x55, 0x69)
LINE = RGBColor(0xE5, 0xE7, 0xEB)
FONT = 'Microsoft YaHei'
TOTAL = 13

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def set_font(run, size, bold, color):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.color.rgb = color
    f.name = FONT
    rPr = run._r.get_or_add_rPr()
    latin = rPr.get_or_add_latin()
    latin.set('typeface', FONT)
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        latin.addnext(ea)
    ea.set('typeface', FONT)


def text(slide, x, y, w, h, items, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         spacing=1.25):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, (t, size, bold, color, sb) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_before = Pt(sb)
        r = p.add_run()
        r.text = t
        set_font(r, size, bold, color)
    return box


def rect(slide, x, y, w, h, color, line=None):
    shp = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.75)
    shp.shadow.inherit = False
    return shp


def head(slide, label, title, n):
    rect(slide, 0.9, 0.62, 0.09, 0.09, ACC)
    text(slide, 1.08, 0.55, 9.0, 0.3, [(label, 10.5, True, ACC, 0)])
    text(slide, 0.9, 0.9, 11.6, 0.8, [(title, 27, True, INK, 0)], spacing=1.1)
    text(slide, 12.0, 7.02, 0.55, 0.25, [(f'{n:02d}', 10, False, DIM, 0)],
         align=PP_ALIGN.RIGHT)


def pic(slide, name, x, y, w, h):
    p = IMGDIR / name
    if not p.exists():
        text(slide, x, y, w, h, [(f'缺少 {name}', 12, False, RED, 0)])
        return
    iw, ih = Image.open(p).size
    sc = min(w / iw, h / ih)
    pw, ph = iw * sc, ih * sc
    slide.shapes.add_picture(str(p), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2),
                             Inches(pw), Inches(ph))


def big(slide, x, y, w, value, label, color=INK, size=44):
    text(slide, x, y, w, 0.9, [(value, size, True, color, 0)], spacing=1.0)
    text(slide, x, y + size / 72 * 1.08, w, 0.35, [(label, 11, False, SUB, 0)])


def bar(slide, x, y, w, h, segs):
    cx = x
    for v, col in segs:
        bw = w * v / 100
        rect(slide, cx, y, bw, h, col)
        cx += bw
    return cx


# ═════════════ 1 封面 ═════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0.9, 1.62, 0.10, 1.35, ACC)
text(s, 1.18, 1.55, 8.0, 0.35, [('大数据原理与应用 · 中期项目', 12, False, SUB, 0)])
text(s, 1.18, 2.0, 11.2, 1.7,
     [('开源软件生态中的', 34, True, INK, 0), ('「基础设施层」及其供养结构', 34, True, INK, 6)],
     spacing=1.15)
text(s, 1.18, 4.0, 10.8, 0.5,
     [('7 个独立数据源 · 132 个月度快照 · 3 个核心问题 + 1 个双源对照', 15, False, ACC, 0)])
rect(s, 1.18, 6.15, 11.2, 0.012, LINE)
text(s, 1.18, 6.35, 11.2, 0.5,
     [('单人为组 ｜ 2026-11-16 ｜ github.com/lzt-2077/opensource-infra-midterm', 11, False, DIM, 0)])

# ═════════════ 2 问题 ═════════════
s = prs.slides.add_slide(BLANK)
head(s, '01  研究设计', '一个所有人都依赖、却没人直接卖的层，谁来供养？', 2)
items = [
    ('01', '谁在供养底基？', '依赖图 × 账号主体', '只有 owner_id，不知道背后是人还是公司。'),
    ('02', '公司造地基，还是用现成？', '依赖图 × 账号主体 × 公司实体', '只看公司自有账号，会漏掉大部分影响力。'),
    ('03', '钱和位置匹配吗？', '依赖图 × 年报 / 990', '位置和钱不接起来，无法判断是否错配。'),
]
for i, (num, q, src, why) in enumerate(items):
    x = 0.9 + i * 3.95
    text(s, x, 2.1, 3.6, 0.3, [(num, 11, True, ACC, 0)])
    text(s, x, 2.45, 3.6, 0.85, [(q, 18, True, INK, 0)], spacing=1.2)
    text(s, x, 3.3, 3.6, 0.35, [(src, 11.5, True, SLATE, 0)])
    text(s, x, 3.7, 3.4, 0.9, [(why, 11.5, False, SUB, 0)], spacing=1.5)
rect(s, 0.9, 5.35, 11.5, 0.012, LINE)
text(s, 0.9, 5.55, 11.5, 0.5,
     [('另一个双源对照：cargo × PyPI —— 没有公共实体键，属于同法复现，不计入核心问题。', 11, False, DIM, 0)])

# ═════════════ 3 数据 ═════════════
s = prs.slides.add_slide(BLANK)
head(s, '02  数据', '7 个独立源，去重后 4.8 GB', 3)
srcs = [
    ('S1', 'crates.io dump', '3.2 GB', '依赖图（主干）'),
    ('S2', 'PyPI 全量', '1.4 GB', '跨生态对照'),
    ('S3', 'GitHub API', '60 MB', '账号主体'),
    ('S4', '基金会年报', '100 MB', '钱'),
    ('S5', '学术文献', '6 MB', '基础设施定义'),
    ('S6', 'LF / CNCF 映射', '120 KB', '机构名'),
    ('S7', 'npm / Maven 试点', '17 MB', '外部压力测试'),
    ('ALL', '合计', '4.8 GB', '最大单源 66.7%'),
]
for i, (tag, name, size, role) in enumerate(srcs):
    row, col = divmod(i, 4)
    x = 0.9 + col * 2.93
    y = 1.95 + row * 2.05
    rect(s, x, y, 2.72, 0.012, LINE)
    text(s, x, y + 0.12, 2.6, 0.25, [(tag, 10, True, ACC if tag != 'ALL' else DIM, 0)])
    text(s, x, y + 0.4, 2.6, 0.5, [(name, 14, True, INK, 0)], spacing=1.1)
    text(s, x, y + 0.95, 2.6, 0.3, [(size, 11, False, SUB, 0)])
    text(s, x, y + 1.25, 2.6, 0.3, [(role, 10.5, False, DIM, 0)])
text(s, 0.9, 6.0, 11.5, 0.5,
     [('S1 与 S2 是两个相互独立的包生态，不是同一底层数据的分片。', 10.5, False, DIM, 0)])

# ═════════════ 4 关联（原生图）═════════════
s = prs.slides.add_slide(BLANK)
head(s, '03  关联', '七个源怎么接成一张表？', 4)
cols = [
    (0.9, 2.2, '原始源（7）'),
    (3.45, 2.2, '关联键'),
    (6.1, 2.7, '融合层'),
    (9.55, 3.0, '问题'),
]
for x, w, name in cols:
    rect(s, x, 1.8, w - 0.25, 0.012, LINE)
    text(s, x, 1.9, w - 0.2, 0.3, [(name, 10.5, True, ACC, 0)])
s1 = ['S1  crates.io dump', 'S2  PyPI 全量', 'S3  GitHub API', 'S4  基金会年报 / 990',
      'S5  学术文献', 'S6  LF / CNCF 映射', 'S7  npm / Maven']
for i, t in enumerate(s1):
    text(s, 0.9, 2.4 + i * 0.5, 2.4, 0.35, [(t, 10.5, False, INK, 0)])
s2 = ['crate_id / name', 'owner_id → GitHub login', 'created_at → 月度锚点',
      '仓库组织 → 域名 → 机构名', 's → t 依赖边']
for i, t in enumerate(s2):
    text(s, 3.45, 2.4 + i * 0.65, 2.5, 0.35, [(t, 10.5, False, INK, 0)])
s3 = [('包级融合表', '171,730 × 30'), ('包 × 账号 × 主体', '422,586 行'),
      ('月度快照序列', '132 个，零缺失')]
for i, (a, b) in enumerate(s3):
    y = 2.35 + i * 1.15
    text(s, 6.1, y, 2.7, 0.3, [(a, 11.5, True, INK, 0)])
    text(s, 6.1, y + 0.3, 2.7, 0.3, [(b, 10.5, False, SUB, 0)])
    rect(s, 6.1, y + 0.75, 2.4, 0.012, LINE)
s4 = [('Q1', '谁在供养底基'), ('Q2', '造地基还是用现成'),
      ('Q3', '钱和位置是否匹配'), ('Q4', '两个生态的对照')]
for i, (q, t) in enumerate(s4):
    y = 2.35 + i * 0.95
    text(s, 9.55, y, 3.2, 0.3, [(q, 10.5, True, ACC, 0)])
    text(s, 9.95, y, 2.8, 0.3, [(t, 10.5, False, INK, 0)])
for x in [3.15, 5.8, 9.2]:
    text(s, x, 3.15, 0.3, 0.4, [('→', 16, False, DIM, 0)])
text(s, 0.9, 6.25, 11.5, 0.5,
     [('S1×S2 没有公共实体键：cargo 与 PyPI 只做同法复现，不做实体融合。', 10.5, False, DIM, 0)])

# ═════════════ 5 方法：底基怎么划 ═════════════
s = prs.slides.add_slide(BLANK)
head(s, '04  方法', '底基怎么划？四个步骤，132 次', 5)
steps = [
    ('1  取时点', '每月一个锚点：2015-01 → 2025-12，共 132 个。'),
    ('2  建图 G(t)', '每个包取 t 之前的最新版本；只留 kind=0 且 optional=false 的依赖；去自环。'),
    ('3  算入度', 'indeg(x) = 有多少个不同的包直接依赖 x（按包去重，不按版本）。'),
    ('4  套门槛', 'B(t) = { x : indeg(x) ≥ θ(t) }，θ(t) = 366 × √( N(t) / 174,799 )。'),
]
for i, (k, v) in enumerate(steps):
    y = 1.95 + i * 1.0
    text(s, 0.9, y, 6.2, 0.3, [(k, 11, True, ACC, 0)])
    text(s, 0.9, y + 0.3, 6.4, 0.6, [(v, 10.5, False, INK, 0)], spacing=1.35)
text(s, 7.55, 1.95, 4.9, 0.3, [('符号与参数', 11, True, SUB, 0)])
sym = [
    ('N(t)', '当期有依赖行为的包数：407 → 174,799。'),
    ('366', '2025-12 的门槛；底基 = 入度 ≥ 366，共 319 个。'),
    ('α = 0.5', '五档扫描：≤ 0.25 早期为空，≥ 0.75 月流失 0.6–1%。'),
]
for i, (k, v) in enumerate(sym):
    y = 2.35 + i * 1.15
    text(s, 7.55, y, 1.05, 0.3, [(k, 11, True, INK, 0)])
    text(s, 8.5, y, 3.85, 0.7, [(v, 10, False, SUB, 0)], spacing=1.35)
rect(s, 0.9, 5.55, 11.5, 0.012, LINE)
text(s, 0.9, 5.7, 11.5, 0.4,
     [('2015-01：θ = 17.7，底基 5 个（1.23%）　→　2025-12：θ = 366，底基 319 个（0.18%）', 13, True, INK, 0)])
text(s, 0.9, 6.25, 11.5, 0.7,
     [('θ 只依赖当期包数 N(t)，与谁在榜上无关——这是它比「取前 N 名」更稳的原因。', 10, False, DIM, 0),
      ('末期的 366 是校准选择：使 2025-12 底基占 0.18%（319 个包），不是从数据里推出来的。', 9.5, False, DIM, 4)],
     spacing=1.35)

# ═════════════ 5b 稳定性与负面结果 ═════════════
s = prs.slides.add_slide(BLANK)
head(s, '04b  稳定性', '为什么不用固定排名？', 6)
text(s, 0.9, 1.9, 5.4, 0.3, [('固定取前 450 名', 10.5, True, SUB, 0)])
text(s, 0.9, 2.2, 5.4, 0.6, [('月均退出 4.39%，最坏 88.94%', 18, True, RED, 0)])
text(s, 0.9, 3.0, 5.4, 0.3, [('绝对门槛 θ(t)', 10.5, True, SUB, 0)])
text(s, 0.9, 3.3, 5.4, 0.6, [('月均 0.27%；Jaccard 中位 0.978', 18, True, GREEN, 0)])
text(s, 0.9, 4.2, 5.35, 1.2,
     [('原因：入度是累积量，几乎单调不减；排名是相对量，分母一动就整体洗牌。', 11, False, SUB, 0)], spacing=1.45)
text(s, 6.9, 1.9, 5.5, 0.3, [('聚类：6 种方法，5 种失败', 11, True, SUB, 0)])
text(s, 6.9, 2.3, 5.5, 3.4,
     [('同图换随机种子 ARI 0.570 ｜ 相邻两个月 0.584 ｜ 相隔 17 个月 0.620', 11.5, False, INK, 0),
      ('三个数几乎相同 → 不稳定来自算法，而不是数据漂移。', 10.5, False, SUB, 8),
      ('有效做法：只对骨架聚类，其余 argmax 归入；ARI 0.92，且随月距单调衰减。', 10.5, False, INK, 12)],
     spacing=1.45)
rect(s, 0.9, 6.0, 11.5, 0.012, LINE)
text(s, 0.9, 6.15, 11.5, 0.5,
     [('ARI 与会话内实验在溯源总表标 B 级（无脚本）；固定排名的 4.39% 同样无脚本。', 10, False, DIM, 0)])

# ═════════════ 6 Q1 ═════════════
s = prs.slides.add_slide(BLANK)
head(s, '05  Q1', '底基几乎没有被组织成「需要法人」的形态', 7)
text(s, 0.9, 1.8, 11.5, 0.3, [('底基 319 个包（入边加权）', 10.5, False, DIM, 0)])
vals = [('77.9%', '无（项目组织 + 个人）', SLATE), ('10.4%', '非营利', GREEN),
        ('10.3%', '未知', DIM), ('1.4%', '公司', RED)]
for i, (v, lab, col) in enumerate(vals):
    big(s, 0.9 + i * 3.0, 2.15, 2.7, v, lab, col, 42)
text(s, 0.9, 3.5, 11.5, 0.3, [('底基 319 个包', 9.5, False, DIM, 0)])
bar(s, 0.9, 3.75, 11.5, 0.28, [(77.9, SLATE), (10.4, GREEN), (10.3, RGBColor(0xF3, 0xF4, 0xF6)), (1.4, RED)])
text(s, 0.9, 4.2, 11.5, 0.3, [('全库 1,089,488 条入边', 9.5, False, DIM, 0)])
bar(s, 0.9, 4.45, 11.5, 0.28, [(74.58, SLATE), (8.17, GREEN), (12.75, RGBColor(0xF3, 0xF4, 0xF6)), (4.51, RED)])
text(s, 0.9, 5.0, 11.5, 0.9,
     [('全库公司 4.51%（剔除组织内部依赖 2.70%）；按包数公司 16/319 = 5.0%。', 11, False, SUB, 0),
      ('项目组织入边 490,016 条中，仅 1.23%（6,026 条）有 CNCF/LF 或 NumFOCUS 托管。', 11, False, SUB, 6)],
     spacing=1.4)
text(s, 0.9, 6.55, 11.5, 0.4,
     [('三列模型：法人类型 × 组织形态 × 财政赞助，三个维度正交，不可相加。', 9.5, False, DIM, 0)])

# ═════════════ 7 Q2 ═════════════
s = prs.slides.add_slide(BLANK)
head(s, '06  Q2', '公司的影响力，主要不在公司自己的账号上', 8)
text(s, 0.9, 1.85, 5.4, 1.3, [('94.1%', 72, True, ACC, 0)], spacing=1.0)
text(s, 0.9, 3.15, 5.6, 0.8,
     [('8,175 个「公司参与」的包中，7,692 个没有任何公司组织账号。', 12.5, False, INK, 0)], spacing=1.45)
text(s, 0.9, 3.95, 5.6, 0.3, [('有公司账号 483 个（5.9%）', 10, False, RED, 0)])
bar(s, 0.9, 4.25, 5.6, 0.22, [(5.9, RED), (94.1, ACC)])
text(s, 0.9, 4.65, 5.6, 0.3, [('无公司账号 7,692 个', 10, False, ACC, 0)])
text(s, 7.0, 1.95, 5.4, 3.2,
     [('同一批包，换一套标签', 11, True, SUB, 0),
      ('账号级 94.1% ｜ 命名空间级 84.9%', 15, True, INK, 10),
      ('按 corp_share ≥ 0.5 复算：93.2%', 11.5, False, SUB, 14),
      ('「公司参与」= 仓库内至少一次公司域名提交（中位 5.6%），定义很松。', 10.5, False, DIM, 12)],
     spacing=1.4)
rect(s, 0.9, 5.6, 11.5, 0.012, LINE)
text(s, 0.9, 5.75, 11.5, 0.5,
     [('这是账号级计数，不解释为「隐瞒所有权」；它只说：公司员工有提交的包里，公司组织账号几乎不出现。', 10, False, DIM, 0)])

# ═════════════ 8 Q3 ═════════════
s = prs.slides.add_slide(BLANK)
head(s, '07  Q3', '钱和位置，没有稳定对应', 9)
cards = [
    ('OpenSSL', '1,397', '条 Rust 入边', '68.7 万美元', '支出 93.1 万 → 储备 51.7 万 → 28.9 万（赤字 22.8 万）'),
    ('Blender', '4', '条 Rust 入边', '571 万欧元', '收入 255 万（2023）→ 571 万（2025），两年 +124%'),
]
for i, (name, edges, unit, money, note) in enumerate(cards):
    x = 0.9 + i * 6.0
    rect(s, x, 1.95, 5.4, 0.012, LINE)
    text(s, x, 2.1, 5.2, 0.4, [(name, 20, True, INK, 0)])
    text(s, x, 2.65, 2.5, 0.9, [(edges, 40, True, ACC, 0)], spacing=1.0)
    text(s, x + 2.1, 2.9, 2.0, 0.3, [(unit, 10.5, False, SUB, 0)])
    text(s, x, 3.65, 5.2, 0.45, [(money, 18, True, INK, 0)])
    text(s, x, 4.2, 5.0, 0.9, [(note, 10.5, False, SUB, 0)], spacing=1.45)
rect(s, 0.9, 5.55, 11.5, 0.012, LINE)
text(s, 0.9, 5.7, 11.5, 0.9,
     [('两个案例不在同一总体（Rust 的 C 库绑定 vs C++ 桌面应用），只作「不存在简单对应」的反例，不能当作定量「脱钩」证据。', 10.5, False, DIM, 0),
      ('OpenSSL 的 22.8 万是现金储备变动；收入 − 支出 = −24.5 万，差 1.6 万为权责发生制与收付实现制之差。', 9.5, False, DIM, 5)],
     spacing=1.4)

# ═════════════ 9 Q4 ═════════════
s = prs.slides.add_slide(BLANK)
head(s, '08  Q4（双源对照）', '两个生态的头部结构一样吗？', 10)
pic(s, '图6-两生态对照.png', 0.55, 1.75, 8.1, 3.55)
text(s, 9.0, 1.8, 1.6, 0.3, [('PyPI', 10, True, ACC, 0)])
text(s, 10.7, 1.8, 1.6, 0.3, [('cargo', 10, True, GREEN, 0)])
nums = [('Gini', '0.924', '0.902'), ('top100 占边', '50.0%', '54.3%'),
        ('top1000 占边', '77.5%', '77.3%')]
for i, (lab, a, b) in enumerate(nums):
    y = 2.2 + i * 1.15
    text(s, 9.0, y, 3.5, 0.3, [(lab, 10, False, DIM, 0)])
    text(s, 9.0, y + 0.25, 1.7, 0.5, [(a, 19, True, ACC, 0)])
    text(s, 10.7, y + 0.3, 1.7, 0.4, [(b, 15, False, GREEN, 0)])
text(s, 9.0, 5.75, 3.6, 0.8,
     [('无公共键 → 同法复现，不是实体融合。', 10, False, DIM, 0)], spacing=1.3)

# ═════════════ 10 时间 ═════════════
s = prs.slides.add_slide(BLANK)
head(s, '09  时间', '90% 的依赖集中在多少比例的包里？', 11)
pic(s, '图1-依赖集中度.png', 1.0, 1.8, 11.2, 3.95)
text(s, 1.0, 5.95, 11.2, 0.8,
     [('入度是累积量：越晚加入的包越难进入头部，因此覆盖 90% 依赖所需的包占比持续下降（40.5% → 4.8%）。', 10.5, False, DIM, 0)],
     spacing=1.4)

# ═════════════ 11 网络 ═════════════
s = prs.slides.add_slide(BLANK)
head(s, '10  网络', '谁在支撑别人的运行时？', 12)
pic(s, '图3-谁在支撑运行时.png', 0.45, 1.65, 5.8, 4.55)
pic(s, '图8-领域分块-76块.png', 6.5, 1.65, 6.3, 4.55)
text(s, 0.45, 6.3, 5.8, 0.6, [('入度 top-24：语言原语、工具、运行时与应用框架混在同一层', 10.5, False, SUB, 0)], spacing=1.35)
text(s, 6.5, 6.3, 6.3, 0.6,
     [('探索性聚类：76 个领域块（Q=0.79）；因跨月不稳定未进入结论', 10.5, False, SUB, 0)], spacing=1.35)

# ═════════════ 12 局限 / 复现 ═════════════
s = prs.slides.add_slide(BLANK)
head(s, '11  可靠性', '已知局限、核验方式与复现入口', 13)
cols = [
    ('局限', ['幸存者偏差：越早的快照越偏向活到 2026 的包', 'req 版本约束未解析，残余伪边',
              '账号级实体解析仅 47.1%', 'build 依赖层缺失（cc 不在图内）']),
    ('核验', ['头条数字都有一次不依赖 AI 的独立复算', '5 个 AI 错误全部由「回原始数据核对」发现',
              'ARI 与会话内实验标 B 级，不写进结论', '口径差异主动报两套（94.1% / 84.9%）']),
    ('复现', ['README 四步命令', '可视化/导出图.py → 图集/', '可视化/做PPT.py → 本 PPT',
              'github.com/lzt-2077/opensource-infra-midterm']),
]
for i, (title, rows) in enumerate(cols):
    x = 0.9 + i * 3.95
    text(s, x, 1.95, 3.6, 0.35, [(title, 13, True, ACC, 0)])
    text(s, x, 2.4, 3.55, 3.4, [(r, 10.5, False, INK, 10) for r in rows], spacing=1.45)
rect(s, 0.9, 6.1, 11.5, 0.012, LINE)
text(s, 0.9, 6.25, 11.5, 0.5,
     [('AI 承担约 80% 代码；选题、口径与「这个数字不可信」的判断由人做。完整记录见 AI_USAGE.md。', 10, False, DIM, 0)])

prs.save(OUT)
print(f'已写 {OUT}  ({OUT.stat().st_size/1024:.0f} KB)，共 {len(prs.slides._sldIdLst)} 页')
