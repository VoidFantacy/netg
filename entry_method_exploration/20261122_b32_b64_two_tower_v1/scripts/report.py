"""Summarize sealed-run metrics in the experiment report."""
import csv
from pathlib import Path

from run import DATASETS, ROOT, cfg, read

A = ROOT/'analysis'
DS = dict(zip(DATASETS, ('COCO','WebVid')))


def csv_rows(name):
    with (A/f'{name}.csv').open() as f:
        return list(csv.DictReader(f))


def keyed(rows, *fields):
    return {tuple(r[f] for f in fields):r for r in rows}


def f(row, key):
    return float(row[key])


def i(row, key):
    return int(row[key])


def pct(value):
    return f'{value*100:.4f}%'


points = keyed(csv_rows('points'),'dataset','L','method')
same = keyed(csv_rows('same_L'),'dataset','L','method')
replays = keyed(csv_rows('replay'),'dataset','L','method','cap')
frontiers=read(A/'outcomes.json')
parity=csv_rows('E225_coco_B32_packet_parity')
identical=sum(all(v=='True' for key,v in line.items() if key!='L') for line in parity)
text = [
    '# E226 COCO / WebVid 双塔直接补点',
    '',
    '在相同 GT10 主搜索后合并原生 raw-IP 精算结果。B32 保留原版，B64 按原联合未覆盖贪心扩展，并保留每行的有序 B32 前缀。两池各训练独立查询塔和候选塔。塔为无偏置 512→32 线性映射，按真实池内遗漏成员和同池原内积教师分布训练。正式精算上限固定为 48 个去重后的候选。',
    '',
    '这轮保留原版 B32 为默认补点对照。全精算 B64 在两集出现值得单独复验的 Recall–QPS 结果。两种双塔都比同池同预算 PCA 回收更多真值成员，固定 48 的版本尚未稳定改善原版 B32 的完整曲线。',
    '',
    '## 正式完整计时',
    '',
    'COCO hard、WebVid soft-t1 各 3,072 条真实查询，真 K100。11 档 L、每集 66 点，合计 132 点、264 批、811,008 次计时查询。CPU15 每次单线程，测两遍，完整路由、主搜、投影、候选选择、精算、Top-K 合并及返回包生命周期。加载、预热、GT 评分、写盘和额外审计在计时外。',
    '',
    'L184 延续前一轮重点预算。工作量取 256 条正式前缀资格见证，质量和吞吐取各 3,072 条完整批次。',
    '',
    '| 数据集 | 方法 | Recall@100 | 完整 QPS | 候选池均值 | 精算均值 | 对 B32 全链路 μs/query 差 |',
    '|---|---|---:|---:|---:|---:|---:|',
]
for ds in DATASETS:
    base=points[ds,'184','B32']
    for arm in ('B32','PCA-B32','TT-B32','B64','PCA-B64','TT-B64'):
        p=points[ds,'184',arm]
        text.append(f'| {DS[ds]} | {arm} | {pct(f(p,"recall"))} | {f(p,"qps"):,.1f} | '
                    f'{f(p,"mean_pool_256"):.1f} | {f(p,"mean_exact_256"):.1f} | {f(p,"wall_us")-f(base,"wall_us"):+.2f} |')
text += ['', '### 同期 B32 前沿', '',
    '离散对照对每个新方法点取至少同召回的最快原版 B32。慢遍比较使用新方法慢遍对 B32 快遍。折线按实际测点做召回重叠区间内插值，仅用于描述曲线。', '',
    '| 数据集 | 方法 | 离散达标对照存在 | 均值更快 | 慢遍仍更快 | 在 B32 折线右侧 |',
    '|---|---|---:|---:|---:|---:|']
for ds in DATASETS:
    for method in ('TT-B32','TT-B64','B64'):
        a=frontiers[ds][method]
        text.append(f'| {DS[ds]} | {method} | {a["eligible"]}/11 | {a["faster_than_discrete"]} | '
            f'{a["slow_faster_than_fast"]} | {a["faster_than_B32_line"]}/{a["overlap"]} |')
text += ['', '全精算 B64 在 16 个召回重叠点中有 15 个位于 B32 折线右侧。按已测离散目标比较，L200 相对最快达标 B32 的完整 QPS 在 COCO 高 5.34%、WebVid 高 6.73%，达标对照均为 L224。两点相对折线分别高 0.91% 与 1.47%。该条件证据优先用于独立密集复测。', '', '### 同池同精算的学习贡献', '',
         '| 数据集 | 宽度 | 双塔优于 PCA 的 L 档 | Recall 差范围（百分点） | L184 救回 / 损伤 |',
         '|---|---|---:|---:|---:|']
for ds in DATASETS:
    for w in ('32','64'):
        cases=[r for (d,l,m),r in same.items() if d==ds and m==f'TT-B{w}']
        deltas = [i(r,'PCA_net') for r in cases]
        at=same[ds,'184',f'TT-B{w}']
        text.append(f'| {DS[ds]} | B{w} | {sum(x>0 for x in deltas)}/11 | '
                    f'{min(deltas)/3072:+.4f} 至 {max(deltas)/3072:+.4f} | {at["PCA_rescued"]} / {at["PCA_damaged"]} |')
text += ['', '## 候选供给与校准回放', '',
    '冻结主返回评估 L176/184/200/224。每集 56 点，COCO 1,024 条、WebVid 1,020 条校准查询，合计 114,464 次选点与原生合并。逐查询检查 B64 为 B32 的超集，并检查进入精算的候选属于对应全池，原版 B32 结果与 E222 位级一致。下表为 L184。', '',
    '| 数据集 | B32 / B64 候选中的真实漏点数 | B64 全精算相对 B32 净增 | 双塔 B32 / B64 精算 48 相对 B32 净增 |',
    '|---|---:|---:|---:|']
for ds in DATASETS:
    base=replays[ds,'184','B32','96']
    wide=replays[ds,'184','B64','192']
    vals=[i(replays[ds,'184',arm,'48'],'hits')-i(base,'hits') for arm in ('TT-B32','TT-B64')]
    text.append(f'| {DS[ds]} | {base["gt_members_in_scored_candidates"]} / {wide["gt_members_in_scored_candidates"]} | '
                f'{i(wide,"hits")-i(base,"hits"):+,} | {vals[0]:+,} / {vals[1]:+,} |')
text += ['', '## 覆盖、成本与复核', '',
    f'正式输出两遍逐字节一致，独立 Python 集合和 NumPy 评分核实 132 点，256 条前缀逐查询用独立原生标量全排序比对。COCO 同窗的原版 B32 与封存 E225 有 {identical}/11 组四个载荷逐字节一致。WebVid 的训练和校准与公开正式窗做了精确向量字节隔离。WebVid 有四条旧窗重复记录被排除，正式窗保留原始 3,072 条及其一对重复向量。两集正式窗在历史实验使用过，实验范围为 K100 的两集同分布留出。',
    '',
    '以下增量大小按实际结构计算。每臂需一份码本、查询权重和全基库大小的 int32 ID 到码槽映射，B64 另需扩展表。正式对照进程一次加载三个码本用于串行测量。构建和拟合为独立离线墙钟。', '',
    '| 数据集 | 唯一编码 ID | 单臂 B32 / B64 增量 MiB | 扩 B64 表 | 两池拟合及准备 |',
    '|---|---:|---:|---:|---:|']
for ds in DATASETS:
    base=ROOT/'models'/ds
    receipt=read(base/'training.json')
    pool=read(base/'pool/complete.json')
    storage=sum((base/'twin32'/v).stat().st_size for v in ('codes.f32','query.f32'))
    storage+=4*read(cfg(ds,'formal'))['base']['n']
    wide=sum((base/'pool'/v).stat().st_size for v in ('B64.ids.i32','B64.counts.i8'))
    text.append(f'| {DS[ds]} | {receipt["bank_size"]:,} | {storage/2**20:.2f} / {(storage+wide)/2**20:.2f} | '
                f'{pool["seconds"]:.2f} s | {receipt["offline_wall_seconds"]:.2f} s |')
text += ['', '![双塔与原版 B32 的正式四格对照](analysis/recall_qps.png)', '',
    '[协议](protocol.md) · [完整点](analysis/points.csv) · [两遍原始时间](analysis/rounds.csv) · [同期达标配对](analysis/matched.csv) · [正式救损](analysis/same_L.csv) · [全部校准回放](analysis/replay.csv) · [封存](seal.json)', '']
with (ROOT/'report.md').open('x') as out:
    out.write('\n'.join(text))
