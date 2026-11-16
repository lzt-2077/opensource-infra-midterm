# -*- coding: utf-8 -*-
"""
生成课堂展示 PPT（文字+表格版）

用法： python 作业/可视化/做PPT.py
输出： 作业/中期展示.pptx

说明：本脚本只生成文字与表格骨架。五张核心图请从 作业/可视化.html 截图，
      粘贴到对应页的「配图占位」处（或直接把本页替换为整页截图）。
"""
import os
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from PIL import Image
from pptx.oxml.ns import qn


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

sys.stdout.reconfigure(encoding='utf-8')
R = Path(__file__).resolve().parent.parent
OUT = R / os.environ.get('PPT_OUT', '中期展示.pptx')

INK = RGBColor(0x11, 0x18, 0x27)
DIM = RGBColor(0x6B, 0x72, 0x80)
BLUE = RGBColor(0x25, 0x63, 0xEB)
RED = RGBColor(0xDC, 0x26, 0x26)
GREEN = RGBColor(0x05, 0x96, 0x69)
LIGHT = RGBColor(0xF1, 0xF5, 0xF9)
FONT = 'Microsoft YaHei'

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def tx(slide, x, y, w, h, text, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT,
       anchor=MSO_ANCHOR.TOP, spacing=1.15):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.02)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(4)
        r = p.add_run()
        r.text = line
        set_font(r, size, bold, color)
    return box


def head(slide, kicker, title):
    tx(slide, 0.65, 0.35, 12, 0.32, kicker, 12, BLUE, bold=True)
    tx(slide, 0.65, 0.65, 12, 0.7, title, 28, INK, bold=True)
    line = slide.shapes.add_shape(1, Inches(0.65), Inches(1.42), Inches(12), Pt(1.6))
    line.fill.solid(); line.fill.fore_color.rgb = RGBColor(0xE2, 0xE8, 0xF0); line.line.fill.background()


def table(slide, x, y, w, h, rows, size=12, first_bold=True, col_widths=None):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = shp.table
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.text = str(val)
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            for p in cell.text_frame.paragraphs:
                for r in p.runs:
                    set_font(r, size, (i == 0) or (first_bold and j == 0), INK)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0xE8, 0xEE, 0xF9) if i == 0 else (
                LIGHT if i % 2 == 0 else RGBColor(0xFF, 0xFF, 0xFF))
    if col_widths:
        for j, cw in enumerate(col_widths):
            tbl.columns[j].width = Inches(cw)
    return tbl


def note(slide, text):
    tx(slide, 0.65, 6.95, 12, 0.35, text, 10, DIM)


IMGDIR = R / '图集'


def pic(slide, name, x, y, w, h):
    p = IMGDIR / name
    if not p.exists():
        tx(slide, x, y, w, h, f'（缺少 {name}，先跑 可视化/导出图.py）', 12, RED)
        return
    iw, ih = Image.open(p).size
    sc = min(w / iw, h / ih)
    pw, ph = iw * sc, ih * sc
    slide.shapes.add_picture(str(p), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2),
                             Inches(pw), Inches(ph))


def gallery(kicker, title, items, boxh=4.55, capy=6.35):
    s = prs.slides.add_slide(BLANK)
    head(s, kicker, title)
    if len(items) == 1:
        name, cap = items[0]
        pic(s, name, 1.2, 1.65, 10.9, boxh)
        tx(s, 1.2, capy, 10.9, 0.45, cap, 11, DIM)
    else:
        for (name, cap), x in zip(items, [0.4, 6.55]):
            pic(s, name, x, 1.62, 6.35, boxh)
            tx(s, x, capy, 6.35, 0.55, cap, 11, DIM)


# ───────────────────────── 1 封面 ─────────────────────────
s = prs.slides.add_slide(BLANK)
tx(s, 0.9, 1.7, 11.5, 0.4, '大数据原理与应用 · 中期项目展示', 15, DIM)
tx(s, 0.9, 2.15, 11.5, 1.0, '开源软件生态中的「基础设施层」及其供养结构', 36, INK, bold=True)
tx(s, 0.9, 3.25, 11.5, 0.6, '多源数据融合分析 ｜ 7 个独立数据源 ｜ 132 个月度依赖图快照', 18, BLUE)
tx(s, 0.9, 4.15, 11.0, 1.2,
   '一个问题：那层「所有人都依赖、但没人直接卖」的技术基础设施，究竟由谁供养？\n'
   '三个核心问题：Q1 谁供养 · Q2 公司造地基还是用现成 · Q3 资金与技术重要度是否匹配',
   15, INK, spacing=1.5)
tx(s, 0.9, 5.9, 11.5, 0.4, '单人为组 ｜ 2026-11-16 ｜ 报告 / 数据源 / 代码 / 可视化 / AI_USAGE 见提交包', 12, DIM)
tx(s, 0.9, 6.35, 11.5, 0.4, '代码仓库：github.com/lzt-2077/opensource-infra-midterm', 12, BLUE)

# ───────────────────────── 2 问题与多源设计 ─────────────────────────
s = prs.slides.add_slide(BLANK)
head(s, '01  研究设计', '三个核心问题，每个都必须跨两个以上数据源')
table(s, 0.65, 1.7, 12.0, 2.9, [
    ['核心问题', '需要的源', '为什么单一信源不够'],
    ['Q1  基础设施层由谁供养？', '依赖图 + 账号主体画像 + 机构映射',
     '依赖图只有 owner_id 数字 ID，不知道背后是人还是公司；账号画像不知道包在结构上的位置'],
    ['Q2  公司是「造地基」还是「用现成」？', '依赖图 + 账号主体 + 公司实体',
     '只看公司自有账号会漏掉绝大部分影响力（员工个人账号）'],
    ['Q3  治理与资金是否匹配技术重要度？', '依赖图 + 基金会财务文件 + 维护者规模',
     '依赖图知道位置、990 知道钱，两者不接起来无法判断错配'],
], size=12, col_widths=[3.6, 3.6, 4.8])
tx(s, 0.65, 4.85, 12.0, 1.6,
   '辅助性问题（不计入 3 个核心问题）：S1×S2 双源对照（同法复现，无公共实体键）+ S1 单源时间序列。\n'
   '判定标准：结论必须由多源共同支撑；单源只能做探索与建图。',
   13, DIM, spacing=1.4)
note(s, '对应报告 §1')

# ───────────────────────── 3 数据源 ─────────────────────────
s = prs.slides.add_slide(BLANK)
head(s, '02  数据源', '7 个独立源、6 类数据形态，去重后约 4.8 GB（单源最大 66.7%）')
table(s, 0.65, 1.65, 12.0, 3.35, [
    ['#', '数据源', '形态 / 规模', '在项目里的角色'],
    ['S1', 'crates.io 数据库全量 dump', '关系库导出 · 3.2 GB · 43,258,107 行依赖', '依赖图（主干）'],
    ['S2', 'PyPI 全量元数据（BigQuery）', 'Parquet · 1.4 GB · 6 分片', '跨生态对照（独立生态）'],
    ['S3', 'GitHub REST/GraphQL', 'JSONL · 约 60 MB', '账号主体、贡献者自报公司域名'],
    ['S4', '基金会财务文件（9 份）', 'PDF · 约 100 MB', '钱：收入、支出、储备'],
    ['S5', '学术文献', 'PDF · 约 6 MB', '基础设施的理论定义与对照方法'],
    ['S6', 'LF / CNCF 成员与域名映射', 'CSV · 120 KB', '域名 → 机构名（辅助字典）'],
    ['S7', 'npm / Maven 试点', 'JSON · 17 MB', '外部生态的压力测试'],
], size=11, col_widths=[0.6, 4.0, 4.4, 3.0])
tx(s, 0.65, 5.25, 12.0, 1.4,
   '独立性：S1 与 S2 是两个相互独立的包生态，不是同一底层数据的分片。\n'
   '规模说明：4.8 GB 为去重后实际体积；crates.io 的 2.2 GB 压缩包不计入，避免同一源重复计算。',
   13, DIM, spacing=1.5)
note(s, '对应 data_sources.md；来源等级见 依赖图/00-数据溯源总表.md')

# ───────────────────────── 4 关联与融合 ─────────────────────────
s = prs.slides.add_slide(BLANK)
head(s, '03  跨源关联', '五种关联维度，核心是一条实体链')
tx(s, 0.65, 1.65, 12.0, 1.1,
   'crate  →  crate_owners.owner_id  →  GitHub login  →  账号主体类型（个人/公司/非营利/无法人）\n'
   '              ↑ 53% 的账号无法解析（注销 / 非 GitHub / 未覆盖）→ 显式标注 unmapped，不计入分母',
   14, INK, spacing=1.5)
table(s, 0.65, 3.0, 12.0, 2.2, [
    ['维度', '做法', '结果'],
    ['实体（一级）', 'crate → owner_id → login → 主体类型', '行级 54.0%；账号级 47.1%'],
    ['时间', 'versions.created_at → 月度锚点', '132 个快照，0 缺失'],
    ['网络', 's → t 依赖边构成有向图', '入度 / 传递可达 / 技术分层'],
    ['机构（二级）', '仓库组织 → 域名 → LF/CNCF 成员名', '机构名归一化'],
    ['跨生态', '同一套方法在两个生态各跑一遍（无公共键）', 'cargo × PyPI 对照'],
], size=12, col_widths=[2.0, 6.0, 4.0])
tx(s, 0.65, 5.45, 12.0, 1.0,
   '融合结果：包级融合表 171,730 × 30；包×账号×主体 422,586 行。\n'
   '关联图：作业/关联图.html（7 源 → 五种连接 → 融合表 → 四个问题）。',
   13, DIM, spacing=1.4)
note(s, '对应报告 §4、§3.3')

# ───────────────────────── 4b 数据血缘 ─────────────────────────
s = prs.slides.add_slide(BLANK)
head(s, '03b  数据血缘', '七个源怎么接成一张可以共同分析的表？')
pic(s, '图7-数据血缘关联图.png', 0.45, 1.55, 6.9, 5.15)
tx(s, 7.55, 1.7, 5.3, 4.9,
   """三条实质性的连接

① 实体：crate → owner_id → GitHub login → 主体类型
   行级 54.0%、账号级 47.1%；未解析显式记为 unmapped

② 时间：versions.created_at → 月度锚点
   132 个快照，零缺失

③ 网络：s → t 依赖边构成有向图
   入度 / 传递可达 / 技术分层

辅助：仓库组织 → 域名 → LF/CNCF 机构名；
      S1×S2 同法复现（无公共键，不是实体融合）""",
   12, INK, spacing=1.25)
note(s, '完整图见 作业/关联图.html ｜ 对应报告 §4')

# ───────────────────────── 5 方法与负面结果 ─────────────────────────
s = prs.slides.add_slide(BLANK)
head(s, '04  方法与一个必须报告的负面结果', '先能稳定地划出「底基层」，才谈得上谁供养')
tx(s, 0.65, 1.65, 6.0, 3.6,
   '底基判据（随时间缩放）\n'
   '  θ(t) = 366 × (N(t) / N(2025-12))^0.5\n'
   '  底基 = { 入度 ≥ θ(t) }\n\n'
   '为什么不用固定排名：\n'
   '  排名规则月均退出 4.39%、最坏 88.94%；\n'
   '  绝对门槛的月度成员变动率 0.27%。\n\n'
   'α=0.5 是五档扫描的选择，不是推导（已声明）。',
   14, INK, spacing=1.4)
tx(s, 6.9, 1.65, 5.8, 3.6,
   '负面结果：50–80 块的社区发现全部不稳定\n\n'
   '  Louvain / Leiden / 共识投票 / SVD+kmeans / Ward\n'
   '  同图换种子 ARI 0.570\n'
   '  相邻两月 ARI 0.584\n'
   '  相隔 17 月 ARI 0.620\n\n'
   '→ 不同月距差异几乎相同 = 不稳定来自算法，不是数据漂移。\n'
   '→ 唯一有效：只对骨架做层次聚类，其余 argmax 归入，ARI 0.92 且随月距单调衰减。',
   14, INK, spacing=1.4)
tx(s, 0.65, 5.6, 12.0, 0.9,
   '诚实标注：ARI 三个值是会话内实验（溯源总表 B 级，无脚本）；底基序列与 N90 序列是 A 级（75/76 号脚本）。',
   12, RED, spacing=1.3)
note(s, '对应报告 §5.2、§5.3')

# ───────────────────────── 6 Q1 ─────────────────────────
s = prs.slides.add_slide(BLANK)
head(s, '05  Q1', '基础设施层几乎没有被组织成「需要法人」的形态')
table(s, 0.65, 1.7, 6.2, 3.2, [
    ['底基 319 包（入边加权）', '占底基入边'],
    ['无（项目组织 + 个人）', '77.9%'],
    ['非营利', '10.4%'],
    ['未知', '10.3%'],
    ['公司', '1.4%'],
], size=14, col_widths=[4.2, 2.0])
tx(s, 0.65, 5.15, 6.3, 1.5,
   '全库对照：无 74.58% / 未知 12.75% / 非营利 8.17% / 公司 4.51%。\n'
   '敏感性：剔除组织内部依赖后公司 2.70%；按包数不加权公司 16/319 = 5.0%。',
   12, DIM, spacing=1.4)
tx(s, 7.2, 1.7, 5.5, 3.4,
   '两条结论\n\n'
   '1. 越靠近地基，公司占比越低（1.4% < 4.51%）。\n'
   '   但这是入边流量口径；按包数是 5.0%，两个都要报。\n\n'
   '2. 「项目组织」绝大多数没人管账：\n'
   '   项目组织入边 490,016 条中，被 CNCF/LF 或 NumFOCUS\n'
   '   托管的只有 6,026 条（1.23%）。\n\n'
   '口径提醒：三列模型（法人类型 × 组织形态 × 财政赞助）\n'
   '三个维度正交、不可相加。',
   13, INK, spacing=1.4)
note(s, '配图：图集/图4-底基由谁供养.png ｜ 对应报告 §5.4')

# ───────────────────────── 7 Q2 ─────────────────────────
s = prs.slides.add_slide(BLANK)
head(s, '06  Q2', '公司的影响力主要不在公司自己的账号上')
tx(s, 0.65, 1.65, 12.0, 0.9,
   '有公司参与度的包 8,175 个（公司域名提交占比 > 0；中位 corp_share 仅 5.6%）。',
   13, DIM)
table(s, 0.65, 2.55, 6.0, 1.5, [
    ['计数（账号级口径）', '包数'],
    ['有公司参与度', '8,175'],
    ['其中 有公司组织账号', '483'],
    ['其中 无公司组织账号', '7,692（94.1%）'],
], size=14, col_widths=[4.2, 1.8])
tx(s, 0.65, 4.35, 6.1, 2.2,
   '三种口径相差近 20 倍，必须写明定义：\n'
   '  A 公司组织账号触及的包：1.67%\n'
   '  B corp_share 加权：4.42%\n'
   '  C 员工自报雇主并集：32.64%',
   12, INK, spacing=1.4)
tx(s, 7.1, 2.55, 5.6, 3.8,
   '标签源敏感性（必须同时报）\n\n'
   '  账号级标签：483 / 8,175 → 94.1%\n'
   '  命名空间级标签：1,237 / 8,175 → 84.9%\n'
   '  至少命中一种：1,351 → 两者都无 83.5%\n\n'
   '按 corp_share 阈值复算：0.2 / 0.5 / 0.8 对应\n'
   '  93.7% / 93.2% / 95.4%\n\n'
   '结论只说到「账号级口径」为止：不把它解释成\n'
   '「隐瞒所有权」。',
   13, INK, spacing=1.4)
note(s, '配图：图集/图5-公司影响力.png ｜ 对应报告 §5.5')

# ───────────────────────── 8 Q3 ─────────────────────────
s = prs.slides.add_slide(BLANK)
head(s, '07  Q3', '钱与位置：不存在稳定对应')
table(s, 0.65, 1.65, 12.0, 1.9, [
    ['案例', 'Rust 生态入边', '占全库', '年收入', '结算'],
    ['OpenSSL', '1,397', '0.127%', '68.7 万美元', '支出 93.1 万 → 储备 51.7 万 → 28.9 万'],
    ['Blender', '4', '0.0004%', '571 万欧元', '收入 255 万（2023）→ 571 万（2025）'],
], size=12, col_widths=[1.8, 2.2, 1.6, 2.4, 4.0])
tx(s, 0.65, 3.8, 12.0, 1.5,
   """两个案例不在同一总体（一个是 Rust 的 C 库绑定，一个是 C++ 桌面应用），只作「不存在简单对应」的反例，
不能当作「严重脱钩」的定量证据。OpenSSL 的 228 千是储备变动，不是收入−支出（−244,782）。

三条结构性观察：① 位置重要 ≠ 钱多；② 资金来源结构与技术位置无关；③ 钱在收缩的一方，结构位置也在退。""",
   12, INK, spacing=1.4)
note(s, '对应报告 §5.6')

# ───────────────────────── 8b Q4（双源对照）─────────────────────────
s = prs.slides.add_slide(BLANK)
head(s, '08  Q4（双源对照）', '两个生态的头部结构一样吗？')
pic(s, '图6-两生态对照.png', 0.45, 1.75, 8.2, 3.55)
tx(s, 8.85, 1.7, 4.0, 4.9,
   """数字对照

被依赖包：98,585 vs 66,315
入边合计：2,090,221 vs 1,101,475
Gini：0.924 vs 0.902
top1：4.38% vs 4.82%
top100：49.97% vs 54.33%
top1000：77.50% vs 77.34%

结论：头部集中是两个生态的共性，
不是 cargo 特有；差别只在 top1–top100。

口径：两生态没有公共实体键，
这是同法复现（外部效度），
不是实体融合。""",
   12, INK, spacing=1.25)
note(s, '早期「cargo 尖塔 vs PyPI 高原、单点差 2.5 倍」是分母不一致造成的伪差距，已作废 ｜ 对应报告 §5.7')

# ───────────────────────── 图集 ─────────────────────────
gallery('图集 1/4  时间', '集中度在升，底基在稀释', [
    ('图1-依赖集中度.png', '90% 的依赖边集中在多少比例的包里：40.5%（2015-01）→ 4.8%（2025-12）'),
    ('图2-底基扩张稀释.png', '底基包 5 → 319 个；占生态 1.23% → 0.18%——绝对扩张，相对稀释'),
], boxh=3.05, capy=5.0)

gallery('图集 2/4  网络', '谁在支撑别人的运行时？', [
    ('图3-谁在支撑运行时.png', '入度 top-24：语言原语、通用工具、运行时与应用框架混在同一层'),
    ('图8-领域分块-76块.png', '探索性聚类（早期 405 底基口径）：76 个领域块（Q=0.79）；因跨月不稳定未进入结论（§5.3）'),
], boxh=4.65, capy=6.45)

gallery('图集 3/4  跨源', '钱与影响力：底基由谁供养', [
    ('图4-底基由谁供养.png', '底基入边 77.9% 无法人；公司 1.4%（按包数不加权 16/319 = 5.0%）'),
    ('图5-公司影响力.png', '8,175 个公司参与包中 94.1% 没有公司组织账号（账号级；命名空间级 84.9%）'),
], boxh=3.05, capy=5.0)

gallery('图集 4/4  时间 × 网络', '一个月里，依赖图变了多少？', [
    ('图9-快照增量.png', '示例（2016-11→2016-12，1,583 节点子图）：绿色=新增节点，黄色=换层；正式序列为 132 个月度快照'),
], boxh=4.95, capy=6.75)

# ───────────────────────── 9 局限 / AI / 复现 ─────────────────────────
s = prs.slides.add_slide(BLANK)
head(s, '09  可靠性', '已知局限、AI 使用与复现入口')
tx(s, 0.6, 1.65, 4.0, 4.8,
   '局限（主动声明）\n\n'
   '· 幸存者偏差：越早的快照越偏向活到 2026 的包\n'
   '· req 版本约束未解析，残余伪边\n'
   '· 账号级实体解析仅 47.1%\n'
   '· 人工标签 293 条，覆盖 40.4% 入边\n'
   '· build 依赖层完全缺失（cc 不在图内）\n'
   '· 2026 年数据不可用，窗口截至 2025-12',
   11, INK, spacing=1.35)
tx(s, 4.7, 1.65, 4.3, 4.8,
   'AI 使用（完整记录见 AI_USAGE.md）\n\n'
   '· AI 约写 80% 代码，人做选题、口径与判断\n'
   '· 5 个实质错误全部由「回原始数据核对」发现：\n'
   '  optional 字符串布尔化 / 子图索引 / 集合构造 /\n'
   '  数组截断 / CDF 与 CCDF 写反\n'
   '· 最危险的不是报错，是「跑通且数字漂亮」\n'
   '· 每个头条数字都有一次不依赖 AI 的独立复算',
   11, INK, spacing=1.35)
tx(s, 9.1, 1.65, 3.7, 4.8,
   '复现入口\n\n'
   '作业/README.md\n'
   '  一键顺序 4 条命令\n\n'
   '作业/整合/*.py\n'
   '  融合表、三列模型、Q1、Q2\n\n'
   '作业/可视化/作图.py\n'
   '  → 可视化.html\n\n'
   '依赖图/00-数据溯源总表.md\n'
   '  A/B/C/D 来源分级',
   11, INK, spacing=1.35)
note(s, '数字口径与文件对应关系见 README §3.3 与 报告 §10')

prs.save(OUT)
print(f'已写 {OUT}  ({OUT.stat().st_size/1024:.0f} KB)，共 {len(prs.slides._sldIdLst)} 页')
