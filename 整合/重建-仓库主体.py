# -*- coding: utf-8 -*-
"""
重建 `仓库-主体.csv` 的 corp_share（org 层公司域名提交占比）

背景
----
Q2 的 94.1% 依赖 `包-位置-主体-新刻度.csv` 的 `corp_share`，而该列最终来自 org 层的
`仓库-主体.csv`。这个 org 层脚本原本是会话里的 heredoc，仓库中没有文件（溯源总表 C 级）。
本脚本把当时的代码完整还原并可验证：重跑后与 `仓库-主体.csv` 的 corp_share 逐行核对。

定义
----
对每个 GitHub org：
    corp_share = (标记为「公司」域名的提交数) / (该 org 全部提交数)
    域名类型来自 `域名-实体字典.csv`；提交按域名统计自 `funder.jsonl`
    样本不足（总提交 < 50）时不判定主体类型，但 corp_share 仍照算

上游
----
    依赖图/funder.jsonl              repo, dom{域名: 提交数}
    依赖图/域名-实体字典.csv          domain, type
    依赖图/owners_meta.jsonl          login, kind, ...
    依赖图/包-形态-位置.csv           dep（参与统计的包集合）
    依赖图/2026-11-14-020024/data/crates.csv   name, repository
    形态-数存量.py                    FOUNDATION_ORGS / COS_ORGS（项目根）

用法： python 作业/整合/重建-仓库主体.py
"""
import sys, csv, json, re, collections
from pathlib import Path
import importlib.util
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

R = Path(__file__).resolve().parent.parent.parent
D = str(R / '依赖图') + '/'
O = str(R / '作业/整合') + '/'


def rd_dict(path, key, val):
    return {r[key].strip().lower(): r[val] for r in csv.DictReader(open(path, encoding='utf-8-sig'))}


spec = importlib.util.spec_from_file_location('cx', str(R / '形态-数存量.py'))
cx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cx)
F = {o.lower() for o in cx.FOUNDATION_ORGS}
C = {o.lower() for o in cx.COS_ORGS}
H = rd_dict(D + '主体字典-人工.csv', 'owner', 'type')
DOM = {k.lower(): v for k, v in rd_dict(D + '域名-实体字典.csv', 'domain', 'type').items()}
meta = {}
for line in open(D + 'owners_meta.jsonl', encoding='utf-8'):
    x = json.loads(line)
    if x.get('_ok'):
        meta[str(x.get('login', '')).lower()] = x


def dcls(d):
    return '免费' if d == '__free__' else DOM.get(d.lower(), '未在册')


# ── org → 公司域名提交占比 ──
cs = collections.defaultdict(lambda: [0, 0])
for line in open(D + 'funder.jsonl', encoding='utf-8'):
    r = json.loads(line)
    if not r.get('ok'):
        continue
    o = r['repo'].lower().split('/')[0]
    for dom, c in (r.get('dom') or {}).items():
        cs[o][1] += c
        if dcls(dom) == '公司':
            cs[o][0] += c
print(f"[1] funder.jsonl：{len(cs):,} 个 org 有域名提交记录")

# ── 包 → org ──
pos = {x['dep']: x['bin'] for x in csv.DictReader(open(D + '包-形态-位置.csv', encoding='utf-8-sig'))}
GH = re.compile(r'^https?://(?:www\.)?github\.com/([^/]+)/([^/?#]+)', re.I)
rows = []
for ch in pd.read_csv(D + '2026-11-14-020024/data/crates.csv',
                      usecols=['name', 'repository'], chunksize=200000, on_bad_lines='skip'):
    rows.append(ch[ch.name.isin(pos)])
d = pd.concat(rows).drop_duplicates('name')
d['r'] = d.repository.fillna('').str.strip()
m = d.r.str.extract(GH)
d['org'] = m[0].str.lower()
d = d[d.org.notna()].copy()
print(f"[2] 包 → org：{len(d):,} 个包有 GitHub org")

# ── axis1（发版账号数）──
acc = pd.read_csv(D + '包-账号.csv', encoding='utf-8-sig')
acc = acc[acc.crate.isin(set(d.name))]
uo = acc[acc.account_kind == 'user'].groupby('crate')['account'].agg(lambda s: {str(x).lower() for x in s})
to = acc[acc.account_kind == 'team'].groupby('crate')['account'].agg(lambda s: {str(x).lower() for x in s})
d['uo'] = d.name.map(lambda n: uo.get(n, set()))
d['to'] = d.name.map(lambda n: to.get(n, set()))
ou = collections.defaultdict(set)
ot = collections.defaultdict(set)
for o, a, b in zip(d.org, d.uo, d.to):
    ou[o] |= a
    ot[o] |= b

NAMEPAT = re.compile(r'foundation|consortium|association|institute|alliance|society|project', re.I)


def axis1(o):
    n = len(ou.get(o, ()))
    if n == 0:
        return ('未知', '仅团队发版' if ot.get(o) else '无记录', 0)
    return ('1人' if n == 1 else '少数' if n <= 5 else '集体', f'{n} 个发版账号', n)


def axis2(o):
    c, tot = cs.get(o, [0, 0])
    share = (c / tot) if tot else None
    listed = H.get(o) or ('非营利' if o in F else '公司' if o in C else None)
    if listed == '非营利':
        return '非营利锚定', '名录', share, tot
    if listed == '公司':
        return '法人锚定', '名录', share, tot
    if share is not None and tot >= 50:
        return ('法人锚定' if share >= 0.5 else '无法人'), f'行为(公司域名{">=" if share>=0.5 else "<"}0.5)', share, tot
    if o in meta and NAMEPAT.search(o):
        return '非营利锚定', '组织名特征', share, tot
    return '未知', '无证据', share, tot


recs = []
for o in sorted(set(d.org)):
    a1, b1, n = axis1(o)
    a2, b2, sh, tot = axis2(o)
    recs.append({'org': o, 'axis1_发版账号数': a1, 'axis1_依据': b1, 'n_user_owners': n,
                 'axis2_主体': a2, 'axis2_依据': b2,
                 'corp_share': round(sh, 4) if sh is not None else '',
                 'n_commits': tot, 'n_teams': len(ot.get(o, ())),
                 'kind': (meta.get(o) or {}).get('kind', ''),
                 'n_pkgs': int((d.org == o).sum())})
t = pd.DataFrame(recs)
t.to_csv(O + '仓库-主体-重建.csv', index=False, encoding='utf-8-sig')
print(f"[3] 重建 org 层 {len(t):,} 行 → 仓库-主体-重建.csv")

# ── 核对 ──
old = pd.read_csv(D + '仓库-主体.csv', encoding='utf-8-sig')
j = t[['org', 'corp_share', 'axis2_主体']].merge(
    old[['org', 'corp_share', 'axis2_主体']], on='org', how='inner', suffixes=('_new', '_old'))
print(f"\n[4] 核对（共同 org {len(j):,}）")
an = pd.to_numeric(j['corp_share_new'], errors='coerce')
bo = pd.to_numeric(j['corp_share_old'], errors='coerce')
both = an.notna() & bo.notna()
print(f"    corp_share   非空双双有值 {int(both.sum()):,}；"
      f"其中相等 {int((an[both] - bo[both]).abs().lt(1e-9).sum()):,}"
      f"（{100*(an[both]-bo[both]).abs().lt(1e-9).mean():.2f}%）；空值一一对应 "
      f"{int((an.isna() == bo.isna()).sum()):,}/{len(j):,}")
print(f"    axis2_主体   一致率 {100*(j['axis2_主体_new'] == j['axis2_主体_old']).mean():.2f}%")
