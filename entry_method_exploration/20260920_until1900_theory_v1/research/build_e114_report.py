from pathlib import Path
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
os.sched_setaffinity(0,{15})
import json,csv,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
TB=Path(__file__).resolve().parents[1];R=TB/'stages/e114_terminal_peaks'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
assert not (R/'report.md').exists();v=read(R/'reviews/numeric_verification.json');assert v['status']=='PASS'
summary=read(R/'results/summary.json');methods=list(csv.DictReader((R/'results/methods.csv').open()));pairs=list(csv.DictReader((R/'results/pairs.csv').open()))
cost=[]
for s in summary:
    rr=list(csv.DictReader((R/'results'/s['dataset']/'query_peaks.csv').open()))
    independent_peaks=sum(int(x['query']) in range(0,4096,256) for x in rr)
    cost.append(dict(dataset=s['dataset'],original_field_reference_inner_products=s['reference_inner_products'],
        original_semantics='Logical neighbor, peak and GT references per unique query/peak; GT term counted per peak',
        actual_primary_dot_products=s['out_edges_checked']+s['unique_query_peaks']+s['n'],
        cached_GT_duplicate_count=s['unique_query_peaks']-s['n'],
        independent_fsum_dot_products=s['independent_edges']+independent_peaks,
        interpretation='Main loop actually computes GT score once per query, not once per peak; no rerun or numerical result change'))
dump(R/'reviews/distance_count_clarification.json',dict(status='CORRECTED_ACCOUNTING_ONLY',
    original_numeric_summary_preserved=True,no_reexecution=True,NSG_calls=0,datasets=cost))
(R/'figures').mkdir();plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42})
fig,axes=plt.subplots(1,2,figsize=(11.8,4.2));labels=['WebVid','Yandex'];y=np.arange(2)
same=np.array([s['all_eight_same_terminal_ID_pct'] for s in summary]);ax=axes[0]
ax.barh(y,same,color='#477caa',label='Same terminal ID');ax.barh(y,100-same,left=same,color='#d6dce3',label='Different terminal IDs')
for i,z in enumerate(same):ax.text(z/2,i,f'{z:.1f}%',ha='center',va='center',color='white',weight='bold')
ax.set_title('All queries: eight preset entry policies',loc='left',fontsize=11);ax.set_yticks(y,labels);ax.invert_yaxis();ax.legend(loc='lower left',bbox_to_anchor=(0,-.38),frameon=False,fontsize=9)
ax=axes[1];arr=[]
for s in summary:
    failed=s['default_failures'];rescued=s['any_preset_method_hits']-(s['n']-failed)
    arr.append([s['default_failed_all_eight_same_terminal_ID'],failed-s['default_failed_all_eight_same_terminal_ID']-rescued,rescued])
arr=np.asarray(arr);percent=arr/np.array([s['default_failures'] for s in summary])[:,None]*100
left=np.zeros(2)
for j,(name,color) in enumerate([('Same incorrect peak','#6f7d8d'),('Different peaks; all miss','#c5a070'),('Some preset policy hits','#4b9578')]):
    ax.barh(y,percent[:,j],left=left,label=name,color=color)
    for i in range(2):ax.text(left[i]+percent[i,j]/2,i,f'{percent[i,j]:.1f}%',ha='center',va='center',fontsize=9,color='white' if j!=1 else '#202020')
    left+=percent[:,j]
ax.set_title('Default failures: where the eight policies end',loc='left',fontsize=11);ax.set_yticks(y,[f'WebVid (n={summary[0]["default_failures"]})',f'Yandex (n={summary[1]["default_failures"]})']);ax.invert_yaxis();ax.legend(loc='lower left',bbox_to_anchor=(0,-.48),frameon=False,fontsize=9)
for ax in axes:
    ax.set_xlim(0,100);ax.set_xticks([0,25,50,75,100]);ax.set_xlabel('Queries (%)');ax.spines[['top','right']].set_visible(False)
fig.suptitle('Existing true K1 / L128 results · 4096 queries per dataset',x=.08,ha='left',fontsize=13)
fig.subplots_adjust(left=.075,right=.985,top=.81,bottom=.36,wspace=.6)
fig.savefig(R/'figures/terminal_peaks.png',dpi=180,bbox_inches='tight');fig.savefig(R/'figures/terminal_peaks.pdf',bbox_inches='tight');plt.close(fig)
table=[]
for s in summary:
    name='WebVid' if s['dataset'].startswith('web') else 'Yandex';table.append(f"| {name} | {s['unique_query_peaks']:,} | {s['out_edges_checked']:,} | {s['violating_unique_query_peaks']} | {s['all_eight_same_terminal_ID_pct']:.4f}% | {s['default_failed_all_eight_same_terminal_ID']}/{s['default_failures']} |")
pairtable=[]
for r in pairs:
    if (r['method_a'],r['method_b']) not in [('NSGFixed1','DefaultANN'),('UnitHub1','DefaultANN'),('GT11','GT101'),('GT101','GT103')]:continue
    name='WebVid' if r['dataset'].startswith('web') else 'Yandex'
    gain=int(r['b_rescues_a']);harm=int(r['b_harms_a']);pairtable.append(f"| {name} | {r['method_a']} → {r['method_b']} | {gain} | {harm} | {100*(gain-harm)/4096:+.4f} | {100*int(r['same_peak_ID'])/4096:.4f}% |")
text='''# E114：入口改变与搜索终点

2026-09-20。**TERMINAL_LOCAL_OPTIMA_VERIFIED**：从当前完整搜索语义推出终点的局部闭合性质，并在全部预定旧K1/L128返回中得到支持。Web/Y八种入口策略约79.7%/90.6%的query落到同一节点；默认失败中两集均约52.6%八种策略落到同一错误节点。没有新的性能候选或训练分支，默认保持。

## 理论对应什么

在固定得分、完整展开最终候选池、K≤L的条件下，返回topK与其全部出邻居合并后不会产生严格更高的topK得分。K1的特例是返回点没有严格更高分出邻居。证明只依赖池维护与终止语义，见[推导](research.md)；不是NSG图天然具有全局单调性的证明。

这解释了入口的一个作用：不同初始化可能进入不同搜索终点。当前实验不直接测完整吸引域；也不从“同终点”推断相同K100、路径、NDC或wall。原图的局部最优点可能多个，几何相关性与到达正确终点仍是不同目标。

## 已有结果的核验

全部E107两集4096条已曝光query、8方法、真实K1/L128，按query去重相同终点后扫描全部有效出邻居。使用原float32向量的float64内积与保守舍入误差界，全部非同向量出边均可确认正差，没有负差或需精确有理数复核的不确定边。同向量邻居保留为并列。原16点R1/失败数完全恢复。

| 数据 | 不同query/终点 | 出邻接检查 | 有更高分邻居的终点 | 八方法同终点query | 默认失败且八方法同终点 |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(table)+'''

终点局部稳定半径仅保证“这个节点仍是局部最优”。默认方法半径中位数Web约0.02985、Y约0.02881；它不保证GT、入口或整个搜索输出对同样的query扰动稳定，也不作为新路由特征。全部方法及分位保留于[原统计](results/methods.csv)。

![终点与默认失败的分解](figures/terminal_peaks.png)

## GT10的增益仍包含收益和损伤

下表完全重算旧真实返回，B相对A的增益减损伤除以4096；只解释K1/L128，不是新的QPS或全预算选择。

| 数据 | A → B | B恢复的query | B损伤的query | 净R1变化pp | 同终点ID |
|---|---|---:|---:|---:|---:|
'''+ '\n'.join(pairtable)+'''

默认相对固定单入口的净增益来自少量查询终点变好减去变坏，不是所有查询一致改善。GT10相对GT1的增量较小且两集不一致；这些匹配控制不能把系统总增益全归因于十目标平均。

八方法旧结果中，只要任一个命中就取该答案的特权联合R1为Web81.8848%、Y93.8721%；相对默认额外269/133条可恢复。但它需要真值选择且混合了不同入口/路由策略，不能部署，也不是全H上界。Web742、Y251条在八种既有策略下全部失败；其中默认失败且八方法同终点为532/202条，不能把这些查询选出另训或推断其不可修复。

## 成本、修正与边界

0新NSG/ANN/GT/图/梯度或画像训练/QPS。独立分析4.843秒，外层进程4.971秒，最大RSS约5.288GiB。按既有图memmap读取约190109条有效出边；预定16query/集另用math.fsum核验818条边，最大差2.23e-16以内。原float32返回与重算内积分数最大差小于1e-7，未改变任何返回或原ID命中规则。

首个统计JSON的reference_inner_products按每个query/终点重复计了GT引用，属于逻辑引用数；实际GT内积每query只算一次。核算更正为主循环Web70032、Y137844次内积，独立fsum另341/514次；原JSON/源码保留，未重跑或改数值结果。[计数说明](reviews/distance_count_clarification.json)。

E114只验证终点性质与有限已测方法的关系，未检验新策略在未见query上的预测能力。K100闭合是条件推导，本次数值扫描只核验K1。底图只核对原size/mtime及已有身份链，不声称本次重新全文件SHA扫描；56项query/GT/旧结果身份与冻结源码/报告逐项核验。

[协议](protocol.md) · [配置](config.locked.json) · [全部56个方法对](results/pairs.csv) · [独立数值核验](reviews/numeric_verification.json) · [执行记录](reviews/job.json) · [PNG](figures/terminal_peaks.png) · [PDF](figures/terminal_peaks.pdf)。
'''
(R/'report.md').write_text(text)
dump(R/'reviews/report_build.json',dict(status='BUILT_PENDING_VISUAL_AND_CLOSEOUT',source=ident(__file__),
    inputs=[ident(R/'results'/p) for p in ['summary.json','methods.csv','pairs.csv']],report=ident(R/'report.md'),
    figures=[ident(p) for p in (R/'figures').iterdir()],new_searches=0))
print(json.dumps(dict(report=str(R/'report.md'),figures=str(R/'figures'),count_correction=cost),indent=2))
