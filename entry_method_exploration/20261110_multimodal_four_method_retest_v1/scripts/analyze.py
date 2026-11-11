"""Read-only measurement analysis; all plots use E200 actual measurements."""
from pathlib import Path
import os,sys,json,csv,gzip,hashlib,struct,time,argparse
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
RUN=Path(__file__).resolve().parents[1];ROOT=RUN.parents[1]
NAMES={'coco':'COCO','flickr30k':'Flickr30k','webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex'}
METHODS=['NSG','GT10','GT10+Residual','GATE']
COLORS={'NSG':'#68737d','GT10':'#1976d2','GT10+Residual':'#d9543f','GATE':'#2e8b57'}

def read(path):return json.loads(Path(path).read_text())
def raw(path):
    p=Path(path)
    if p.exists():return p.read_bytes()
    with gzip.open(str(p)+'.gz','rb') as f:return f.read()
def dump(path,value):
    with Path(path).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def table(path,rows):
    with Path(path).open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def gt_for(ds):
    c=read(ROOT/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1/configs'/f'{ds}.analysis.json')['eval_gt']
    start=c.get('row_start',0);n=c['n'];k=c['k']
    if c['format']=='ivecs':
        a=np.fromfile(c['path'],'<i4').reshape(-1,k+1);assert np.all(a[:,0]==k);a=a[:,1:]
    else:a=np.fromfile(c['path'],'<i8' if c['format']=='raw_i64' else '<i4').reshape(-1,k)
    return a[start:start+n].astype(np.int64)
def packet(point,n,K):
    p=point/'raw';buffers=[raw(p/name) for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']]
    h=hashlib.sha256(struct.pack('<QQ',n,K))
    for b in buffers:h.update(b)
    h.update(bytes(n*8));h.update(bytes(n*8))
    ids=np.frombuffer(buffers[0],'<i4').reshape(n,K)
    distances=np.frombuffer(buffers[1],'<f4').reshape(n,K)
    entries=np.frombuffer(buffers[2],'<i4').reshape(n,3)
    assert np.isfinite(distances).all() and (np.diff(distances,axis=1)>=0).all()
    assert (np.diff(np.sort(ids,axis=1),axis=1)>0).all()
    return ids,entries,h.hexdigest()

def main(out):
    assert read(RUN/'reviews/measurement_complete.json')['status']=='PASS'
    assert not out.exists();out.mkdir(parents=True);(out/'figures').mkdir()
    t0=time.time();lock=read(RUN/'config.locked.json');points=[];rounds=[];paired=[];hit_arrays={};datasets=lock['datasets']
    for ds in datasets:
        config=read(RUN/'configs'/f'{ds}.json');gt=gt_for(ds);n=len(gt);N=config['base']['n']
        for K in [1,100]:
            job=RUN/'results'/ds/f'k{K}_run';complete=read(job/'complete.json');assert complete['points']==80
            offsets=np.arange(n,dtype=np.int64)[:,None]*N
            gtcode=(offsets+np.sort(gt[:,:K],axis=1)).ravel()
            gtcode=np.append(gtcode,np.iinfo(np.int64).max)
            for L in lock['K_L'][str(K)]:
                data={}
                for method in METHODS:
                    point=job/f'k{K}'/f'{method}_L{L}';meta=read(point/'result.json')
                    assert meta['n']==n and meta['K']==K and meta['L']==L and meta['timing_repeats']==2
                    ids,entries,digest=packet(point,n,K);assert ids.min()>=0 and ids.max()<N
                    assert all(x['packet_sha256']==digest for x in meta['rounds'])
                    codes=offsets+ids;pos=np.searchsorted(gtcode,codes);correct=gtcode[pos]==codes
                    hits=correct.sum(axis=1);total=int(hits.sum());recall=total/(n*K)
                    hit_arrays[f'{ds}__k{K}__{method}__L{L}']=hits.astype('<u2')
                    walls=[float(x['wall_seconds']) for x in meta['rounds']];qps=[n/x for x in walls]
                    assert np.isclose(meta['qps'],sum(qps)/2,rtol=1e-12)
                    assert np.isclose(meta['wall_seconds'],sum(walls)/2,rtol=1e-12)
                    row={'dataset':ds,'K':K,'L':L,'method':method,'n':n,'hits':total,'recall':recall,'recall_percent':recall*100,
                      'qps_mean':sum(qps)/2,'qps_min':min(qps),'qps_max':max(qps),'qps_round0':qps[0],'qps_round1':qps[1],
                      'wall_mean_seconds':sum(walls)/2,'wall_round0_seconds':walls[0],'wall_round1_seconds':walls[1],'qps_pooled':2*n/sum(walls),
                      'mean_query_us':sum(walls)/2/n*1e6,'severe_queries':int((hits<10).sum()) if K==100 else None,
                      'zero_hit_queries':int((hits==0).sum()),'packet_sha256':digest,'point_dir':str(point),'threads':1}
                    points.append(row);data[method]={'row':row,'hits':hits,'correct_codes':codes[correct]}
                    for rep,x in enumerate(meta['rounds']):rounds.append({'dataset':ds,'K':K,'L':L,'method':method,'round':rep,'n':n,'wall_seconds':walls[rep],'qps':qps[rep],'threads':x['threads'],'cpu':x['cpu'],'packet_sha256':x['packet_sha256']})
                for method,ref in [('GT10','NSG'),('GT10+Residual','GT10'),('GATE','NSG')]:
                    a,b=data[method],data[ref];ah,bh=a['hits'],b['hits'];ar,br=a['row'],b['row']
                    pair={'dataset':ds,'K':K,'L':L,'method':method,'reference':ref,'recall_delta_pp':ar['recall_percent']-br['recall_percent'],
                       'qps_change_percent':100*(ar['qps_mean']/br['qps_mean']-1),'mean_time_increase_percent':100*(ar['mean_query_us']/br['mean_query_us']-1),
                       'rescued_members':int(len(np.setdiff1d(a['correct_codes'],b['correct_codes'],assume_unique=True))),
                       'lost_members':int(len(np.setdiff1d(b['correct_codes'],a['correct_codes'],assume_unique=True))),
                       'improved_queries':int((ah>bh).sum()),'degraded_queries':int((ah<bh).sum()),
                       'severe_rescued':int(((bh<10)&(ah>=10)).sum()) if K==100 else None,
                       'new_severe':int(((bh>=10)&(ah<10)).sum()) if K==100 else None}
                    assert pair['rescued_members']-pair['lost_members']==ar['hits']-br['hits'];paired.append(pair)
        print('ANALYZED',ds,len(points),flush=True)
    assert len(points)==640 and len(rounds)==1280 and len(paired)==480
    table(out/'points.csv',points);table(out/'rounds.csv',rounds);table(out/'paired.csv',paired)
    np.savez_compressed(out/'per_query_hits.npz',**hit_arrays)
    targets=[];frontier=[]
    for ds in datasets:
        for K in [1,100]:
            group=[p for p in points if p['dataset']==ds and p['K']==K]
            for threshold in [.90,.95,.99]:
                for method in METHODS:
                    valid=[p for p in group if p['method']==method and p['recall']>=threshold]
                    best=max(valid,key=lambda p:p['qps_mean']) if valid else None
                    targets.append({'dataset':ds,'K':K,'target_recall':threshold,'method':method,'reached':bool(best),'L':best['L'] if best else None,'actual_recall':best['recall'] if best else None,'qps_mean':best['qps_mean'] if best else None,'qps_min':best['qps_min'] if best else None,'qps_max':best['qps_max'] if best else None})
            for p in group:
                dom=[q for q in group if q['method']!=p['method'] and q['hits']>=p['hits'] and q['qps_mean']>=p['qps_mean'] and (q['hits']>p['hits'] or q['qps_mean']>p['qps_mean'])]
                gt=[q for q in group if q['method']=='GT10' and q['hits']>=p['hits']]
                best=max(gt,key=lambda q:q['qps_mean']) if gt else None
                frontier.append({'dataset':ds,'K':K,'method':p['method'],'L':p['L'],'covered_by_other_method':bool(dom),'covering_points':';'.join(f'{q["method"]}:L{q["L"]}' for q in dom),'GT10_at_least_quality_L':best['L'] if best else None,'qps_vs_GT10_at_least_quality_percent':100*(p['qps_mean']/best['qps_mean']-1) if best else None})
    table(out/'targets.csv',targets);table(out/'frontier.csv',frontier)
    for K in [1,100]:
        fig,axs=plt.subplots(2,2,figsize=(13.2,9.0),constrained_layout=True)
        for ax,ds in zip(axs.ravel(),datasets):
            for method in METHODS:
                rows=sorted([p for p in points if p['dataset']==ds and p['K']==K and p['method']==method],key=lambda p:p['L'])
                x=[p['recall_percent'] for p in rows];y=[p['qps_mean'] for p in rows]
                ax.plot(x,y,'o-',lw=1.8,ms=3.3,color=COLORS[method],label=method)
                ax.fill_between(x,[p['qps_min'] for p in rows],[p['qps_max'] for p in rows],color=COLORS[method],alpha=.12)
            ax.set_title(f'{NAMES[ds]} | K={K}');ax.set_xlabel(f'Recall@{K} (%)');ax.set_ylabel('QPS (mean of 2 runs)');ax.grid(alpha=.2);ax.legend(fontsize=9)
        fig.suptitle(f'E200: full test queries, one thread, 20 measured budgets per curve\nShading: two-run range; complete query wall; fixed models',fontsize=13)
        for ext in ['png','svg']:fig.savefig(out/'figures'/f'recall_qps_k{K}.{ext}',dpi=170)
        plt.close(fig)
    report=['# E200 四多模态数据集四方法加密重测','',
      '完整矩阵：4集 × 4方法 × 2个K × 20档预算 = 640点；每点两遍，共1280完整单线程批次、1120万正式查询。默认保持E99 GT10。',
      '', 'NSG、GT10、GT10＋直接残差和GATE共用同一原scalar主核。GT10固定WebVid soft-t1，其余hard；残差为完整16K/B32表及返回等价工程优化。GATE为E97修正标签后的外部入口基线。',
      '', '![Recall@1](figures/recall_qps_k1.png)','', '![Recall@100](figures/recall_qps_k100.png)','',
      '每条曲线保留20个实测预算点；QPS是两次N/wall的算术平均，阴影仅为两轮范围，不是置信区间。平均wall与合并QPS另列CSV，不混用。Recall由实际返回和原GT重新计算，两轮返回逐字节相同。',
      '', '## 达到召回门槛的最快实测点','', '单元格为实际Recall% / 平均QPS（L）；未达到记—。这些是有限预算网格上的门槛比较，实际召回可能不同，不能称严格等Recall提速。','',
      '| 数据 | K | 目标Recall | NSG | GT10 | GT10＋残差 | GATE |','| --- | --- | --- | --- | --- | --- | --- |']
    for ds in datasets:
        for K in [1,100]:
            for th in [.90,.95,.99]:
                cells=[]
                for m in METHODS:
                    v=next(t for t in targets if t['dataset']==ds and t['K']==K and t['target_recall']==th and t['method']==m)
                    cells.append(f'{v["actual_recall"]*100:.3f}% / {v["qps_mean"]:.2f} (L{v["L"]})' if v['reached'] else '—')
                report.append(f'| {NAMES[ds]} | {K} | {th*100:.0f}% | '+' | '.join(cells)+' |')
    report+=['','## 同L增量与费用','', '同L200用于分阶段记账，不能代替等费用前沿。残差救回/损伤指正确成员事件；严重低召回仅K100的0–9命中。','',
      '| 数据 | K | GT10 Recall/QPS | ＋残差 Recall/QPS | ΔRecall pp | 完整平均耗时变化 | 救回/损伤 |','| --- | --- | --- | --- | --- | --- | --- |']
    for ds in datasets:
        for K in [1,100]:
            a=next(p for p in points if p['dataset']==ds and p['K']==K and p['L']==200 and p['method']=='GT10')
            b=next(p for p in points if p['dataset']==ds and p['K']==K and p['L']==200 and p['method']=='GT10+Residual')
            p=next(p for p in paired if p['dataset']==ds and p['K']==K and p['L']==200 and p['method']=='GT10+Residual')
            report.append(f'| {NAMES[ds]} | {K} | {a["recall_percent"]:.4f}% / {a["qps_mean"]:.2f} | {b["recall_percent"]:.4f}% / {b["qps_mean"]:.2f} | {p["recall_delta_pp"]:+.4f} | {p["mean_time_increase_percent"]:+.2f}% | {p["rescued_members"]}/{p["lost_members"]} |')
    report+=['','## 数据、成本与解释边界','',
      '完整测试查询为COCO 10000、Flickr30k 5000、WebVid 10000、Yandex 10000；原raw-IP、底库、NSG图、测试GT和GT10/残差训练资产保持。公开测试已有曝光；本轮是完整重测，不是新的盲确认。',
      '', 'Web/Yandex GATE复用冻结模型；COCO/Flickr沿E97复现流程补建512hub、拓扑特征和离线塔。两集GATE训练/monitor来自合法residual角色前10000/随后1024，与测试向量和身份组分离，但曾参与B32监督。方法继承的训练规模不同，不能称等监督量因果消融。GT只用于离线标签与返回后评测。',
      '', '离线新GATE阶段耗时见reviews/gate_preparation_costs.json；正式进程与压缩耗时见reviews/formal_process_costs.json，内部wall已包含于进程耗时，不能重复加总。继承的构图/GT/训练成本没有清零；文件大小不等于RSS。',
      '', 'Flickr GATE离线训练期间运行环境发生重启，已从epoch7的完整模型、优化器和torch随机数检查点接续epoch8；原日志和恢复检查点保留于reviews/recovery_boot1。模型选择仍遵守原监控集和早停规则。中断前已提交训练时间与恢复后进程时间分列，未完成epoch的耗时未知，不将主机停机时长当作训练成本，也不把所记录的下界当作完整构建总成本。重启发生在全部正式计时开始之前。',
      '', '完整wall包含正常输出生命周期、路由、搜索、残差评分合并及统一复制销毁；加载、GT、写盘、hash、压缩和独审在外。没有将E103优化核或旧实验QPS拼入新主表。两轮计时范围不提供跨机器或统计显著性保证，有限网格未覆盖不等于全局最优。',
      '', '[全部点](points.csv) · [两遍原始计时](rounds.csv) · [同L救损与费用](paired.csv) · [门槛点](targets.csv) · [有限网格前沿](frontier.csv)。独立整数/计时核验与实际图形审查完成后才作最终交付。']
    (out/'report_zh.md').write_text('\n'.join(report)+'\n')
    dump(out/'analysis_validation.json',{'status':'PASS_PRIMARY_ANALYSIS','points':len(points),'rounds':len(rounds),'pairs':len(paired),'formal_queries':sum(p['n'] for p in rounds),'elapsed_seconds':time.time()-t0,'independent_audit_pending':True,'visual_review_pending':True})
    print(out,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=RUN/'analysis/final_v1');a=p.parse_args();main(a.out)
