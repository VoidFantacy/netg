"""Write the evidence summary, then verify the sealed artifacts."""
import csv
from pathlib import Path
import sys

from drive import DATASETS,ROOT,config,digest,read,verify,write

A=ROOT/'analysis'
NAMES=dict(zip(DATASETS,('COCO','WebVid')))


def table(name):
    with (A/f'{name}.csv').open() as fp:
        return list(csv.DictReader(fp))


def show(row,arm):
    if not row[f'{arm}_L']:
        return '—'
    return f'L{row[f"{arm}_L"]} · {100*float(row[f"{arm}_recall"]):.4f}% · {float(row[f"{arm}_qps"]):,.1f}'


def show_delta(value):
    return f'{float(value):+.2f}%' if value else '—'


def init():
    points=table('points'); targets=table('targets'); pairs=table('same_L')
    stats=read(A/'outcome.json'); parity=table('E227_baseline_parity')
    assert len(points)==80 and len(table('rounds'))==160 and len(targets)==16
    text=['# E228 B64 全精算复测', '',
        '冻结 E226 的 B32/B64 两套表和 SPAN4。三路候选合并去重并排除主返回，按原生 raw-IP 对所有候选精算。两集各 3,072 条真实 K100 查询，20 档 L、80 点、160 批 CPU15 单线程完整计时。每点两遍，使用算术平均 QPS。', '',
        '窗口从物理行号 6144 开始。COCO 取至 9215。WebVid 跳过 2 条与前 6,144 条向量字节重复的记录，顺延至 9217。两集与 E226 正式窗和拟合/校准窗隔离，COCO 核源组身份，WebVid 核精确向量及官方训练来源，另比对全部 20,000 条归档画像拟合向量。此窗口来自历史公共查询。', '',
        'B64 在两集的全部同 L 测点提高召回，完整吞吐同 L 中位数分别下降 2.77% 和 2.90%。两集把 L 调低到同一召回目标后，COCO 7/7、WebVid 5/6 个双边达标目标的 B64 均值更快，慢遍仍快分别 6/7 和 4/6。B64 在每集 16 个同召回重叠点都位于 B32 折线右侧，折线 QPS 差中位数 +1.64% 和 +2.27%。这支持将 B64 作为已测两集 K100 的条件配置。', '',
        '## 实测达标点', '',
        '每臂独立取同一固定 Recall@100 目标的最快完整 QPS。表内列出实际召回和完整 QPS。慢遍列比较 B64 的慢遍与 B32 的快遍。', '',
        '| 数据集 | Recall@100 目标 | GT10+B32（L / 实际召回 / QPS） | GT10+B64（L / 实际召回 / QPS） | QPS 差 | 慢遍对快遍 |',
        '|---|---:|---:|---:|---:|---:|']
    for r in targets:
        text.append(f'| {NAMES[r["dataset"]]} | {float(r["target_pct"]):.1f}% | {show(r,"B32")} | {show(r,"B64")} | '
                    f'{show_delta(r["QPS_delta_pct"])} | {show_delta(r["slow_vs_fast_pct"])} |')
    text += ['', 'WebVid 72.0% 目标两臂均落在本轮下限 L168，B64 的完整 QPS 差为 −2.97%。这个目标的更小 L 留待另测。', '', '## 全网格比较', '',
        '| 数据集 | 实测目标两边均达标 | B64 用更小 L | B64 均值更快 | B64 慢遍仍更快 | B64 在 B32 折线右侧 |',
        '|---|---:|---:|---:|---:|---:|']
    for ds in DATASETS:
        s=stats[ds]
        text.append(f'| {NAMES[ds]} | {s["targets_both"]}/8 | {s["targets_smaller_L"]}/{s["targets_both"]} | '
            f'{s["targets_faster"]}/{s["targets_both"]} | {s["targets_slow_faster"]}/{s["targets_both"]} | {s["line_faster"]}/{s["line_both"]} |')
    text += ['', '折线结论限 B32 和 B64 召回重叠范围内的描述性插值。两遍速度差用于检查方向和波动。', '',
        '## 同 L 候选和费用', '',
        '| 数据集 | 锚点 | B32 / B64 平均精算数 | B64 召回差 | 正确成员救回 / 损伤 | B64 全链路耗时增量 |',
        '|---|---:|---:|---:|---:|---:|']
    for ds in DATASETS:
        for l in ('184','200'):
            b,t=(next(p for p in points if p['dataset']==ds and p['L']==l and p['method']==m) for m in ('B32','B64'))
            row=next(p for p in pairs if p['dataset']==ds and p['L']==l)
            text.append(f'| {NAMES[ds]} | L{l} | {float(b["mean_exact_256"]):.1f} / {float(t["mean_exact_256"]):.1f} | '
                f'{float(row["recall_delta_pp"]):+.4f} 个百分点 | {row["rescued"]} / {row["lost"]} | {float(row["wall_delta_us"]):+.2f} μs/query |')
    sizes=[]
    for ds in DATASETS:
        pool=Path(read(config(ds))['pool_dir'])
        sizes.append(sum((pool/n).stat().st_size for n in ('B64.ids.i32','B64.counts.i8'))/1024)
    text+=['', f'精算数来自每个正式点的前 256 条独立资格回放。两集扩表 ID 和计数实际各占 {sizes[0]:.2f} / {sizes[1]:.2f} KiB，沿用 E226 表文件。扩表保留原 B32 前缀。', '', '## 复核', '',
        '两遍正式返回逐字节相同。正式资格独立标量全排序检查 20,480 条，核 B64 去重候选逐查询覆盖 B32。以 E226 原查询窗的 12 组两臂前 256 条返回核载荷一致。两集全部计时后按物理行绑定官方 GT100，Recall 使用 Python 集合和 NumPy 各自核验。', '']
    for ds in DATASETS:
        refs=[p for p in parity if p['dataset']==ds]
        exact=sum(all(v==p['shared_queries'] for key,v in p.items() if key.endswith(('.i32','.f32'))) for p in refs)
        text.append(f'{NAMES[ds]} 对 E227 的公共物理查询行，{exact}/{len(refs)} 个可比 L 的四份 B32 返回载荷全相同。')
    text += ['', '![原版 GT10+B32 与全精算 B64](analysis/recall_qps.png)', '',
        '[协议](protocol.md) · [逐点](analysis/points.csv) · [固定目标](analysis/targets.csv) · [按点匹配](analysis/matched.csv) · [原始两遍](analysis/rounds.csv) · [同 L 救损](analysis/same_L.csv) · [封存](seal.json)', '']
    with (ROOT/'report.md').open('x') as fp:
        fp.write('\n'.join(text))
    write(ROOT/'state.json',dict(status='COMPLETE_E228',K=100,formal_points=80,formal_batches=160,
        qualified_queries=20480,E226_prefix_parity_points=12,native_production_control='GT10+B32',results=stats,
        report='report.md',figure='analysis/recall_qps.png'))
    files={str(f.relative_to(ROOT)):dict(bytes=f.stat().st_size,sha256=digest(f)) for f in sorted(ROOT.rglob('*'))
           if f.is_file() and '__pycache__' not in f.parts}
    write(ROOT/'seal.json',dict(status='SEALED_E228',files=files))


def verify_seal():
    verify(ROOT/'inputs.json')
    seal=read(ROOT/'seal.json')
    for rel,item in seal['files'].items():
        f=ROOT/rel
        assert f.stat().st_size==item['bytes'] and digest(f)==item['sha256'],rel
    print(seal['status'],len(seal['files']),'files verified')


if __name__=='__main__':
    if 'verify' not in sys.argv:
        init()
    verify_seal()
