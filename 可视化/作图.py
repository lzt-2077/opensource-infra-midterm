# -*- coding: utf-8 -*-
"""
生成 5 张核心可视化（自包含 HTML + 内联 SVG，无外部依赖）

每张图满足作业要求：问题式标题 / 数据范围 / 单位 / 来源标注 / 不截断坐标
用法： python 作业/可视化/作图.py
"""
import sys
import numpy as np, pandas as pd
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

R = Path(__file__).resolve().parent.parent.parent
D = R / '依赖图'
O = R / '作业'
OUT = O / '可视化.html'

FONT = "'Microsoft YaHei','Segoe UI',sans-serif"
C = dict(bg='#ffffff', ink='#111827', dim='#6b7280', grid='#e5e7eb',
         blue='#2563eb', green='#059669', amber='#d97706', red='#dc2626',
         purple='#7c3aed', slate='#475569')
LAYER_COLOR = {'A 语言原语': '#2563eb', 'B 通用工具/格式': '#0891b2', 'C 运行时/平台绑定': '#059669',
               'D 应用框架': '#d97706', 'E 领域族(厂商/链/游戏)': '#dc2626',
               'F 已废弃/半废弃': '#6b7280', 'G 未归类': '#7c3aed'}


def svg_open(w, h, title):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="{FONT}" role="img" aria-label="{title}">'
            f'<rect width="{w}" height="{h}" fill="{C["bg"]}"/>')


def axis(px, py, w, h, ymin, ymax, ylab, ytick=5, xlab=''):
    s = []
    for i in range(ytick + 1):
        v = ymin + (ymax - ymin) * i / ytick
        y = py + h - h * i / ytick
        s.append(f'<line x1="{px}" y1="{y:.1f}" x2="{px+w}" y2="{y:.1f}" stroke="{C["grid"]}"/>')
        s.append(f'<text x="{px-8}" y="{y+4:.1f}" font-size="11" fill="{C["dim"]}" '
                 f'text-anchor="end">{v:g}</text>')
    s.append(f'<line x1="{px}" y1="{py+h}" x2="{px+w}" y2="{py+h}" stroke="{C["slate"]}"/>')
    s.append(f'<line x1="{px}" y1="{py}" x2="{px}" y2="{py+h}" stroke="{C["slate"]}"/>')
    s.append(f'<text x="{px-46}" y="{py-12}" font-size="11" fill="{C["dim"]}">{ylab}</text>')
    if xlab:
        s.append(f'<text x="{px+w/2}" y="{py+h+30}" font-size="11" fill="{C["dim"]}" '
                 f'text-anchor="middle">{xlab}</text>')
    return ''.join(s)


# ══════════════════════ 图 1：N90 集中度 ══════════════════════
d70 = pd.read_csv(D / '年代图/入驻/76-N90-主图.csv', encoding='utf-8-sig', dtype={'月': str})
d70 = d70.dropna(subset=['N90占比%']).reset_index(drop=True)
W, H, px, py, pw, ph = 980, 380, 70, 52, 850, 250
ymax = 45
xs = px + pw * np.arange(len(d70)) / (len(d70) - 1)
ys = (py + ph - ph * d70['N90占比%'].to_numpy() / ymax)
pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in zip(xs, ys))
g1 = [svg_open(W, H, 'N90'), axis(px, py, pw, ph, 0, ymax, '% 的包', 5,
       '月份（2015-01 → 2025-12，共 %d 个月）' % len(d70))]
g1.append(f'<polyline points="{pts}" fill="none" stroke="{C["blue"]}" stroke-width="2.2"/>')
for i, lab in [(0, '2015-01'), (len(d70) - 1, '2025-12')]:
    g1.append(f'<circle cx="{xs[i]:.1f}" cy="{ys[i]:.1f}" r="4" fill="{C["blue"]}"/>')
    dy = -12 if i else 18
    g1.append(f'<text x="{xs[i]:.1f}" y="{ys[i]+dy:.1f}" font-size="12" fill="{C["ink"]}" '
              f'text-anchor="{"start" if i==0 else "end"}">{lab}：{d70["N90占比%"][i]:.1f}%</text>')
g1.append(f'</svg>')
CH1 = ''.join(g1)

# ══════════════════════ 图 2：底基扩张 vs 稀释 ══════════════════════
d75 = pd.read_csv(D / '年代图/入驻/75-底基序列-主图.csv', encoding='utf-8-sig', dtype={'月': str})
d75 = d75[d75['底基'] > 0].reset_index(drop=True)
d75['占比%'] = 100 * d75['底基'] / d75['N有边']
W, H, px, py, pw, ph = 980, 400, 78, 52, 700, 260
xs = px + pw * np.arange(len(d75)) / (len(d75) - 1)
yA = py + ph - ph * d75['底基'].to_numpy() / 400
yB = py + ph - ph * d75['占比%'].to_numpy() / 1.6
g2 = [svg_open(W, H, '底基双轴'),
      axis(px, py, pw, ph, 0, 400, '底基包数（个）', 4,
           '月份（2015-01 → 2025-12，共 %d 个月）' % len(d75))]
for i in range(5):
    v = 1.6 * i / 4
    y = py + ph - ph * i / 4
    g2.append(f'<text x="{px+pw+10}" y="{y+4:.1f}" font-size="11" fill="{C["red"]}">{v:.1f}</text>')
g2.append(f'<text x="{px+pw+52}" y="{py-12}" font-size="11" fill="{C["red"]}">底基占比（%）</text>')
g2.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.2"/>' %
          (' '.join(f'{x:.1f},{y:.1f}' for x, y in zip(xs, yA)), C['blue']))
g2.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.2" stroke-dasharray="5,4"/>' %
          (' '.join(f'{x:.1f},{y:.1f}' for x, y in zip(xs, yB)), C['red']))
g2.append(f'<text x="{xs[-1]-4:.1f}" y="{yA[-1]-10:.1f}" font-size="12" fill="{C["blue"]}" '
          f'text-anchor="end">底基包数 {int(d75["底基"].iloc[-1])} 个（实线）</text>')
g2.append(f'<text x="{xs[-1]-4:.1f}" y="{yB[-1]+18:.1f}" font-size="12" fill="{C["red"]}" '
          f'text-anchor="end">占生态比例 {d75["占比%"].iloc[-1]:.2f}%（虚线）</text>')
g2.append(f'<text x="{px+6}" y="{yA[0]-8:.1f}" font-size="12" fill="{C["blue"]}">起点 {int(d75["底基"].iloc[0])} 个</text>')
g2.append(f'<text x="{px+6}" y="{yB[0]+16:.1f}" font-size="12" fill="{C["red"]}">起点 {d75["占比%"].iloc[0]:.2f}%</text>')
g2.append('</svg>')
CH2 = ''.join(g2)

# ══════════════════════ 图 3：谁在支撑别人的运行时 ══════════════════════
d74 = pd.read_csv(D / '年代图/入驻/74-底基-技术分层.csv', encoding='utf-8-sig')
top = d74.sort_values('入度', ascending=False).head(24).reset_index(drop=True)
W = 980
rowh, top0 = 22, 64
ph = rowh * len(top)
H = top0 + ph + 120
mx = top['入度'].max()
bw = 620
g3 = [svg_open(W, H, '底基构成'),
      f'<text x="20" y="26" font-size="12" fill="{C["dim"]}">横轴：入度（被多少个包直接依赖，单位：个）</text>']
for i, r in top.iterrows():
    y = top0 + i * rowh
    w = bw * r['入度'] / mx
    col = LAYER_COLOR.get(r['技术层'], C['slate'])
    g3.append(f'<text x="196" y="{y+15}" font-size="12" fill="{C["ink"]}" text-anchor="end">{r["包"]}</text>')
    g3.append(f'<rect x="204" y="{y+3}" width="{w:.1f}" height="{rowh-8}" fill="{col}" opacity="0.85"/>')
    g3.append(f'<text x="{204+w+6:.1f}" y="{y+15}" font-size="11" fill="{C["dim"]}">{int(r["入度"]):,}</text>')
# 图例
ly = top0 + ph + 24
g3.append(f'<text x="204" y="{ly}" font-size="11" fill="{C["dim"]}">技术层：</text>')
lx = 270
for k, col in LAYER_COLOR.items():
    g3.append(f'<rect x="{lx}" y="{ly-9}" width="10" height="10" fill="{col}"/>')
    g3.append(f'<text x="{lx+14}" y="{ly}" font-size="11" fill="{C["ink"]}">{k}</text>')
    lx += 18 + len(k) * 10.5
g3.append('</svg>')
CH3 = ''.join(g3)

# ══════════════════════ 图 4：底基由谁供养（仅权威标注 + 未标注单列）══════════════════════
q1 = pd.read_csv(O / '整合/Q1-底基三列.csv', encoding='utf-8-sig')
q1 = q1[q1['维度'] == '法人类型']
COL4 = {'无': C['slate'], '非营利': C['green'], '公司': C['red'], '未知': '#e5e7eb'}
W, H = 1000, 300
bw4, x0 = 820, 120
tot = q1['底基入度'].sum()
g4 = [svg_open(W, H, '底基供养')]
y = 64
x = x0
g4.append(f'<text x="{x0-14}" y="{y+23}" font-size="13" fill="{C["ink"]}" text-anchor="end">'
          f'底基 319 包</text>')
for _, r in q1.sort_values('底基入度', ascending=False).iterrows():
    v = float(r['底基入度'])
    if v <= 0: continue
    w = bw4 * v / tot
    key = r['取值']
    g4.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="36" '
              f'fill="{COL4.get(key, C["slate"])}" opacity="0.92"/>')
    if w > 52:
        g4.append(f'<text x="{x+w/2:.1f}" y="{y+23}" font-size="12" '
                  f'fill="{"#fff" if key!="未知" else C["ink"]}" text-anchor="middle">'
                  f'{100*v/tot:.1f}%</text>')
    x += w
g4.append(f'<text x="{x0}" y="{y+58}" font-size="12" fill="{C["dim"]}">'
          f'三列模型（法人类型一列）：无 77.9%　非营利 10.4%　公司 1.4%　未知 10.3%</text>')
g4.append(f'<text x="{x0}" y="{y+96}" font-size="13" fill="{C["ink"]}">'
          f'底基入度合计 {int(tot):,}；公司仅占 1.4%，低于全库的 4.51%（剔除组织内部依赖后 2.70%）</text>')
g4.append(f'<text x="{x0}" y="{y+130}" font-size="12" fill="{C["dim"]}">'
          f'法人类型来自命名空间级级联标签（溯源总表 B 级）；人工核验 293 条，覆盖 40.4% 入边（底基 50.7%）</text>')
g4.append(f'<text x="{x0}" y="{y+156}" font-size="12" fill="{C["red"]}">'
          f'底基侧未标注 10.3%，单列为「未知」，不推测；不要与全库口径混用</text>')
g4.append('</svg>')
CH4 = ''.join(g4)

# ══════════════════════ 图 5：公司影响力来自哪里 ══════════════════════
W, H = 980, 340
BARW = 560
g5 = [svg_open(W, H, '公司影响力')]
g5.append(f'<text x="30" y="34" font-size="12" fill="{C["dim"]}">'
          f'(a) 有公司参与（仓库内至少 1 次公司域名提交）的 8,175 个包中，有多少没有任何公司组织账号</text>')
x0, top_w, y = 40, 900, 58
n_own, n_emp = 483, 7692
w1 = top_w * n_own / (n_own + n_emp)
g5.append(f'<rect x="{x0}" y="{y}" width="{w1:.1f}" height="36" fill="{C["red"]}" opacity="0.85"/>')
g5.append(f'<rect x="{x0+w1:.1f}" y="{y}" width="{top_w-w1:.1f}" height="36" fill="{C["blue"]}" opacity="0.85"/>')
g5.append(f'<text x="{x0+top_w+12}" y="{y+23}" font-size="12" fill="{C["ink"]}">'
          f'有公司账号 {n_own} 个（{100*n_own/(n_own+n_emp):.1f}%）</text>')
g5.append(f'<text x="{x0+w1+14:.1f}" y="{y+23}" font-size="12" fill="#fff">'
          f'无公司账号 {n_emp:,} 个（{100*n_emp/(n_own+n_emp):.1f}%）</text>')
g5.append(f'<text x="{x0}" y="{y+60}" font-size="12" fill="{C["ink"]}">'
          f'→ 94.1% 的公司参与包没有公司组织账号，其余 7,692 个包只有员工的个人账号（账号级口径）。</text>')
g5.append(f'<text x="30" y="176" font-size="12" fill="{C["dim"]}">'
          f'(b) 三种口径下的"公司占全库入边"，横轴从 0 开始，不截断</text>')
cal = [('A 组织账号直接持有（包级排他，可复现）', 1.67, C['red']),
       ('B 公司参与度 corp_share 加权（可复现）', 4.42, C['amber']),
       ('C 员工自报雇主并集（口径最宽）', 32.64, C['slate'])]
mxv = 35
for i, (lab, v, col) in enumerate(cal):
    yy = 200 + i * 42
    g5.append(f'<text x="330" y="{yy+18}" font-size="12" fill="{C["ink"]}" text-anchor="end">{lab}</text>')
    g5.append(f'<rect x="342" y="{yy+4}" width="{BARW*v/mxv:.1f}" height="20" fill="{col}" opacity="0.85"/>')
    g5.append(f'<text x="{342+BARW*v/mxv+8:.1f}" y="{yy+19}" font-size="12" fill="{C["ink"]}">{v:.2f}%</text>')
for i in range(8):
    vv = mxv * i / 7
    xx = 342 + BARW * i / 7
    g5.append(f'<text x="{xx:.1f}" y="336" font-size="10" fill="{C["dim"]}" text-anchor="middle">{vv:.0f}%</text>')
g5.append('</svg>')
CH5 = ''.join(g5)

# ══════════════════════ 组装 ══════════════════════
CH = [
    ('图 1',
     '90% 的依赖集中在多少比例的包里？',
     '一条持续下行的曲线：2015 年需要 40.5% 的包才覆盖 90% 的依赖边，2025 年只需 4.8%。说明结构集中度在持续上升。',
     CH1, '数据范围 2015-01 → 2025-12（132 个月度快照）｜单位 %（占当期有依赖边的包数）｜来源 S1 crates.io dump，主图口径（kind=0 且 optional=false）｜文件 76-N90-主图.csv'),
    ('图 2',
     '基础设施层是在扩张，还是在稀释？',
     '底基包的绝对数量从 5 个增长到 319 个（实线），但它占生态的比例从 1.23% 降到 0.18%（虚线）。数量在涨，份额在跌。',
     CH2, '数据范围 2015-01 → 2025-12｜左轴：底基包数（个）｜右轴：底基占有依赖边包数的比例（%）｜门槛 θ(t)=366·(N(t)/N_2025-12)^0.5，主图口径｜文件 75-底基序列-主图.csv'),
    ('图 3',
     '谁在支撑别人的运行时？',
     '入度最高的 24 个包里，语言原语与通用工具占多数，但 clap、reqwest、hyper、axum 这类应用框架也在前列——底基层在技术上并不是同质的。',
     CH3, '数据范围 2025-12 时点｜单位 入度（被多少个包直接依赖，个）｜颜色 = 技术职能分层｜来源 S1 依赖图 + 包分类元数据｜文件 74-底基-技术分层.csv'),
    ('图 4',
     '底基包由谁供养？',
     '319 个底基包里，入边加权后：无 77.9%、非营利 10.4%、未知 10.3%、公司 1.4%（按包数不加权则公司 16 个 / 5.0%）。',
     CH4, '数据范围 2025-12 时点，319 个底基包（316 可匹配，覆盖 99.6% 入度）｜单位 占底基入度 %｜三列模型·法人类型一列｜口径 kind=0 且 optional=false｜文件 Q1-底基三列.csv，脚本 三列模型-重建.py'),
    ('图 5',
     '公司的影响力来自自有账号，还是员工？',
     '(a) 有公司参与的 8,175 个包里，94.1% 没有任何公司组织账号；(b) 同一件事的三种口径相差近 20 倍，口径必须写明。',
     CH5, '数据范围 2025-12 时点｜单位 个（a）与 %（b）｜口径 A/B 可复现于本仓库，C 依赖提交邮箱域名｜来源 S1 × S3｜文件 Q2-员工代持计数证据.csv、Q2-三种口径对照.csv'),
]

html = [f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>核心可视化 · 开源生态基础设施层</title>
<style>
 body{{margin:0;padding:36px 24px;background:#f8fafc;color:{C['ink']};font-family:{FONT};line-height:1.6}}
 .wrap{{max-width:1040px;margin:0 auto}}
 h1{{font-size:22px;margin:0 0 6px}} .sub{{color:{C['dim']};font-size:13px;margin-bottom:28px}}
 .card{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:20px 22px 14px;margin-bottom:24px}}
 .q{{font-size:16px;font-weight:600;margin:0 0 4px}} .tag{{font-size:11px;color:{C['blue']};margin-bottom:8px}}
 .lead{{font-size:13px;color:#374151;margin:6px 0 10px}}
 .src{{font-size:11px;color:{C['dim']};border-top:1px dashed #e2e8f0;padding-top:8px;margin-top:6px}}
</style></head><body><div class="wrap">
<h1>核心可视化 · 五张</h1>
<div class="sub">开源软件生态中的"基础设施层"及其供养结构 ｜ 所有图横轴均从 0 起，未截断 ｜ 2026-11-16</div>
"""]
for tag, q, lead, chart, src in CH:
    html.append(f'<div class="card"><div class="tag">{tag}</div><div class="q">{q}</div>'
                f'<div class="lead">{lead}</div>{chart}<div class="src">{src}</div></div>')
html.append('</div></body></html>')
OUT.write_text(''.join(html), encoding='utf-8')
print(f'已写 {OUT}  ({OUT.stat().st_size/1024:.0f} KB)')
print(f'图1 点数 {len(d70)}；图2 点数 {len(d75)}；图3 条目 {len(top)}')
