"""Write and seal the full four-dataset result package."""
import csv
from pathlib import Path
import sys

from drive import BATCHES,DATASETS,NAMES,POINTS,ROOT,WEBVID,config,digest,read,verify,write

A=ROOT/'analysis'


def csv_rows(file):
    with (A/f'{file}.csv').open() as stream:
        return list(csv.DictReader(stream))


def f(row,key):
    return float(row[key])


def fmt(row,method):
    if not row[f'{method}_L']:
        return '—'
    return f'L{row[f"{method}_L"]} / {f(row,f"{method}_recall_pct"):.4f}% / {f(row,f"{method}_qps"):,.1f}'


def delta(value):
    return '—' if value=='' else f'{float(value):+.2f}%'


def main():
    points=csv_rows('points'); goals=csv_rows('targets'); paired=csv_rows('same_L')
    assert len(points)==POINTS and len(csv_rows('rounds'))==BATCHES
    outcome=read(A/'outcome.json')
    legacy=csv_rows('historical_parity')
    ok=sum(all(row[k]=='True' for k in ('ids.i32','distances.f32','entry_ids.i32','profile_distances.f32')) for row in legacy)
    text=['# E229 四集 B32 与全精算 B64 正式测量', '',
        'COCO、Flickr30k、WebVid 2.5M、Yandex first10M 各 3,072 条官方公开查询。真 K1 和 K100 均独立执行，四集共 218 点、436 批、1,339,392 个计时查询。CPU15 实际单线程，每点两遍完整端到端，QPS 取两遍算术平均。两臂冻结同一 GT10 路由及 SPAN4 主搜索。B64 每路保留原 B32 前缀，三路取并集、去重并排除主返回，随后全部做原 raw-IP 精算。', '',
        'COCO 和 WebVid 延用 E228 隔离窗，Flickr30k 和 Yandex 延用 E213 前窗。查询与相应训练角色复核无重叠，COCO/Flickr30k 以源组核验，WebVid/Yandex 核精确向量字节。各窗为历史公共查询。两种 K 共享在原 K100/L200 训练 token 上扩出的 B64 表，所有召回均从各自真实返回与正式 GT 独立评分。', '',
        '按双边都达到的固定目标，B64 平均 QPS 更快为 K1 8/24、K100 15/35 个，慢遍仍快为 8/24、12/35。WebVid 两种 K 的收益较一致，COCO K1 和 Flickr30k K100 有条件收益。COCO K100 本轮只在 2/7 个目标的均值更高，慢遍均未超过原版快遍。Yandex 的 K1 同 L 召回全部相等，K100 同 L 增加 0.0146–0.0374 个百分点，两种 K 的达标目标均由 B32 更快。保留原版 B32 为通用对照，按数据集、K 与目标召回选择全精算 B64。', '',
        'WebVid K100 的 72% 目标，B64 L160 对 B32 L168 提高 0.46% 平均 QPS，两遍区间重叠。75.5% 目标 B64 L208 对 B32 L224 提高 2.97%，慢遍对快遍仍高 2.72%。本轮 COCO B64 的 K100 网格不含 E228 的 L204 配置，E228 密集窗回报的 +1.40% 与本轮 97% 目标的 +0.20% 使用不同实测网格。', '',
        '## 达标速度和同 L 结果', '',
        '双边达标使用固定目标下的两臂最快实测点。慢遍对快遍用于观察波动。折线统计仅在实测召回重叠区间内描述位置。', '',
        '| 数据集 | K | 双边达标目标 | B64 用小 L | B64 更快 | 慢遍仍更快 | 折线右侧 | 同 L 召回差（百分点） | 同 L QPS 差中位数 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for ds in DATASETS:
        for k in ('1','100'):
            a=outcome[ds][k]; low,high=a['same_L_recall_range_pp']; n=a['targets_both']
            text.append(f'| {NAMES[ds]} | {k} | {n}/{a["targets_total"]} | {a["targets_smaller_L"]}/{n} | '
                f'{a["targets_faster"]}/{n} | {a["targets_slow_faster"]}/{n} | {a["line_faster"]}/{a["line_both"]} | '
                f'{low:+.4f} 至 {high:+.4f} | {a["same_L_qps_delta_median"]:+.2f}% |')
    text += ['', '每个目标的 L、实际召回和完整 QPS 见下表。', '',
        '| 数据集 | K | 召回目标 | GT10+B32 | GT10+B64 | QPS 差 | 慢遍对快遍 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for row in goals:
        text.append(f'| {NAMES[row["dataset"]]} | {row["K"]} | {f(row,"target_pct"):g}% | {fmt(row,"B32")} | '
                    f'{fmt(row,"B64")} | {delta(row["qps_delta_pct"])} | {delta(row["slow_vs_fast_pct"])} |')
    text+=['', '## L200 同档与扩表资源', '',
        '| 数据集 | K | 原版召回 / QPS | 全精算召回 / QPS | 多精算 | 真值救回 / 损伤 | 命中 0–9 变化 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for ds in DATASETS:
        for k in ('1','100'):
            a=next(p for p in paired if p['dataset']==ds and p['K']==k and p['L']=='200')
            b,t=(next(p for p in points if p['dataset']==ds and p['K']==k and p['L']=='200' and p['method']==m) for m in ('B32','B64'))
            fail=f'{b["failures_under_10"]} → {t["failures_under_10"]}' if k=='100' else '—'
            text.append(f'| {NAMES[ds]} | {k} | {f(b,"recall_pct"):.4f}% / {f(b,"qps"):,.1f} | '
                f'{f(t,"recall_pct"):.4f}% / {f(t,"qps"):,.1f} | {f(a,"mean_added_exact_256"):.1f} | {a["rescued"]} / {a["lost"]} | {fail} |')
    text += ['', '精算量为前 256 条原生核验见证的算术平均。峰值 RSS 包含完整索引和两臂共用进程。扩表数组体积单列。', '',
        '| 数据集 | B64 原始数组 KiB | 原 B32 编译训练覆盖 → B64 | 完整进程峰值 RSS GiB |',
        '|---|---:|---:|---:|']
    for ds in DATASETS:
        pool=Path(read(config(ds))['pool_dir']); p=read(pool/'complete.json'); native=read(ROOT/'data'/ds/'complete.json')
        size=sum((pool/k).stat().st_size for k in ('B64.ids.i32','B64.counts.i8'))
        text.append(f'| {NAMES[ds]} | {size/1024:.2f} | {p["covered_B32"]:,} → {p["covered_B64"]:,} | '
                    f'{native["peak_rss_kib"]/2**20:.2f} |')
    text += ['', '## 复核', '',
        f'两遍实际返回逐字节相同。{POINTS*256:,} 条额外原生标量 Top-K 核验及候选池超集检查。旧实验与本轮共有配置，{ok}/{len(legacy)} 组对照的四份载荷均相同。四集计时结束后评分，使用封存 GT 文件的完整 SHA-256 和物理查询行对齐，两路评分逐查询核对。', '',
        '![四集 Recall@1 与完整 QPS](analysis/recall_qps_k1.png)', '',
        '![四集 Recall@100 与完整 QPS](analysis/recall_qps_k100.png)', '',
        '[协议](protocol.md) · [逐点](analysis/points.csv) · [固定召回目标](analysis/targets.csv) · [同 L 救损](analysis/same_L.csv) · [同召回匹配](analysis/matched.csv) · [逐遍计时](analysis/rounds.csv) · [封存](seal.json)', '']
    with (ROOT/'report.md').open('x') as out:
        out.write('\n'.join(text))
    write(ROOT/'state.json',dict(status='COMPLETE_E229',datasets=DATASETS,K=[1,100],formal_points=POINTS,
        formal_batches=BATCHES,qualified_queries=POINTS*256,report='report.md',results=outcome))
    files={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(ROOT.rglob('*'))
           if p.is_file() and '__pycache__' not in p.parts}
    write(ROOT/'seal.json',dict(status='SEALED_E229',files=files))


def audit():
    verify(ROOT/'inputs.json')
    seal=read(ROOT/'seal.json')
    for rel,info in seal['files'].items():
        p=ROOT/rel
        assert p.stat().st_size==info['bytes'] and digest(p)==info['sha256'],rel
    print(seal['status'],len(seal['files']),'files verified')


if __name__=='__main__':
    if 'verify' not in sys.argv:
        main()
    audit()
