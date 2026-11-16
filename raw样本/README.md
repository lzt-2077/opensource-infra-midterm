# 原始数据样本（raw samples）

> 原始数据总量约 4.8 GB（去重后实际体积；不含 crates.io 的 2.2 GB 压缩包，避免同一源重复计算），按作业要求不全部上传，此处提交**代表性样本**用于验证字段结构与清洗链条。
> 完整数据的采集与重建脚本见 `../整合/构建.py` 与 `依赖图/年代图/入驻/64a-抽直达层.py`、`64b-切片.py`。

| 文件 | 来源 | 行数 | 大小 | 说明 |
|---|---|---|---|---|
| `S1-dependencies-样本.csv` | crates.io `dependencies.csv` | 5,000 | 158 KB | 依赖声明。**注意：`crate_id` 列是依赖目标，`version_id` 才是发出依赖的版本** |
| `S1-crates-样本.csv` | crates.io `crates.csv` | 2,000 行（含多行 readme 字段，实际记录数少于行数） | 85 KB | 包元数据 |
| `S1-versions-样本.csv` | `versions-id.csv` | 5,000 | 266 KB | 版本时间轴，用于构造月度快照 |
| `S1-crate_owners-样本.csv` | crates.io `crate_owners.csv` | 2,000 | 89 KB | 包 → 账号（跨源关联起点） |
| `S2-pypi-样本.parquet` | PyPI BigQuery 导出 | 3,000 | 327 KB | 列式存储；13 列 |
| `S3-github-contributors-样本.jsonl` | GitHub API | 2,000 | 2.6 MB | 贡献者记录 |

## 字段口径提醒

1. **`dependencies.csv` 没有 `dep_crate_id` 列**，`crate_id` 列即依赖目标。
2. **`optional` 列是 `t`/`f` 字符串**，不是布尔值。用 `astype(bool)` 解析会把 `'f'` 判为真（本项目实际踩过这个坑，见 `../报告.md` §3.2）。
3. `kind` 取值：`0` = normal，`1` = build，`2` = dev。本项目主分析只用 `kind=0`。
4. 同一 `(version_id, crate_id, kind)` 可能因 `target` 不同出现多行，占必需依赖边的 0.21%。

## 完整数据的校验信息

| 数据块 | 规模 | 记录数 |
|---|---|---|
| crates.io 数据库 dump（tar.gz） | 2.2 GB | — |
| └ 解包后 `data/` | 3.2 GB | 16 个文件 |
| └ `dependencies.csv` | 1.9 GB | 43,258,107 行 |
| └ `crates.csv` | 1.4 GB | 377,431 条记录 |
| └ `versions-id.csv` | 197 MB | 3,700,490 行 |
| PyPI Parquet（6 分片） | 1.4 GB | — |
| GitHub contributors.jsonl | 4.3 MB | — |
| 基金会 PDF | 约 100 MB | 9 份 |

完整数据的重建方式：把 dump 解包到 `依赖图/2026-11-14-020024/data/`，然后运行 `依赖图/年代图/入驻/64a-抽直达层.py`（约 31 秒生成 298 MB 紧凑层），此后任意时点切片由 `64b-切片.py` 完成（约 2 秒/时点）。
