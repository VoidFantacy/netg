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
    roles=read(ROOT.parent/'20261123_b64_far_depth_sweep_v1/configs/roles.json')
    text=['# E243 WebVid B64 多预算遗漏监督', '',
        '保留原 B32 前缀。固定原 B32 前缀。More64 加入更多独立的真实训练向量，仍按 L200 编表。Mixed64 用同样训练向量的 L176、192、208 遗漏联合编表。真实 K100，次序、底库、主图、GT10 路由、原生精算合并固定。', '',
        f'确认窗 3,072 条，训练与校准另用开发窗。确认物理行从 {roles["confirmation_span"][0]} 至 {roles["confirmation_span"][1]} 按冻结清单选择，与开发、E229 诊断及原画像拟合窗精确字节隔离。{POINTS} 点、{BATCHES} 批 CPU15 单线程两遍完整计时。结果均从真实返回评分。', '',
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
    train=read(ROOT/'models/train/roles.json')
    text += ['', '## 离线训练', '',
        f'沿用 {train["original"]:,} 条原训练，加入 {train["extra"]:,} 条按查询字节排重的独立训练。']
    for name in ('more','mixed'):
        c=read(ROOT/'models'/name/'complete.json')
        text.append(f'- {name} 编表 {c["tokens"]:,} 个实际遗漏事件，B32 覆盖 {c["covered_B32"]:,}，扩表覆盖 {c["covered_B64"]:,}，原生编表 {c["seconds"]:.1f} 秒。')
    text.append('')
    text += ['', '## 验证', '', f'{POINTS*256:,} 次额外原生标量 Top-K 全排序核对，两遍包位级一致。逐条核新版候选包含 B32 和 Mixed52 嵌套关系。各法同档路由和画像分数一致。', '',
        '![B32、老 B64、新 B64 Mixed64](analysis/recall_qps.png)', '',
        '[协议](protocol.md) · [训练身份](models/train/roles.json) · [逐点结果](analysis/points.csv) · [目标比较](analysis/targets.csv) · [同 L 救损](analysis/same_L.csv) · [原始两遍](analysis/rounds.csv) · [封存](seal.json)', '']
    (ROOT/'report.md').write_text('\n'.join(text)); write(ROOT/'state.json',dict(status='COMPLETE_E243',points=POINTS,batches=BATCHES,results=stats,report='report.md'))
    files={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    write(ROOT/'seal.json',dict(status='SEALED_E243',files=files))


def audit():
    verify(ROOT/'inputs.json')
    s=read(ROOT/'seal.json')
    for rel,v in s['files'].items():
        p=ROOT/rel; assert p.stat().st_size==v['bytes'] and digest(p)==v['sha256'],rel
    print(s['status'],len(s['files']),'files verified')


if __name__=='__main__':
    if 'verify' not in sys.argv: finish()
    audit()
