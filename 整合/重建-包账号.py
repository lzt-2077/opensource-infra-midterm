# -*- coding: utf-8 -*-
"""
重建 `包-账号.csv`（crate × 账号）

为什么需要这个脚本
------------------
`依赖图/包-账号.csv`（422,586 行）是 Q1/Q2 的实体关联起点，但仓库里没有生成它的脚本（溯源总表等级 C）。
本脚本从 crates.io dump 的四张表完整重建，并与现有文件逐字段核对。

上游（全部在 2026-11-14-020024/data/）
    crate_owners.csv   crate_id, created_at, created_by, owner_id, owner_kind(0=user,1=team)
    users.csv          id, username                        ← owner_id → 账号名
    teams.csv          id, login(github:org:team)          ← team 型 owner → 组织名
    年代图/命名空间映射-2026.csv  crate_id, name            ← crate_id → 包名

字段规则（逆向自现有文件）
    account       = users.username（owner_kind=0）
                  = teams.login 的第二段（owner_kind=1）
                  = ghost_<owner_id>（users 里查不到）
    account_kind  = user / team（由 owner_kind 决定）
    team_login    = teams.login（仅 team 型）
    added_at      = crate_owners.created_at
    added_by      = users.username[created_by]
    is_nonhuman   = 人工判定的自动化账号清单（见下），共 180 个

关于 is_nonhuman
----------------
该项是**人工判定**，不是规则。清单一度只能从现有文件反推；本脚本把它落到
`账号-非人类.csv`（含 provenance 说明），使脚本本身不依赖被审计的文件。

用法： python 作业/整合/重建-包账号.py
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

R = Path(__file__).resolve().parent.parent.parent
D = str(R / '依赖图/2026-11-14-020024/data') + '/'
G = str(R / '依赖图') + '/'
O = str(R / '作业/整合') + '/'

# ── 1. 上游 ──
co = pd.read_csv(D + 'crate_owners.csv', encoding='utf-8-sig')
us = pd.read_csv(D + 'users.csv', encoding='utf-8-sig')
tm = pd.read_csv(D + 'teams.csv', encoding='utf-8-sig')
mp = pd.read_csv(G + '年代图/命名空间映射-2026.csv', encoding='utf-8-sig',
                 usecols=['crate_id', 'name'])
print(f"[1] crate_owners {len(co):,} / users {len(us):,} / teams {len(tm):,} / 名称映射 {len(mp):,}")

U = dict(zip(us.id, us.username))
T = dict(zip(tm.id, tm.login))
N = dict(zip(mp.crate_id, mp.name))

# ── 2. 非人类清单 ──
NL = Path(O) / '账号-非人类.csv'
if NL.exists():
    nnh = set(pd.read_csv(NL, encoding='utf-8-sig')['account'])
    print(f"[2] 读入人工判定清单 {len(nnh)} 个账号")
else:
    src = Path(G) / '包-账号.csv'
    nnh = set(pd.read_csv(src, encoding='utf-8-sig', low_memory=False)
              .query('is_nonhuman == 1')['account'].dropna().unique()) if src.exists() else set()
    pd.DataFrame({'account': sorted(nnh)}).to_csv(NL, index=False, encoding='utf-8-sig')
    print(f"[2] 从现有文件反推并落实清单 {len(nnh)} 个 → 账号-非人类.csv（人工判定，非规则）")

# ── 3. 组装 ──
def acct(oid, kind):
    if kind == 1:
        l = T.get(oid)
        return (l.split(':')[1] if l else f'ghost_{oid}'), l
    return U.get(oid, f'ghost_{oid}'), np.nan

rows = np.empty((len(co), 2), dtype=object)
for i, (oid, kind) in enumerate(zip(co.owner_id.to_numpy(), co.owner_kind.to_numpy())):
    rows[i, 0], rows[i, 1] = acct(int(oid), int(kind))

out = pd.DataFrame({
    'crate': co.crate_id.map(N).fillna(''),
    'crate_id': co.crate_id,
    'account': rows[:, 0],
    'account_kind': np.where(co.owner_kind == 1, 'team', 'user'),
    'team_login': rows[:, 1],
    'is_nonhuman': [1 if a in nnh else 0 for a in rows[:, 0]],
    'added_at': co.created_at,
    'added_by': co.created_by.map(U),
})
out.to_csv(O + '包-账号-重建.csv', index=False, encoding='utf-8-sig')
print(f"[3] 重建 {len(out):,} 行 → 包-账号-重建.csv")

# ── 4. 与现有文件核对 ──
old = Path(G) / '包-账号.csv'
if old.exists():
    o = pd.read_csv(old, encoding='utf-8-sig', low_memory=False)
    print(f"\n[4] 核对现有文件（{len(o):,} 行）")
    new_key = set(zip(out.crate_id, out.account))
    old_key = set(zip(o.crate_id, o.account))
    inter = len(new_key & old_key)
    print(f"    (crate_id, account) 行集合：新 {len(new_key):,} / 旧 {len(old_key):,} / 交集 {inter:,}"
          f"  Jaccard {inter/len(new_key|old_key):.4f}")
    for col in ['account_kind', 'team_login', 'is_nonhuman', 'added_at', 'added_by']:
        a = out.set_index(['crate_id', 'account'])[col]
        b = o.set_index(['crate_id', 'account'])[col]
        common = a.index.intersection(b.index)
        if len(common) == 0:
            continue
        same = (a.loc[common].astype(str).fillna('') == b.loc[common].astype(str).fillna('')).mean()
        print(f"    {col:<13} 共同行 {len(common):,}  一致率 {100*same:.2f}%")
