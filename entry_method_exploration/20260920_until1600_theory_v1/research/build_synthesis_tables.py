import csv,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
rows=list(csv.DictReader((R/'stages/e108_unit_hub_online/results/metrics.csv').open()))
table=['| 数据 | K | 原GT10默认 | 单位hub小图 |','|---|---:|---:|---:|']
selected=[]
for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
 for k in ['1','100']:
  vals=[]
  for method in ['GT10Default','UnitHub']:
   matches=[x for x in rows if x['dataset']==ds and x['K']==k and x['L']=='128' and x['method']==method];assert len(matches)==1
   x=matches[0];selected.append(x);vals.append(f"{100*float(x['recall']):.4f} / {float(x['mean_qps']):.2f} / {x['failed']}")
  table.append(f"| {'WebVid' if ds.startswith('web') else 'Yandex'} | {k} | "+' | '.join(vals)+' |')
stages=[];costtable=['| 阶段 | 真实NSG | 含加载的搜索进程秒 | 其它主要增量 |','|---|---:|---:|---|']
for st in sorted((R/'stages').iterdir()):
 audit=read(st/'reviews/completion_audit.json');jobs=read(st/'reviews/jobs.json')
 search=sum(j['seconds'] for j in jobs if j['kind'] in ['smoke','main','formal'])
 auxiliary=sum(j['seconds'] for j in jobs if j['kind'] not in ['smoke','main','formal'])
 stages.append(dict(stage=st.name,NSG_calls=audit['NSG_calls'],search_process_seconds=search,other_recorded_process_seconds=auxiliary,max_rss_gib=audit['max_rss_gib'],jobs_source=str((st/'reviews/jobs.json').resolve()),jobs=jobs,audit_source=str((st/'reviews/completion_audit.json').resolve()),definitions='Search process wall includes loading, smoke/count, and output checks. Other process wall is compile/prepare/graph/topology; Python analysis and orchestration are not included in either sum.'))
 label=st.name.split('_')[0].upper();extra={'E107':'初始化因素与2次合成反例','E108':'4小图；54配置/162轮wall','E109':'fit完美代理，不训练','E110':'仅首展开；失败编译另2.02秒','E111':'约17.81秒图派生进程，0搜索'}[label]
 costtable.append(f"| {label} | {audit['NSG_calls']:,} | {search:.2f} | {extra} |")
assert sum(x['NSG_calls'] for x in stages)==2797056
(R/'results').mkdir(exist_ok=True)
ledger=dict(created_unix=time.time(),NSG_calls=sum(x['NSG_calls'] for x in stages),synthetic_calls=6,search_process_seconds=sum(x['search_process_seconds'] for x in stages),stages=stages,additional_synthetic=read(R/'research/graph_dependence_v1/complete.json'),initial_order_diagnostic=read(R/'research/initial_seed_order_v1/complete.json'),failed_compile_seconds=2.017575263977051,historical_input_cost='Inherited historical GT/base/NSG/profile cost is not zero and is not re-estimated here.')
(R/'results/cost_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(R/'results/online_L128.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
p=R/'report.md';text=p.read_text();assert text.count('<!-- ONLINE_TABLE -->')==text.count('<!-- COST_TABLE -->')==1
p.write_text(text.replace('<!-- ONLINE_TABLE -->','\n'.join(table)).replace('<!-- COST_TABLE -->','\n'.join(costtable)))
print(json.dumps(dict(NSG_calls=ledger['NSG_calls'],synthetic_calls=6,search_process_seconds=ledger['search_process_seconds'],online_rows=len(selected)),indent=2))
