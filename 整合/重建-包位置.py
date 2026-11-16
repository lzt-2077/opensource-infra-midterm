# -*- coding: utf-8 -*-
"""
重建位置表：`包-位置-v2.csv`

背景
----
旧 `包-位置-v2.csv`（171,730 行）没有生成脚本，且其 `in_deg_full` 所用的图**无法从现有数据确定**：

    serde   旧表 142,996 ｜ kind=0 得 139,264 ｜ kind=0+1 得 140,249 ｜ 全种类得 146,318
    tokio   旧表  83,863 ｜ kind=0 得  70,402 ｜ kind=0+1 得  70,483 ｜ 全种类得 104,559

三种候选都落在目标两侧，无法复现。因此本脚本**不再猜旧图**，而是在报告统一口径上
（2025-12，`kind=0` 且 `optional=false`）重建一张口径明确、可复现的位置表。

指标
----
    in_deg     入度（精确）
    reach      传递反向可达：有多少个包能通过任意长度依赖链到达它（KMV 近似）
    band_*     入度分档：0 / 1-9 / 10-99 / 100-999 / 1000-2999 / 3000+
    pct_*      百分位（0-100）

reach 的算法
------------
1. 先做**强连通分量（SCC）缩点**，得到 DAG —— 依赖图里有环（可选依赖所致），不能直接拓扑排序
2. 给每个节点一个随机 64 位哈希；每个分量保存其成员中最小的 k 个哈希（KMV 草图）
3. 按拓扑序遍历边 c' → c，把 c' 的草图并入 c（union 后截断到 k）
4. 估计 |T(c)|：草图满 k 时用 KMV 估计式 (k-1)/(max_hash/2^64)，不满 k 时即精确计数
5. reach(v) = |T(component(v))| - 1

k=128 时相对误差约 1/√k ≈ 9%，用于分档与百分位足够；本脚本会与旧表做秩相关对照。

用法： python 作业/整合/重建-包位置.py
"""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd, igraph as ig
sys.stdout.reconfigure(encoding='utf-8')

R = Path(__file__).resolve().parent.parent.parent
D = str(R / '依赖图') + '/'
O = str(R / '作业/整合') + '/'
K = 128
ANCHOR = pd.Timestamp('2025-12-14T02:00:00Z')
t0 = time.time()


def P(*a):
    print(f"[{time.time()-t0:5.1f}s]", *a, flush=True)


# ── 1. 主图边 ──
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
e = chosen[EV] & ~EO
dep_c = ED[e]
root_c = np.array([CID.get(int(x), -1) for x in EV[e]])
ok = (root_c > 0) & (dep_c != root_c)
dep_c, root_c = dep_c[ok], root_c[ok]
P(f"主图边 {len(dep_c):,}")

mp = pd.read_csv(D + '年代图/命名空间映射-2026.csv', encoding='utf-8-sig',
                 usecols=['crate_id', 'name', 'namespace', 'repo_key', 'forge'])
# pandas 3.0 的 str dtype 会保留 NaN，必须先过滤再 lower
_nm = mp.name.astype('object').where(mp.name.notna(), None)
c2n = {int(c): str(n).lower() for c, n in zip(mp.crate_id, _nm) if n is not None}
n2c = {v: k for k, v in c2n.items()}
# 节点 = 两端都能映射到包名的边（必须同时过滤，否则 zip 会静默截断）
rn = [c2n.get(int(x)) for x in root_c]
dn = [c2n.get(int(x)) for x in dep_c]
keep = np.array([(a is not None) and (b is not None) and (a != b) for a, b in zip(rn, dn)])
rn = [a for a, k in zip(rn, keep) if k]
dn = [b for b, k in zip(dn, keep) if k]
nodes = sorted(set(rn) | set(dn))
node_ix = {n: i for i, n in enumerate(nodes)}
Nn = len(nodes)
root = np.fromiter((node_ix[a] for a in rn), np.int64, len(rn))
dep = np.fromiter((node_ix[b] for b in dn), np.int64, len(dn))
assert len(root) == len(dep), (len(root), len(dep))
P(f"节点 {Nn:,}  边 {len(root):,}（两端均可映射）")

# ── 2. SCC 缩点 ──
g = ig.Graph(n=Nn, edges=list(zip(root.tolist(), dep.tolist())), directed=True)
g.simplify()
scc = g.connected_components(mode='strong')
mem = np.array(scc.membership)
Nc = mem.max() + 1
sizes = np.bincount(mem, minlength=Nc)
P(f"SCC：{Nc:,} 个分量，最大 {int(sizes.max()):,}")

# 分量级边（去重）
ce = np.unique(np.stack([mem[root], mem[dep]], axis=1), axis=0)
ce = ce[ce[:, 0] != ce[:, 1]]
P(f"分量级边 {len(ce):,}")
gd = ig.Graph(n=Nc, edges=list(zip(ce[:, 0].tolist(), ce[:, 1].tolist())), directed=True)
gd.simplify()
order = gd.topological_sorting(mode='OUT')          # 源在前
P(f"拓扑序 {len(order):,}")

# ── 3. KMV 草图 ──
rng = np.random.default_rng(20261116)
h = rng.integers(0, 2**63, size=Nn, dtype=np.int64)
Rk = np.zeros((Nc, K), dtype=np.int64)              # 0 表示空位（哈希右移保证 >0）
rank = np.full(Nc, -1, dtype=np.int64)
for c in range(Nc):
    m = h[mem == c] if sizes[c] <= K else np.sort(h[mem == c])[:K]
    Rk[c, :len(m)] = np.sort(m)
    rank[c] = len(m)                                 # 记录是否已满

edges_by_src = {}
src_arr, dst_arr = ce[:, 0], ce[:, 1]
ordpos = np.empty(Nc, np.int64)
ordpos[order] = np.arange(Nc)

def merge_into(dst, src):
    cur = Rk[dst][Rk[dst] > 0]
    add = Rk[src][Rk[src] > 0]
    if len(add) == 0:
        return
    u = np.union1d(cur, add)
    if len(u) > K:
        u = u[:K]
    Rk[dst] = 0
    Rk[dst, :len(u)] = u
    rank[dst] = len(u)

# 按拓扑序处理：src 必须先完成
edge_list = sorted(zip(src_arr.tolist(), dst_arr.tolist()), key=lambda x: ordpos[x[0]])
for s_, d_ in edge_list:
    merge_into(d_, s_)
P(f"KMV 传播完成（k={K}）")

# ── 4. 估计 reach ──
T = np.empty(Nc, dtype=np.int64)
for c in range(Nc):
    cur = Rk[c][Rk[c] > 0]
    if len(cur) < K:
        T[c] = len(cur)                              # 精确
    else:
        est = (K - 1) * (2.0 ** 63) / float(cur[-1])
        T[c] = min(int(est), Nn)
P(f"reach 估计完成，中位 {np.median(T):,.0f}，最大 {T.max():,}")

# ── 5. 组装表 ──
ind = np.bincount(dep, minlength=Nn)
reach_node = T[mem] - 1                              # 去掉自己
pos = pd.DataFrame({'pkg': nodes, 'in_deg': ind, 'reach': reach_node})

def band(x):
    if x <= 0: return '0'
    if x < 10: return '1-9'
    if x < 100: return '10-99'
    if x < 1000: return '100-999'
    if x < 3000: return '1000-2999'
    return '3000+'

pos['band_full'] = pos.in_deg.map(band)
pos['pct_full'] = (pos.in_deg.rank(pct=True) * 100).round(2)
pos['reach_band'] = pos.reach.map(lambda x: '0' if x <= 0 else '1-9' if x < 10 else
                                  '10-99' if x < 100 else '100-999' if x < 1000 else
                                  '1k-10k' if x < 10000 else '10k-100k' if x < 100000 else '100k+')
pos['pct_reach'] = (pos.reach.rank(pct=True) * 100).round(2)
pos['crate_id'] = pos.pkg.map(n2c)
pos = pos.merge(mp.rename(columns={'name': 'pkg'})[['pkg', 'namespace', 'repo_key', 'forge']],
                on='pkg', how='left').rename(columns={'namespace': 'ns'})
# 主体信息（来自已重建的 org 层）
try:
    sub = pd.read_csv(D + '仓库-主体.csv', encoding='utf-8-sig',
                      usecols=['org', 'axis1_发版账号数', 'axis2_主体', 'corp_share'])
    pos = pos.merge(sub, left_on='ns', right_on='org', how='left') \
             .rename(columns={'axis1_发版账号数': 'axis1', 'axis2_主体': 'axis2'}) \
             .drop(columns=['org'])
except FileNotFoundError:
    pass
pos.to_csv(O + '包-位置-重建.csv', index=False, encoding='utf-8-sig')
P(f"已写 包-位置-重建.csv（{len(pos):,} 行 × {len(pos.columns)} 列）")

# ── 6. 与旧表对照（秩相关） ──
old = pd.read_csv(D + '包-位置-v2.csv', encoding='utf-8-sig', low_memory=False)
j = pos[['pkg', 'in_deg', 'reach']].merge(old[['pkg', 'in_deg_full', 'reach_full']], on='pkg')
print(f"\n对照旧表（共同包 {len(j):,}）")
for a, b in [('in_deg', 'in_deg_full'), ('reach', 'reach_full')]:
    m = j[a].notna() & j[b].notna()
    print(f"  {a:<8} vs {b:<12} Spearman {j.loc[m, a].corr(j.loc[m, b], method='spearman'):.4f}")
print("  说明：旧表所用图无法确定（见文件头），此处只验证方向一致性，不追求数值相同。")
