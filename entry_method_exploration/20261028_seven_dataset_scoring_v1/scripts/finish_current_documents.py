"""Update current delivery prose; preserve frozen scripts and historical contracts."""
import csv
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
REPO = R.parents[1]
REL = 'entry_method_exploration/' + R.name


def main():
    assert (R / 'reviews/PDF_delivery_update.json').exists()
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip() == '96cf05d5410cf51272048cd1f90b4bb194e23c62'
    rows = list(csv.DictReader((R / 'analysis/candidate_assessment.csv').open()))
    keep = [x for x in rows if x['decision'] == 'RETAIN_EXPLORATORY']
    covered = [x for x in keep if x['existing_B32_dominating_L'] or x['existing_PQ_dominating_L']]
    nondominated = [x for x in keep if x['median_nondominated_in_available_grid'] == 'True']
    scope = (f'相对密集GT10保留的{len(keep)}点中，{len(covered)}点被同窗口已有B32/PQ的实测Recall与中位QPS共同覆盖；'
             f'{len(nondominated)}点未被当前已测方法网格覆盖。B32仅有原四档补全L，没有密集费用匹配的中间L；'
             '未覆盖不能写成优于充分调节预算的B32或全局最优。')
    storage = ('首轮actual timed包的原始字节无损保存在各集raw_packets.tar.zst，原轮次SHA不变；'
               'packet_archive.py可验证并精确还原。trace无损gzip并保留未压缩SHA。'
               f'见[存储合同]({REL}/storage_format_update.md)。')
    for name in ['summary.md', 'spec.md', 's-target.md', 's-experiment.md']:
        p = REPO / name
        s = p.read_text().replace('更新于2026-10-28启动的E191交付。', '更新于2026-10-29；E191于2026-10-28启动。')
        s = s.replace('更新于2026-10-28。', '更新于2026-10-29。', 1)
        if name == 'summary.md':
            s = s.replace('原timed包raw保留，trace无损gzip及原SHA可重放。', storage)
            s = s.replace('## 核验与限制', '## 已有补全参照\n\n' + scope + '\n\n## 核验与限制', 1)
        elif name == 'spec.md':
            s = s.replace('实际timed返回原raw保持，trace为wall外实际主包的全排序重建并保留未压缩SHA；io_data.read_array透明解压重放。',
                          '实际timed原始字节经逐文件SHA往返核验后无损存入raw_packets.tar.zst；packet_archive.py支持验证和精确还原，run_archived_posthoc.py只适配读取，原科学posthoc源码保持。trace为wall外实际主包的全排序重建，gzip保留未压缩SHA。归档与分析不和正式性能并发。')
            needle = '补充身份见[dense freeze](' + REL + '/dense_freeze.json)。'
            s = s.replace(needle, needle + '当前存储合同见[存储修订](' + REL + '/storage_format_update.md)。')
        elif name == 's-target.md':
            s = s.replace('## 下一门（提案，未启动）', scope + '\n\n## 下一门（提案，未启动）', 1)
            s = s.replace('1. 对密集控制后保留的数据/K/L/来源冻结部署配置和费用，',
                          '1. 对密集控制后保留的数据/K/L/来源，先补齐已有B32同窗口的密集费用匹配控制，再冻结部署配置和费用，')
        p.write_text(s)
    p = REPO / 'LOCAL_CODEX_START.md'
    s = p.read_text().replace('2026-10-28启动的E191已完成', 'E191于2026-10-28启动、2026-10-29完成')
    s = s.replace('保留实际timed raw，trace gzip保留原SHA。', storage)
    s = s.replace('可复制接续：', scope + '\n\n可复制接续：', 1)
    p.write_text(s)
    p = REPO / 'experiment_history/191_seven_dataset_scoring_v1.md'
    s = p.read_text().replace('实际返回raw保持，trace无损gzip保留原SHA。',
                              '实际timed返回原始字节无损tar+zstd归档，逐文件SHA往返通过，支持精确还原；trace无损gzip保留原SHA。')
    conclusions = json.loads((R / 'reviews/interpretation.json').read_text())['conclusions']
    s += '\n## 2026-10-29完成时的详细判断\n\n' + '\n\n'.join(conclusions) + '\n\n' + scope + '\n'
    s += '\n[全部已有方法覆盖核对](../' + REL + '/analysis/candidate_assessment.csv) · [存储合同](../' + REL + '/storage_format_update.md)。\n'
    p.write_text(s)
    p = R / 'report_zh.md'
    s = p.read_text().replace('2026-10-28启动；完整单线程', '2026-10-28启动，2026-10-29完成；完整单线程', 1)
    s = s.replace('首轮actual timed包保留raw，后两轮bits/SHA；',
                  '首轮actual timed原始字节无损tar+zstd归档，支持验证及精确还原，后两轮bits/SHA；')
    needle = '## 严重失败、完整恢复与损伤'
    comparison = ('## 已有B32/PQ对照的进一步判断\n\n' + scope + '\n\n'
                  '[逐候选核对](analysis/candidate_assessment.csv) · [全部方法网格覆盖](analysis/all_method_dominance.csv)。'
                  '中位QPS覆盖与三轮范围不重叠另列；三轮计时不等于独立质量样本。\n\n')
    s = s.replace(needle, comparison + needle, 1)
    s += '\n当前归档与还原方式见[存储修订](storage_format_update.md)；原协议的物理raw计划保留历史身份。\n'
    p.write_text(s)
    for name in ['summary.md', 'spec.md', 's-target.md', 's-experiment.md', 'LOCAL_CODEX_START.md']:
        p = REPO / name
        s = p.read_text()
        if name in ['summary.md', 'spec.md']:
            s += '\n新块表末4K不参与本轮拟合或配置选择；旧GT10画像与旧B32仍继承各自合法历史监督，不能说末4K从未参与系统监督。\n'
            p.write_text(s)
    receipt = dict(status='PASS_CURRENT_DELIVERY_DOCUMENTS_UPDATED',
                   completed_local_date='2026-10-29', retained=len(keep), available_B32_or_PQ_covered=len(covered),
                   available_grid_nondominated=len(nondominated),
                   source_script=str(Path(__file__).resolve()),
                   source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   frozen_scientific_scripts_changed=False,
                   time=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (R / 'reviews/current_documents_update.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
