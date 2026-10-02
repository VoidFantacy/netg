"""Finalize report-only session 14. No native libraries, ANN, fit, or browser."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import time

O = Path(__file__).resolve().parents[1]
C = O.parent
R = C.parents[1]
P = C / 'session13_report_v1'

def read(path):
    return json.loads(path.read_text())

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def identity(path):
    return dict(path=str(path), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def check(records, base=None):
    for row in records:
        p = Path(row['path'])
        if not p.is_absolute():
            assert base is not None
            p = base / p
        actual = identity(p)
        assert actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'], str(p)

assert not (O / 'final_seal.json').exists()
check(read(O / 'input_freeze.json')['files'])
post = read(P / 'reviews/postseal_additions_seal.json')
check(post['files'], P)
pdf = read(O / 'reviews/review_208_pdf_visual_complete.json')
assert identity(P / 'report.pdf')['sha256'] == pdf['pdf_sha256']
assert pdf['pages'] == 6 and pdf['actual_browser_returncode'] == 0
rollover = read(O / 'reviews/review_211_session13_postseal_rollover14.json')
assert rollover['old_exit_code'] == 0 and rollover['old_pid_gone']
assert rollover['new_session'] == 14 and rollover['old_ended_at'] < rollover['new_started_at']
assert (R / 'spec.md').read_bytes() == (O / 'source_before/spec.md').read_bytes()
now = time.time()
local = datetime.datetime.fromtimestamp(now, datetime.timezone(datetime.timedelta(hours=8))).isoformat()
assert now < 1789303200
handoff = f'''# 第14会话安全交接：交付核验完成，整日目标保持未完成

记录时间 {local}；本会话20:40安全边界，整日21:00截止。唯一串行写入者，无子代理/第二CLI，本会话没有新训练、ANN、HNSW、NSG、构图、GT、选型或QPS。所有研究阶段已完成，无待恢复实验。

[交付入口](session14_closeout_v1/delivery.md) · [中文报告及四图](session13_report_v1/report.md) · [六页PDF](session13_report_v1/report.pdf) · [401失败query交互浏览](session13_report_v1/report.html)。最终仍E94双集各2000、五L五轮、50点250wall；Web组合相对compact有修复但仍不及匹配P，Y低L正/高L损伤，默认不替换。

本会话完整读AGENTS/四主文档、相关历史82/83/84及协议/配置/源码/结果。第13只读resume在实际工具返回exit0后确认66条主seal通过；本次检查其4条postseal记录及当前交付身份。监督208已实际逐页查看六页PDF（实际PDF字节SHA一致），205/206已穷举桌面/手机401query×五L和两种下载；这些是继承审查，本会话未重跑浏览器/PDF或原始数值验收。监督211证明第13实际exit0/turn.completed/PID消失后才启动第14；本会话自身宿主CLI退出须在返回后由监督另核验。

交接核验v1因旧postseal相对路径假设失败，v2因closeout文件生成前检查其链接失败；两版源码/冻结/失败与v2中间state/handoff保留，v3仅纠正路径解析和检查顺序，0实验重跑。详见session14_closeout_v1/reviews/execution_correction*.json。

新增交付清单、记录85及根文档同步；source_before/root_after齐全。历史83/84、E92/E93/E94、原第13报告/图/HTML/PDF与其seal不改；spec接口/计量不变，字节保持。PDF新证据通过补充记录表达，不静默重写旧报告。

当天累计6854176 NSG/17820080 HNSW/360普通build不变；E94为700800/560000、994.213s操作/695.047s纯wall，50点250wall。旧开发220点1100wall为四个不同批次。完整训练/GT成本未知项不补零；本次交付核验耗时不计QPS。P-fit含旧train/monitor，aux/cal/audit历史使用，动作接受反馈算训练；E34历史validation最终反馈不回流，held-out未开。

本阶段新输出预算2MiB，另72MiB保留、free floor6.45GiB；实际输出/磁盘/命名空间扫描见[closeout](session14_closeout_v1/closeout.json)。本会话无背景任务，无pending原生工具；最后只读检查返回终态后即可结束。沙箱只能看到本命名空间，不能据此冒称已验证宿主CLI退出。

下一命令仅检查本次交付封存与状态，不启动研究、重新评分或浏览器：

```bash
python3 -B entry_method_exploration/20260913_until2100_v1/session14_closeout_v1/src/resume_inspect.py
```

再读最新supervisor_notes，由监督者在21:00前向用户提交上述完整材料并处理整日状态。无需恢复旧runner、再次选型、重测曲线或重复已通过审查。后续若另开研究，仅沿[机制说明](session13_report_v1/mechanism_note.md)中的有效动作支持、完整并图交互、旧收益丢失和跨来源迁移重新定协议/数据角色/预算；不能按最终失败例调参或自动扩大网格。本会话day_goal_complete=false，未把安全交接当作整日目标完成。
'''
(C / 'handoff_session14.md').write_text(handoff)
state = read(C / 'state.json')
assert (state['total_new_NSG'], state['total_HNSW'], state['total_builds'], state['final_validation_QPS_points']) == (6854176, 17820080, 360, 50)
assert not any(state[k] for k in ['native_pids', 'offline_pids', 'pending_tool_sessions'])
state.update(status='SESSION14_COMPLETE_SAFE_HANDOFF', session14_status='COMPLETE_DELIVERY_SAFE_HANDOFF',
             session_safe_boundary_epoch=now, session_safe_boundary_local_time=local,
             session14_safe_boundary_epoch=now, session14_pending_tasks=[], day_goal_complete=False,
             free_GiB=shutil.disk_usage('/data').free / 2**30,
             handoff=str(C / 'handoff_session14.md'), session14_delivery=str(O / 'delivery.md'),
             session14_pdf_verification='Inherited supervisor208 actual six-page PDF review; SHA matched in session14',
             supervisor_review_through='211: actual session13 exit and serial session14 start; 208 PDF six pages, 210 seals',
             next_action='Run python3 -B entry_method_exploration/20260913_until2100_v1/session14_closeout_v1/src/resume_inspect.py; read handoff_session14/latest supervisor notes; final day delivery only. No pending experiment.')
write(C / 'state.json', state)
for name in ['AGENTS.md', 'summary.md', 'spec.md', 's-target.md', 's-experiment.md', 'experiment_history/README.md']:
    out = O / 'root_after' / name
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(R / name, out)
shutil.copy2(C / 'state.json', O / 'root_after/state.json')
shutil.copy2(C / 'handoff_session14.md', O / 'root_after/handoff_session14.md')
assets = [P / n for n in ['report.md', 'report.pdf', 'report.html', 'mechanism_note.md']]
assets += sorted((P / 'figures').glob('*'))
write(O / 'delivery_manifest.json', dict(created_at=now, files=[identity(p) for p in assets],
      final_points=50, timing_batches=250, failure_queries=401, complete_failure_cells=10730,
      inherited_browser_reviews=[205, 206], inherited_PDF_review=208, new_ANN=0,
      source_final=C.name + '/stage35_final_comparison_v1', day_goal_complete=False))
docs = [R / n for n in ['summary.md', 's-target.md', 's-experiment.md', 'experiment_history/README.md', 'experiment_history/85_campaign_delivery_readiness.md']]
docs += [C / 'handoff_session14.md', O / 'delivery.md', O / 'protocol.md']
links = 0
link_targets = []
for doc in docs:
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', doc.read_text()):
        target = target.split('#', 1)[0]
        if not target or '://' in target:
            continue
        resolved = (doc.parent / target).resolve()
        link_targets.append(resolved)
        if resolved != O / 'closeout.json':
            assert resolved.exists(), (str(doc), target)
        links += 1
diff = subprocess.run(['git', 'diff', '--no-index', '--check', str(O / 'source_before/summary.md'), str(R / 'summary.md')], capture_output=True, text=True)
assert diff.returncode in [0, 1] and not diff.stdout and not diff.stderr, diff.stdout + diff.stderr
processes = subprocess.check_output(['ps', '-eo', 'pid,ppid,comm'], text=True)
(O / 'reviews/processes.txt').write_text(processes)
used = sum(p.stat().st_size for p in O.rglob('*') if p.is_file())
free = shutil.disk_usage('/data').free
# Include external new handoff/card and conservatively budget another 64KiB of final metadata.
new_external = (C / 'handoff_session14.md').stat().st_size + (R / 'experiment_history/85_campaign_delivery_readiness.md').stat().st_size
assert used + new_external + 65536 < 2 * 2**20
assert free - 72 * 2**20 - 65536 > 6.45 * 2**30
write(O / 'closeout.json', dict(status='COMPLETE_DELIVERY_SAFE_HANDOFF', epoch=time.time(),
      session_deadline=1789303200, deadline_met_at_closeout=time.time() < 1789303200,
      day_goal_complete=False, new_training=0, new_NSG=0, new_HNSW=0, new_builds=0, new_GT=0, new_QPS=0,
      original_main_seal_check='66 identities checked by actual session13 resume command; exit0',
      newly_checked_postseal_records=len(post['files']), local_links_checked=links,
      report_identity_files=len(assets), spec_unchanged=True, scientific_results_unchanged=True,
      output_bytes_before_seal=used, new_external_bytes=new_external, output_cap_bytes=2 * 2**20,
      free_GiB=free/2**30, free_after_reserve_GiB=(free-72*2**20)/2**30,
      pending_experiment_tools=[], pending_background_tasks=[],
      process_scope='Current sandbox namespace only; no native/fit/browser tasks launched in session14. Host CLI exit awaits supervisor after final reply.',
      closeout_tool_exit_requires_terminal_return=True,
      inherited_GT_training_total_seconds=None, report_operation_seconds_not_QPS=time.time()-now))
assert all(p.exists() for p in link_targets), [str(p) for p in link_targets if not p.exists()]
files = sorted(p for p in O.rglob('*') if p.is_file())
files += [C / 'handoff_session14.md', R / 'experiment_history/85_campaign_delivery_readiness.md']
write(O / 'final_seal.json', dict(created_at=time.time(), files=[identity(p) for p in files],
      mutable_root_policy='Frozen root_after snapshots; live roots and campaign state may evolve', day_goal_complete=False))
print(json.dumps(dict(status='PASS_SESSION14_CLOSEOUT', seal_records=len(files), links=links,
      free_GiB=free/2**30, day_goal_complete=False), ensure_ascii=False))
