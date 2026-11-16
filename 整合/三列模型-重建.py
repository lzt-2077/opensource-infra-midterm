# -*- coding: utf-8 -*-
"""
三列模型重建器（cargo）

背景
----
`年代图/入驻/_三列-cargo-填赞助.csv` 曾经没有生成脚本。本文档把当时的规则从会话记录里
还原成可运行代码，并同时给出两种加权口径：

  A. 旧口径（validation）：用 `命名空间-主体-订正版.csv` 里的 `入` 列
     （= 2026-11-09 全图，含 optional，总 2,896,485）
     期望复现：无×项目组织 47.00%、无×个人 29.94%、未知 12.14%、非营利×基金会自持 6.26%、公司 3.99%

  B. 主图口径：用 2025-12 主图（kind=0 且 optional=false）重算的 ns 级入度
     （总约 1,089,581），与报告 §5.1/§5.2 一致

数据链
------
  命名空间-主体-订正版.csv   ns, 入, 入外, axis2, 新判, 类      ← 32/34/35 号订正后的分类
  命名空间-新分类.csv        dep_ns, ..., kind                  ← GitHub 账号类型 user/organization
  %TEMP%/nf-full.json        NumFOCUS 项目全文（63 个）
  %TEMP%/cncf-projects.json  CNCF landscape 项目（263 个）
  versions-id.csv + _dep-normal-opt.npz + 命名空间映射-2026.csv  ← 主图 ns 级入度

规则（与会话记录一致）
   类=法人        → 公司 / 公司部门 / 自持
   类=非营利      → 非营利 / (项目组织|基金会自持|基金会自持·未拆) / (CNCF·LF|自持|未判定)
   类=无法人      → 无 / (项目组织 if kind=organization; 个人 if kind=user; 组织·个人(未拆)) / 无
   类=未知        → 未知 / 不明 / 未判定

用法： python 作业/整合/三列模型-重建.py
"""
import sys, json, re, os
from pathlib import Path
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

R = Path(__file__).resolve().parent.parent.parent
D = str(R / '依赖图') + '/'
O = str(R / '作业/整合') + '/'
T = os.environ.get('TEMP', r'C:\Users\13191\AppData\Local\Temp')

SELF_NP = {'rust-lang', 'apache', 'mozilla', 'nlnetlabs', 'unicode-org',
           'bitcoindevkit', 'zcashfoundation'}
HOSTED_NP = {'open-telemetry', 'wasmcloud', 'wasmedge', 'sigstore', 'delta-io',
             'opensearch-project', 'containerd', 'envoyproxy'}

# ── 1. 上游：分类结果 + 账号类型 ──
sub = pd.read_csv(D + '年代图/入驻/命名空间-主体-订正版.csv', encoding='utf-8-sig', low_memory=False)
knd = pd.read_csv(D + '年代图/入驻/命名空间-新分类.csv', encoding='utf-8-sig', low_memory=False)
KIND = dict(zip(knd['dep_ns'], knd['kind']))
print(f"[1] 主体订正版 {len(sub):,} 行；新分类 {len(knd):,} 行")
print("    类 分布：" + sub['类'].value_counts().to_dict().__str__())
print("    kind 分布：" + knd['kind'].value_counts(dropna=False).to_dict().__str__())


def rows(ns, c):
    if c == '法人':
        return '公司', '公司部门', '自持'
    if c == '非营利':
        if ns in HOSTED_NP:
            return '非营利', '项目组织', 'CNCF/LF'
        if ns in SELF_NP:
            return '非营利', '基金会自持', '自持'
        return '非营利', '基金会自持·未拆', '未判定'
    if c == '无法人':
        k = KIND.get(ns)
        form = '项目组织' if k == 'organization' else '个人' if k == 'user' else '组织·个人(未拆)'
        return '无', form, '无'
    return '未知', '不明', '未判定'


sub[['法人类型', '组织形态', '财政赞助']] = sub.apply(
    lambda r: pd.Series(rows(r['ns'], r['类'])), axis=1)

# ── 2. 财政赞助补判：NumFOCUS / CNCF ──
NF, SL = set(), set()
p = Path(T) / 'nf-full.json'
if p.exists():
    for r in json.load(open(p, encoding='utf-8')):
        SL.add(r.get('slug', '').lower())
        for o in re.findall(r'github\.com/([A-Za-z0-9_.-]+)', json.dumps(r, ensure_ascii=False)):
            NF.add(o.lower())
NF |= {'pandas-dev', 'numpy', 'scipy', 'matplotlib', 'scikit-learn', 'networkx', 'sympy',
       'xarray', 'dask', 'bokeh', 'holoviz', 'zarr', 'statsmodels', 'astropy', 'pymc',
       'julia', 'conda', 'conda-forge', 'pybind11'}
p = Path(T) / 'cncf-projects.json'
CN = set()
if p.exists():
    cc = json.load(open(p, encoding='utf-8'))
    CN = {x['repo'].split('/')[0].lower() for a in cc.values() for x in a if x.get('repo')}
print(f"[2] NumFOCUS owner/slug {len(NF)} 个；CNCF owner {len(CN)} 个；交集 {len(NF & CN)}")

low = sub['ns'].astype(str).str.lower()
sub['赞助2'] = sub['财政赞助']
sub.loc[low.isin(NF), '赞助2'] = 'NumFOCUS'
sub.loc[low.isin(CN - NF), '赞助2'] = 'CNCF/LF'


def report(df, icol, label, expect=None):
    tot = df[icol].sum()
    pv = df.pivot_table(index=['法人类型', '组织形态'], columns='赞助2',
                        values=icol, aggfunc='sum', fill_value=0)
    pv['合计'] = pv.sum(axis=1)
    pv['占%'] = (100 * pv['合计'] / tot).round(2)
    pv = pv.sort_values('合计', ascending=False)
    print(f"\n{'='*70}\n{label}  总入边 {int(tot):,}\n{'='*70}")
    print(pv.to_string())
    if expect:
        print("\n校验（对阵会话记录）：")
        ok = True
        for (lt, fm), v in expect.items():
            got = pv.loc[(lt, fm), '占%'] if (lt, fm) in pv.index else None
            flag = '✓' if got is not None and abs(got - v) < 0.05 else '✗'
            if flag == '✗':
                ok = False
            print(f"   {lt} × {fm:<12} 期望 {v:>6.2f}%  实得 {got if got is None else f'{got:.2f}%':>7}  {flag}")
        print("   → 完全复现" if ok else "   → 存在偏差，见上")
    return pv


# ── 3. A 口径：旧「入」列（validation）──
report(sub, '入', 'A. 旧口径（2026-11-09 全图含 optional）', expect={
    ('无', '项目组织'): 47.00, ('无', '个人'): 29.94, ('未知', '不明'): 12.14,
    ('非营利', '基金会自持'): 6.26, ('公司', '公司部门'): 3.99,
})

# ── 4. B 口径：主图 ns 级入度 ──
v = pd.read_csv(D + 'versions-id.csv', encoding='utf-8-sig',
                dtype={'id': 'int64', 'crate_id': 'int64'},
                usecols=['id', 'crate_id', 'created_at'])
v['ts'] = pd.to_datetime(v['created_at'], utc=True, format='mixed', errors='coerce')
v = v.dropna(subset=['ts'])
v = v[v.ts <= pd.Timestamp('2025-12-14T02:00:00Z')]
last = v.sort_values('ts').groupby('crate_id', as_index=False).tail(1)
CID = dict(zip(last.id.astype('int64').values, last.crate_id.astype('int64').values))
z = np.load(D + '年代图/入驻/_dep-normal-opt.npz')
EV, ED, EO = z['version_id'], z['dep_crate_id'], z['is_opt'].astype(bool)
mx = int(max(EV.max(), last.id.max())) + 2
chosen = np.zeros(mx, bool)
chosen[last.id.to_numpy()] = True
e = chosen[EV] & ~EO
dep = ED[e]
root = np.array([CID.get(int(x), -1) for x in EV[e]])
dep = dep[(root > 0) & (dep != root)]
mp = pd.read_csv(D + '年代图/命名空间映射-2026.csv', encoding='utf-8-sig',
                 usecols=['crate_id', 'namespace'])
c2ns = {int(c): str(x) for c, x in zip(mp.crate_id, mp.namespace) if pd.notna(x)}
nss = np.array([c2ns.get(int(x), '') for x in dep], dtype=object)
ind = pd.Series(nss[nss != '']).value_counts()

sub2 = sub.drop(columns=['入']).merge(
    pd.DataFrame({'ns': ind.index, '入': ind.values}), on='ns', how='inner')
print(f"\n[3] 主图口径能匹配的 ns：{len(sub2):,} / {len(sub):,}，"
      f"覆盖主图入度 {100*sub2['入'].sum()/ind.sum():.1f}%")
pvB = report(sub2, '入', 'B. 主图口径（2025-12，kind=0 且 optional=false）')

# ── 5. 落盘 ──
out = sub[['ns', '入', '类', '法人类型', '组织形态', '财政赞助', '赞助2']]
out.to_csv(O + '三列模型-旧口径.csv', index=False, encoding='utf-8-sig')
sub2[['ns', '入', '类', '法人类型', '组织形态', '财政赞助', '赞助2']].to_csv(
    O + '三列模型-主图口径.csv', index=False, encoding='utf-8-sig')
pvB.reset_index().to_csv(O + '三列模型-主图口径-透视.csv', index=False, encoding='utf-8-sig')
print(f"\n[4] 已写 三列模型-旧口径.csv / 三列模型-主图口径.csv / 三列模型-主图口径-透视.csv")
