from shared import *
import re
threads(8)
assert not (O/'reviews/final_artifact_freeze.json').exists()
roots=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']
old=read(C/'reviews/yesterday_freeze_initial.json')
for x in old['files']:
    p=Path(x['path']);f=C/'source_before'/p.name if p.parent==R and p.name in roots else p
    assert sha(f)==x['sha256'],str(f)
files=[R/x for x in roots]+[R/'experiment_history/49_fixed_action_support.md',O/'report.md',O/'protocol.md']
links=0
for p in files:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' in target or target.startswith('#'):continue
        assert (p.parent/target.split('#')[0]).exists(),(str(p),target);links+=1
snap=O/'reviews/root_after';snap.mkdir()
for f in roots:shutil.copy2(R/f,snap/f)
shutil.copy2(R/'experiment_history/49_fixed_action_support.md',snap/'history49.md')
assert all(j['status']=='COMPLETE' for j in read(O/'logs/jobs.json'))
dump(O/'reviews/closeout.json',dict(status='PASS',epoch=time.time(),verified_historical_freeze_files=len(old['files']),checked_local_links=links,
     graphs_visually_checked='support_and_transfer_v2.png',native_jobs_complete=True,remaining_native_pids=[],
     index_repair='Initial closeout caught live history README change; original bytes restored, attempted change preserved in reviews; E60 indexed in s-experiment instead.',scope='E60 stage only, daily goal active'))
freeze=[identity(p) for p in sorted(O.rglob('*')) if p.is_file()]
dump(O/'reviews/final_artifact_freeze.json',dict(status='COMPLETE_E60_FROZEN',epoch=time.time(),files=freeze,
     root_policy='Only saved root_after snapshot is frozen; live roots can evolve in next authorized stage'))
s=read(C/'state.json');s.update(status='E60_COMPLETE_E61_PREPARING',native_pids=[],stage1_status='STOP_SAME_LOCAL_ACTION_CONTINUOUS_EXPANSION',stage1_NSG=17830,
     next_action='Freeze distinct missing-GT-member profile reconstruction protocol after E33 baseline cache provenance check',day_goal_complete=False);dump(C/'state.json',s)
(C/'handoff.md').write_text('''# 2026-09-13 campaign阶段交接

E60完成封存，双集支持0/40，原J+辅助约束全部no-op，不扩大同类连续训练。实际17830 NSG/660640 HNSW/322build；659488集合评分、576三路parity通过。所有native已退出，当前无遗留PID。根四文档及历史49同步；E60冻结引用root_after，后续根文档可合法继续更新。昨日history README恢复原字节，E60只在根s-experiment登记。

输入角色：P-fit router_train10000:30000含旧train4096/monitor1024；辅助旧cal0:1024用于动作选择训练诊断，迁移旧audit1024:2048只描述规则、但历史已暴露，本轮又使用。Fast30K曾使用全部router_train，不宣称其余行为全新。E34最终validation不进入本轮输入或选择。

WebVid9个辅助正动作均train-J负：7个训练命中受损、2个训练命中不变而其它项负；Yandex无辅助正动作。门空不能泛化为全空间不可兼容。完整证据见stage1_support_v1/report.md及results/actions.csv。

当前准备第二个独立阶段：完整fit20K的冻结基线遗漏GT10成员驱动画像聚合，固定小强度和同query同遗漏数量的随机目标对照。已找到E33全20K原始基线缓存，正在核对复用身份。该阶段还未启动，不能执行旧E53/当天旧runner继续扫描。下一命令将随新协议/prepare实际实现写入本文件。

复查E60可读：cat entry_method_exploration/20260913_until2100_v1/stage1_support_v1/results/gate.json。

资源起点7.984GiB空余，阶段限制384MiB、free>=7GiB，不删除历史。当前会话最迟10:15安全交接；全天目标未完成，20:00训练停止/20:40新增查询停止/21:00交付窗口保留。
''')
print('E60_FROZEN',len(freeze),'files; links',links,'freeGiB',shutil.disk_usage('/data').free/2**30)
