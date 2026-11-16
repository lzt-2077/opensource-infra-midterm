# -*- coding: utf-8 -*-
"""
Q1 · 基础设施层由谁供养 —— 可复现脚本

设计原则
--------
1. **只使用有出处的标签**。标签唯一来源是 `主体字典-人工.csv`（basis 列标注依据），
   不再使用 `_三列-cargo-填赞助.csv`（该文件无生成脚本，且与人工字典在交集上仅 84% 一致）。
2. **口径与报告其余部分一致**：2025-12 时点、主图（kind=0 且 optional=false）、
   每 crate 取该时点前最新版本、ns 级入度。
3. **未标注就是未标注**。不在人工字典里的 namespace 一律记 `未知`，不推测。

输入
   依赖图/versions-id.csv
   依赖图/年代图/入驻/_dep-normal-opt.npz      kind=0 全部边 + optional 标记
   依赖图/年代图/命名空间映射-2026.csv           crate_id → namespace
   依赖图/主体字典-人工.csv                     owner → type（唯一标签源）

输出
   作业/整合/Q1-三列模型-法人类型.csv
   作业/整合/Q1-口径核对.csv                   旧三列表 vs 人工字典 的一致性
   作业/整合/Q1-底基构成.csv                    319 个底基包层面的分布

用法： python 作业/整合/Q1-三列模型.py
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

R = Path(__file__).resolve().parent.parent.parent
D = str(R / '依赖图') + '/'
O = str(R / '作业/整合') + '/'
ANCHOR = pd.Timestamp('2025-12-14T02:00:00Z')

# ── 1. 主图 ns 级入度 ──
v = pd.read_csv(D + 'versions-id.csv', encoding='utf-8-sig',
                dtype={'id': 'int64', 'crate_id': 'int64'},
                usecols=['id', 'crate_id', 'created_at'])
v['ts'] = pd.to_datetime(v['created_at'], utc=True, format='mixed', errors='coerce')
v = v.dropna(subset=['ts'])
v = v[v.ts <= ANCHOR]
last = v.sort_values('ts').groupby('crate_id', as_index=False).tail(1)
CID = dict(zip(last.id.astype('int64').values, last.crate_id.astype('int64').values))

z = np.load(D + '年代图/入驻/_dep-normal-opt.npz')
EV, ED, EO = z['version_id'], z['dep_crate_id'], z['is_opt'].astype(bool)
mx = int(max(EV.max(), last.id.max())) + 2
chosen = np.zeros(mx, bool)
chosen[last.id.to_numpy()] = True
e = chosen[EV] & ~EO                      # 只用必需依赖
dep = ED[e]
root = np.array([CID.get(int(x), -1) for x in EV[e]])
dep = dep[(root > 0) & (dep != root)]

mp = pd.read_csv(D + '年代图/命名空间映射-2026.csv', encoding='utf-8-sig',
                 usecols=['crate_id', 'namespace', 'name'])
c2ns = {int(c): str(x) for c, x in zip(mp.crate_id, mp.namespace) if pd.notna(x)}
c2nm = {int(c): str(x).lower() for c, x in zip(mp.crate_id, mp.name) if pd.notna(x)}
ns_of = np.array([c2ns.get(int(x), '') for x in dep], dtype=object)
ind = pd.Series(ns_of[ns_of != '']).value_counts()
TOT = int(ind.sum())
print(f"[1] 主图 {ANCHOR.date()}：被依赖包 {len(np.unique(dep)):,} 个；"
      f"其中有 namespace 的 {len(ind):,} 个，入度合计 {TOT:,}")

# ── 2. 权威标签：人工字典 ──
dic = pd.read_csv(D + '主体字典-人工.csv', encoding='utf-8-sig')
MAP = {'无法人组织': '无', '个人': '无', '公司': '公司', '非营利': '非营利'}
dic['法人类型'] = dic['type'].map(lambda x: MAP.get(x, '未知'))
lab = dict(zip(dic['owner'], dic['法人类型']))

df = pd.DataFrame({'ns': ind.index, '入度': ind.values})
df['法人类型'] = df['ns'].map(lab).fillna('未知')
cov = int(df.loc[df['法人类型'] != '未知', '入度'].sum())
print(f"[2] 人工字典 {len(dic)} 个 owner；命中主图 ns "
      f"{int((df['法人类型'] != '未知').sum()):,} 个，覆盖入度 {cov:,} ({100*cov/TOT:.1f}%)")

# ── 3. 分布 ──
mark = df[df['法人类型'] != '未知']
g = mark.groupby('法人类型').agg(namespace数=('ns', 'nunique'), 入度=('入度', 'sum'))
g['占已标注%'] = (100 * g['入度'] / g['入度'].sum()).round(1)
g['占全库%'] = (100 * g['入度'] / TOT).round(2)
g = g.sort_values('入度', ascending=False)
g.loc['（未标注）'] = [int((df['法人类型'] == '未知').sum()),
                      int(df.loc[df['法人类型'] == '未知', '入度'].sum()),
                      None, round(100 * (TOT - cov) / TOT, 2)]
g.to_csv(O + 'Q1-三列模型-法人类型.csv', encoding='utf-8-sig')
print("\n[3] 法人类型分布（主图口径，仅权威标注）")
print(g.to_string())

# ── 4. 口径核对：旧三列表 vs 人工字典 ──
old = pd.read_csv(D + '年代图/入驻/_三列-cargo-填赞助.csv', encoding='utf-8-sig',
                  usecols=['ns', '入', '法人类型'], low_memory=False)
hit = df.merge(old, on='ns', how='inner', suffixes=('_字典', '_旧表'))
sub = hit[hit['法人类型_字典'] != '未知']
agree = (sub['法人类型_字典'] == sub['法人类型_旧表']).sum()
chk = pd.DataFrame([
    {'项目': '旧三列表 入 合计', '值': f"{int(old['入'].sum()):,}", '说明': '11-09 全图含 optional，与主图口径不同'},
    {'项目': '主图 入 合计', '值': f"{TOT:,}", '说明': '2025-12 去 optional'},
    {'项目': '两者交集 ns', '值': f"{len(hit):,}", '说明': ''},
    {'项目': '其中字典有标注', '值': f"{len(sub):,}", '说明': ''},
    {'项目': '标注一致', '值': f"{int(agree):,} ({100*agree/max(len(sub),1):.0f}%)", '说明': '旧表与人工字典的冲突率'},
])
chk.to_csv(O + 'Q1-口径核对.csv', index=False, encoding='utf-8-sig')
print("\n[4] 口径核对")
print(chk.to_string(index=False))

# ── 5. 底基 319 包层面 ──
try:
    t = pd.read_parquet(O + '包级融合表-crates.parquet')
    base = t[t['是否底基2025']]
    nm2 = dict(zip(t['包'], t['命名空间']))
    bb = pd.DataFrame({'包': base['包'], '入度': base['入度_主图'],
                       'ns': base['包'].map(nm2)})
    bb['法人类型'] = bb['ns'].map(lab).fillna('未知')
    gb = bb.groupby('法人类型')['入度'].sum().sort_values(ascending=False)
    out = pd.DataFrame({'法人类型': gb.index, '底基入度': gb.values})
    out['占已标注%'] = np.where(
        out['法人类型'] == '未知', None,
        (100 * out['底基入度'] / out.loc[out['法人类型'] != '未知', '底基入度'].sum()).round(1))
    out.to_csv(O + 'Q1-底基构成.csv', index=False, encoding='utf-8-sig')
    print(f"\n[5] 底基 319 包层面（标注覆盖 "
          f"{100*out.loc[out['法人类型'] != '未知','底基入度'].sum()/out['底基入度'].sum():.1f}% 的底基入度）")
    print(out.to_string(index=False))
except FileNotFoundError:
    print("\n[5] 跳过：包级融合表不存在，先运行 构建.py")
