# -*- coding: utf-8 -*-
"""
重建 Q2：公司影响力来自自有账号还是员工

依赖链（本脚本把整条链跑通，全部 A 级）
----------------------------------------
  依赖图/funder.jsonl + 域名-实体字典.csv
        ↓  重建-仓库主体.py
  仓库-主体-重建.csv                org → corp_share（公司域名提交占比）
        ↓  按 ns 回填（本脚本已验证：100% 一致）
  包级 corp_share                   包 → corp_share
        ↓  与 包-账号-重建.csv + 主体分类-全量.csv 交叉
  Q2 的三个数：公司参与包数 / 有公司组织账号 / 无公司组织账号

为什么要有这个脚本
------------------
Q2 的 94.1% 原先依赖 `包-位置-主体-新刻度.csv` 的 corp_share，而该文件没有生成脚本
（溯源总表 C 级）。本脚本证明：corp_share 可由 `仓库-主体.csv` 的 ns 查表 100% 回填，
而 `仓库-主体.csv` 又可由 funder.jsonl + 域名字典完整重建。链条因此升为 A 级。

用法
  python 作业/整合/重建-包账号.py      # 先跑（产出 包-账号-重建.csv）
  python 作业/整合/重建-仓库主体.py    # 再跑（产出 仓库-主体-重建.csv）
  python 作业/整合/重建-Q2.py
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

R = Path(__file__).resolve().parent.parent.parent
D = str(R / '依赖图') + '/'
O = str(R / '作业/整合') + '/'

# ── 1. 包级 corp_share：仓库-主体[ns] 回填 ──
ref = pd.read_csv(O + '仓库-主体-重建.csv', encoding='utf-8-sig')
CS = dict(zip(ref.org, pd.to_numeric(ref.corp_share, errors='coerce')))
newk = pd.read_csv(D + '包-位置-主体-新刻度.csv', encoding='utf-8-sig', low_memory=False)
newk['corp_share_重建'] = newk.ns.map(CS)

a = pd.to_numeric(newk.corp_share, errors='coerce')
b = newk['corp_share_重建']
both = a.notna() & b.notna()
print(f"[1] 包级 corp_share 回填验证")
print(f"    非空双双有值 {int(both.sum()):,}，相等 {int((a[both]-b[both]).abs().lt(1e-9).sum()):,}"
      f"（{100*(a[both]-b[both]).abs().lt(1e-9).mean():.2f}%）")
print(f"    空值一一对应 {int((a.isna() == b.isna()).sum()):,}/{len(newk):,}")

# ── 2. 公司组织账号：包 → 账号 → 主体类型 ──
acc = pd.read_csv(O + '包-账号-重建.csv', encoding='utf-8-sig')
own = pd.read_csv(D + '主体分类-全量.csv', encoding='utf-8-sig', usecols=['owner', 'type'])
TYPE = dict(zip(own.owner, own.type))
acc['主体类型'] = acc['account'].map(TYPE)
corp_pk = set(acc.loc[acc['主体类型'] == '公司', 'crate'])

# ── 3. Q2 三个数 ──
df = newk[['pkg', 'corp_share_重建']].copy()
df['公司参与'] = df['corp_share_重建'].fillna(0) > 0
df['有公司组织账号'] = df.pkg.isin(corp_pk)
sub = df[df['公司参与']]
n_all, n_own = len(sub), int(sub['有公司组织账号'].sum())
n_emp = n_all - n_own
print(f"\n[2] Q2 重算（对照原结论 8,175 / 483 / 7,692 / 94.1%）")
print(f"    公司参与度 > 0 的包      {n_all:,}")
print(f"    其中 有公司组织账号      {n_own:,}")
print(f"    其中 无公司组织账号      {n_emp:,}  （{100*n_emp/max(n_all,1):.1f}%）")

# ── 4. 口径三选一（公司占全库入边） ──
tot = newk['in_deg_new'].sum()
w = (newk['corp_share_重建'].fillna(0) * newk['in_deg_new']).sum()
print(f"\n[3] 公司参与度加权（占全库入边）：{100*w/tot:.2f}%")
print(f"    公司组织账号触及的包占入边："
      f"{100*newk.loc[newk.pkg.isin(corp_pk), 'in_deg_new'].sum()/tot:.2f}%")

out = pd.DataFrame([
    {'指标': '公司参与度>0 的包', '值': n_all},
    {'指标': '有公司组织账号', '值': n_own},
    {'指标': '无公司组织账号（员工代持）', '值': n_emp},
    {'指标': '员工代持占公司参与包%', '值': round(100 * n_emp / max(n_all, 1), 1)},
    {'指标': '公司参与度加权占全库入边%', '值': round(100 * w / tot, 2)},
])
out.to_csv(O + 'Q2-重算.csv', index=False, encoding='utf-8-sig')
print(f"\n[4] 已写 Q2-重算.csv")
