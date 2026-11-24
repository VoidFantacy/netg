"""Publish the per-window results and seal the original raw packets."""
import csv
import sys

from drive import ARMS,BATCHES,POINTS,ROOT,WINDOWS,digest,read,verify,write


def table(f):
    with (ROOT/'analysis'/f'{f}.csv').open() as fp:
        return list(csv.DictReader(fp))


def float_text(r,key,fmt):
    return format(float(r[key]),fmt) if r[key] else '—'


def finish():
    points=table('points'); pairs=table('same_L'); targets=table('targets'); stats=read(ROOT/'analysis/outcome.json')
    assert len(points)==POINTS and len(table('rounds'))==BATCHES
    roles=read(ROOT/'configs/roles.json')
    text=['# E237 WebVid B64 异源验证与高召回', '',
        '冻结 E243 的 More64 与 Mixed64，以及 E234 单分数门。比较新训练监督及按查询分配的异源性能。真实 K100，次序、底库、主图、GT10 路由、原生精算合并固定。', '',
        f'取 WebVid validation 真实查询 3,072 条，物理行 {roles["physical_span"][0]} 至 {roles["physical_span"][1]}，排除 {roles["excluded"]} 条。与原拟合、E243 扩训及公共测试按向量字节排重。{POINTS} 点、{BATCHES} 批 CPU15 单线程两遍完整计时。评分使用相应 exact raw-IP GT。', '' ,
        '## L196 打开第三路尾部', '',
        '| 窗口 | 配置 | 实际 Recall@100 | 完整 QPS | 平均精算数 |',
        '|---|---|---:|---:|---:|']
    for w in WINDOWS:
        for a in ARMS:
            r=next(p for p in points if (p['window'],p['method'],p['L'])==(w,a,'196'))
            text.append(f'| {w} | {a} | {float_text(r,"recall_pct",".4f")}% | {float_text(r,"qps",",.1f")} | {float_text(r,"exact_mean",".2f")} |')
    text += ['', '## 75.5% 召回目标', '',
        '各法使用有限网格的最快实测达标点。慢遍对快遍只描述速度波动。', '',
        '| 窗口 | 配置 | L | 实际召回 | 完整 QPS | 比老 B64 | 慢遍比老 B64 快遍 |',
        '|---|---|---:|---:|---:|---:|---:|']
    for w in WINDOWS:
        for a in ARMS:
            ctrl='B32' if a=='B64-old' else 'B64-old'
            q=next(d for d in targets if (d['window'],d['method'],d['control'],float(d['target_pct']))==(w,a,ctrl,75.5))
            diff='—' if a=='B64-old' else float_text(q,'qps_delta_pct','+.2f')+'%'
            slow='—' if a=='B64-old' else float_text(q,'slow_vs_fast_pct','+.2f')+'%'
            text.append(f'| {w} | {a} | {q["a_L"] or "—"} | {float_text(q,"a_recall_pct",".4f")}% | '
                        f'{float_text(q,"a_qps",",.1f")} | {diff} | {slow} |')
    text += ['', '## 验证', '', f'{POINTS*256:,} 次额外原生标量 Top-K 全排序核对，两遍包位级一致。逐条核新版候选包含 B32，单分数门选原 B64 子集。各法同档路由和画像分数一致。', '',
        '![B32、老 B64、新 B64 Mixed64](analysis/recall_qps.png)', '',
        '[协议](protocol.md) · [逐点结果](analysis/points.csv) · [目标比较](analysis/targets.csv) · [同 L 救损](analysis/same_L.csv) · [原始两遍](analysis/rounds.csv) · [封存](seal.json)', '']
    (ROOT/'report.md').write_text('\n'.join(text)); write(ROOT/'state.json',dict(status='COMPLETE_E237',points=POINTS,batches=BATCHES,results=stats,report='report.md'))
    files={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    write(ROOT/'seal.json',dict(status='SEALED_E237',files=files))


def audit():
    verify(ROOT/'inputs.json')
    s=read(ROOT/'seal.json')
    for rel,v in s['files'].items():
        p=ROOT/rel; assert p.stat().st_size==v['bytes'] and digest(p)==v['sha256'],rel
    print(s['status'],len(s['files']),'files verified')


if __name__=='__main__':
    if 'verify' not in sys.argv: finish()
    audit()
