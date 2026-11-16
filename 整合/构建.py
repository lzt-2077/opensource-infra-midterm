# -*- coding: utf-8 -*-
"""
构建 Integrated Data（多源融合层）

输入（4 类独立数据源 + 2 个派生层）
  1. crates.io 数据库全量 dump          → 版本时间轴、依赖边
  2. crates.io owners 表                → 包级账号（包-账号.csv）
  3. GitHub 组织/贡献者抓取             → 仓库组织、发版账号、提交数、公司域名
  4. 生态位置派生层（依赖图 146 个月快照）→ 入度、传递可达、底基层级

输出
  作业/整合/包级融合表-crates.parquet    一行一个包
  作业/整合/包-账号-公司域名.parquet      一行一个(包,账号)，带人员公司域名
  作业/整合/样本-*.csv                   各表前 5000 行（提交用）

用法： python 作业/整合/构建.py
"""
import sys
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

D = '依赖图/'
O = '作业/整合/'
ENC = 'utf-8-sig'


def rd(p, **k):
    return pd.read_csv(p, encoding=ENC, low_memory=False, **k)


def to_str(df):
    """parquet 不接受 object 列里混 int/str，统一转字符串"""
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(str).replace({'nan': None})
    return df


# ══════════════ 1. 依赖图位置（2025-12，主图：kind=0 且 optional=false）══════════════
v = pd.read_csv(D + 'versions-id.csv', encoding=ENC,
                dtype={'id': 'int64', 'crate_id': 'int64'},
                usecols=['id', 'crate_id', 'created_at'])
v['ts'] = pd.to_datetime(v['created_at'], utc=True, format='mixed', errors='coerce')
v = v.dropna(subset=['ts'])
v = v[v.ts <= pd.Timestamp('2025-12-14T02:00:00Z')]
last = v.sort_values('ts').groupby('crate_id', as_index=False).tail(1)
CID = dict(zip(last.id.astype('int64').values, last.crate_id.astype('int64').values))

z = np.load(D + '年代图/入驻/_dep-normal-opt.npz')
EV, ED, EO = z['version_id'], z['dep_crate_id'], z['is_opt'].astype(bool)
maxv = int(max(EV.max(), last.id.max())) + 2
chosen = np.zeros(maxv, bool)
chosen[last.id.to_numpy()] = True
e = chosen[EV] & ~EO
mp = pd.read_csv(D + '年代图/命名空间映射-2026.csv', encoding=ENC,
                 usecols=['crate_id', 'name'])
c2n = {int(c): str(x).lower() for c, x in zip(mp.crate_id, mp.name) if pd.notna(x)}
dep_n = np.array([c2n.get(int(x), '') for x in ED[e]], dtype=object)
root_n = np.array([c2n.get(int(x), '') for x in EV[e]], dtype=object)
root_n = np.array([c2n.get(int(CID.get(int(x), -1)), '') for x in EV[e]], dtype=object)
ok = (dep_n != '') & (root_n != '') & (dep_n != root_n)
ind = pd.Series(dep_n[ok]).value_counts()
outd = pd.Series(root_n[ok]).value_counts()
base = set(ind[ind >= 366].index)
g = pd.DataFrame({'包': ind.index, '入度_主图': ind.values})
g['出度_主图'] = g['包'].map(outd).fillna(0).astype(int)
g['是否底基2025'] = g['包'].isin(base)
print(f"[1] 依赖图 2025-12（主图）：被依赖包 {len(g):,}；底基(入度≥366) {len(base)}")

# ══════════════ 2. 位置/主体/领域/技术层/公司参与度 ══════════════
pos = rd(D + '包-位置-v2.csv',
         usecols=['pkg', 'crate_id', 'ns', 'repo_key', 'forge', 'in_deg_full',
                  'band_full', 'reach_full', 'reach_band', 'axis1', 'axis2'])
pos = pos.rename(columns={'pkg': '包', 'ns': '命名空间', 'in_deg_full': '入度_全图',
                          'band_full': '入度档', 'reach_full': '传递可达',
                          'reach_band': '可达档', 'axis1': '发版主体', 'axis2': '法人类型_旧单列'})
lay = rd(D + '包-位置-主体-新刻度.csv', usecols=['pkg', 'domain', 'cohort', 'corp_share'])
lay = lay.rename(columns={'pkg': '包', 'domain': '技术领域', 'cohort': '首发年',
                          'corp_share': '公司占比'})
sub = rd(D + 'crate-主体分类.csv',
         usecols=['crate', 'repo_org', 'owners', 'type', 'conf', 'basis'])
sub = sub.rename(columns={'crate': '包', 'repo_org': '仓库组织', 'owners': 'crates账号',
                          'type': '主体类型', 'conf': '分类置信', 'basis': '分类依据'})
tec = rd(D + '年代图/入驻/74-底基-技术分层.csv',
         usecols=['包', '技术层', '分类', '描述'])
tec = tec.rename(columns={'分类': 'crates分类', '描述': '包描述'})
comp = rd(D + '包-公司参与度.csv', usecols=['pkg', 'comp_all', 'type'])
comp = comp.rename(columns={'pkg': '包', 'comp_all': '公司参与占比', 'type': '参与度类型'})
# 三列模型（法人类型 × 组织形态 × 财政赞助），见 43-轴二三列模型.md
tri = rd(D + '年代图/入驻/_三列-cargo-填赞助.csv',
         usecols=['ns', '法人类型', '组织形态', '财政赞助'])
tri = tri.rename(columns={'ns': '命名空间'}).drop_duplicates('命名空间')

t = (pos.merge(lay, on='包', how='left')
        .merge(sub, on='包', how='left')
        .merge(tec, on='包', how='left')
        .merge(comp, on='包', how='left')
        .merge(tri, on='命名空间', how='left')
        .merge(g, on='包', how='left'))
t['技术层'] = t['技术层'].fillna('非底基')
t['是否底基2025'] = t['是否底基2025'].fillna(False).astype(bool)
t['入度_主图'] = t['入度_主图'].fillna(0).astype(int)
t['出度_主图'] = t['出度_主图'].fillna(0).astype(int)
t = to_str(t)
t.to_parquet(O + '包级融合表-crates.parquet', index=False)
t.head(5000).to_csv(O + '样本-包级融合表.csv', index=False, encoding=ENC)
print(f"[2] 包级融合表 {len(t):,} 行 × {len(t.columns)} 列")
print("    列：" + " | ".join(t.columns))

# ══════════════ 3. 包 × 账号 × 账号主体（跨源实体解析）══════════════
acc = rd(D + '包-账号.csv', usecols=['crate', 'account', 'account_kind', 'is_nonhuman'])
acc.columns = ['包', '账号', '账号类型', '非人类']
own = rd(D + '主体分类-全量.csv',
         usecols=['owner', 'kind', 'name', 'type', 'conf', 'basis'])
own = own.rename(columns={'owner': '账号', 'kind': 'GitHub账号类型', 'name': '账号显示名',
                          'type': '账号主体类型', 'conf': '主体置信', 'basis': '主体依据'})
m = acc.merge(own, on='账号', how='left')
m['已关联主体'] = m['账号主体类型'].notna()
m = m.merge(t[['包', '入度_全图', '传递可达', '法人类型', '组织形态', '技术层', '是否底基2025']],
            on='包', how='left')
m = to_str(m)
m.to_parquet(O + '包-账号-主体.parquet', index=False)
m.head(5000).to_csv(O + '样本-包账号主体.csv', index=False, encoding=ENC)
print(f"[3] 包-账号-主体表 {len(m):,} 行；账号 {m['账号'].nunique():,}")
_ua = acc['账号'].nunique()
_ma = len(set(acc['账号'].dropna()) & set(own['账号'].dropna()))
print(f"    关联成功率：行级 {100*m['已关联主体'].sum()/len(m):.1f}%"
      f"（{int(m['已关联主体'].sum()):,}/{len(m):,}）"
      f"；账号级 {100*_ma/_ua:.1f}%（{_ma:,}/{_ua:,}）")

# ══════════════ 4. Q1 口径说明 ══════════════
# Q1 采用三列模型（法人类型 × 组织形态 × 财政赞助），见 43-轴二三列模型.md。
# 早期版本的「排他主体」单列分类（公司>非营利>无法人>个人）已被否决：它把「个人」
# （组织形态的取值）与「公司/非营利/无」（法人类型的取值）压进同一优先级，
# 属于把两个正交维度压成一列的假选择。相关产物已删除。
print("[4] Q1 使用三列模型（法人类型 / 组织形态 / 财政赞助），三列已并入包级融合表")

print("[5] 各字段非空覆盖率")
for c in ['命名空间', '仓库组织', 'crates账号', '法人类型', '组织形态', '财政赞助',
          '技术领域', '技术层', '入度_全图', '是否底基2025']:
    s = t[c]
    cov = (s.notna() & (s != '')).mean() if s.dtype == object else s.notna().mean()
    print(f"    {c:<12}{100*cov:>6.1f}%")
