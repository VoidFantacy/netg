from pathlib import Path
import csv,json,time,hashlib
import numpy as np
O=Path(__file__).resolve().parents[1];C=O.parent;F=C/'stage35_final_comparison_v1';t=time.monotonic()
pairs=list(csv.DictReader((F/'analysis_v1/paired.csv').open()));out=[];sources=[Path(__file__),O/'protocol.md',F/'analysis_v1/paired.csv',F/'selection.json'];cached={}
comparisons=[('webvid2_5m_light_v1','composed10','compact10','Web组合 / compact'),('webvid2_5m_light_v1','composed10','baseline_soft','Web组合 / GT10-soft P'),('yandex_t2i_official10M_ip_v1','compact10','gt10_hard','Y compact / GT10-hard P')]
for ds,a,b,label in comparisons:
 cfgp=F/'inputs'/ds/'config.json';cfg=json.loads(cfgp.read_text());sources+=[cfgp,Path(cfg['gt_file'])];gt=np.fromfile(cfg['gt_file'],np.int64).reshape(2000,100)[:,:10]
 for L in [64,128,256,400,800]:
  arrays=[]
  for name in [a,b]:
   key=(ds,name,L)
   if key not in cached:
    m=next(m for m in cfg['methods'] if m['L']==L and m['model_name']==name);p=F/'results'/ds/m['name'];ids=np.fromfile(p/'ids.i32',np.int32).reshape(2000,10)
    masks=np.array([sum(1<<j for j,g in enumerate(gs) if int(g) in set(map(int,rr))) for rr,gs in zip(ids,gt)],np.uint16);hits=np.array([int(z).bit_count() for z in masks],np.int16)
    assert np.array_equal(masks,np.fromfile(p/'hitmask.u16',np.uint16));assert np.array_equal(hits,np.fromfile(p/'hits.u8',np.uint8));cached[key]=(masks,hits);sources += [p/x for x in ['ids.i32','hits.u8','hitmask.u16']]
   arrays.append(cached[key])
  (am,ah),(bm,bh)=arrays;delta=ah-bh
  r=dict(dataset=ds,label=label,candidate=a,reference=b,L=L,net_hits=int(delta.sum()),member_gained=sum(int(x&(~y&1023)).bit_count() for x,y in zip(am,bm)),member_lost=sum(int(y&(~x&1023)).bit_count() for x,y in zip(am,bm)),rescued=int(((bh==0)&(ah>0)).sum()),new_failures=int(((bh>0)&(ah==0)).sum()),gain_hits=int(np.maximum(delta,0).sum()),loss_hits=int(np.maximum(-delta,0).sum()))
  old=next(x for x in pairs if x['dataset']==ds and x['candidate']==a and x['reference']==b and int(x['L'])==L)
  for k in ['net_hits','member_gained','member_lost','rescued','new_failures','gain_hits','loss_hits']:assert r[k]==int(old[k]),(ds,L,k)
  assert r['member_gained']-r['member_lost']==r['net_hits'];r['recall_delta_pp']=r['net_hits']/200;r['failure_net_new']=r['new_failures']-r['rescued'];out.append(r)
with (O/'member_failure_balance.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
lines=['# 9月13日研究进展简报','', '**尚未找到稳定优于当前GT10起点的新方法，默认保持。** Web的补边＋父画像恢复组合修复了compact的部分损失，最终同批五L均有质量改善；相对GT10-soft P仍五L落后。Yandex compact低L小幅正向、高L出现损伤。','', '全部曲线来自同批历史validation2000，50点、250轮；CPU15、实际及数值库单线程，完整路由＋原NSG＋输出计时。五轮QPS波动不支持稳定整体加速。最终数据已有历史暴露，本次反馈未回流训练或选型。','', '下表为从原始返回独立集合评分的L128结果（成员是GT10目标；救回/新增失败按query计）：','', '| 对照 | 新找回成员 | 丢失成员 | Recall变化 pp | 救回 / 新增失败 |','|---|---:|---:|---:|---:|']
for r in out:
 if r['L']==128:lines.append(f"| {r['label']} | {r['member_gained']} | {r['member_lost']} | {r['recall_delta_pp']:+.3f} | {r['rescued']} / {r['new_failures']} |")
lines += ['', '零命中才算失败，命中1个不失败；净失败减少不保证总Recall提高。成员增损与逐query净命中变化正负部也不同，全部15组两种口径均已核对原表。跨L重复query不作独立样本，以上为最终结果的描述性复算，不是新实验或新性能点。','', '完整失败表保留401条独立query的全五L、各方法GT10/入口/返回，共10730单元；救回和新增损伤两个方向均保留。','', '[完整实验报告](../stage35_final_comparison_v1/report.md) · [QPS–Recall图](../stage35_final_comparison_v1/analysis_v1/figures/recall_qps.png) · [QPS–失败率图](../stage35_final_comparison_v1/analysis_v1/figures/failure_qps.png) · [按L三指标](../stage35_final_comparison_v1/analysis_v1/figures/three_metrics_by_L.png) · [双向失败案例](../stage35_final_comparison_v1/supplement_v1/figures/failure_cases_both_directions.png) · [401查询全表](../stage35_final_comparison_v1/supplement_v1/failed_queries_all_L.csv) · [15组复算](member_failure_balance.csv)。','', '本会话新增训练/ANN/构图/GT/QPS均为0，沿用E94实测成本700800 NSG、560000 HNSW；994.213秒native操作与695.047秒纯wall分别记录。继承训练和GT完整成本缺项保持未知。20:00前安全交接；整日21:00目标未标完成。']
(O/'report.md').write_text('\n'.join(lines)+'\n')
unique=sorted(set(sources));freeze=[dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in unique];(O/'input_freeze.json').write_text(json.dumps(dict(scope='post-hoc descriptive report dependencies, not pre-query selection',files=freeze),indent=2))
(O/'verification.json').write_text(json.dumps(dict(status='PASS',unique_original_return_rows=len(cached)*2000,paired_rows=len(out),all_original_paired_values_equal=True,new_ANN=0,new_training=0,new_QPS=0,final_feedback_used_for_selection=False,operation_seconds=time.monotonic()-t),indent=2));print(json.dumps(out,ensure_ascii=False));print((O/'verification.json').read_text())
