#!/usr/bin/env python3
"""Score completed public test packets; never search, fit, or select a model."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
METHODS=('NSG','GT','M5')
EXPECTED_L=(200,400,800,1000,1200)
BOOTSTRAP_REPEATS=2000
BOOTSTRAP_SEED=20261009

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()

def load_json(path):return json.loads(Path(path).read_text())

def raw(path,dtype,shape):
    a=np.fromfile(path,dtype=dtype)
    require(a.size==int(np.prod(shape)),f'raw shape: {path}')
    return a.reshape(shape)

def gt_window(c):
    path=Path(c['GT']);first=int(c.get('GT_first',c.get('query_first',0)));n=int(c['n'])
    if c.get('GT_format','ivecs')=='ivecs':
        a=np.memmap(path,dtype='<i4',mode='r');require(a.size>0,'empty GT')
        width=int(a[0]);require(width>=100 and a.size%(width+1)==0,'GT ivecs shape')
        a=a.reshape(-1,width+1);require(np.all(a[:,0]==width),'GT row headers')
        require(first>=0 and first+n<=len(a),'GT window bounds')
        return np.array(a[first:first+n,1:101],copy=True)
    width=int(c.get('GT_width',100));require(width>=100,'GT width')
    a=np.memmap(path,dtype='<i4',mode='r');require(a.size%width==0,'GT raw shape')
    a=a.reshape(-1,width);require(first>=0 and first+n<=len(a),'GT window bounds')
    return np.array(a[first:first+n,:100],copy=True)

def paired_ci_pp(delta_hits,K,key):
    # Query bootstrap of paired differences. Multinomial counts over exact
    # observed integer difference classes equal ordinary row resampling.
    values,counts=np.unique(delta_hits,return_counts=True);n=len(delta_hits)
    seed=(BOOTSTRAP_SEED+int.from_bytes(hashlib.sha256(key.encode()).digest()[:4],'little'))%(2**32)
    rng=np.random.default_rng(seed)
    draws=rng.multinomial(n,counts/n,size=BOOTSTRAP_REPEATS)
    means=(draws@values.astype(np.float64))/(n*K)*100
    lo,hi=np.quantile(means,[.025,.975])
    return {'low_pp':float(lo),'high_pp':float(hi),'repeats':BOOTSTRAP_REPEATS,'seed':int(seed),
            'scope':'descriptive paired query bootstrap; not a quality gate or guaranteed population interval'}

def write_csv(path,rows,fields):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--jobs',type=Path,default=ROOT/'jobs_v2');parser.add_argument('--out',type=Path,default=ROOT/'analysis_v2');args=parser.parse_args()
    jobs=sorted(args.jobs.glob('*.combined.json'));require(len(jobs)==2,'expected two combined dataset jobs')
    require(not args.out.exists(),'preserve existing analysis; use a new --out directory')
    points=[];comparisons=[];source={};windows=[];all_pairs=[];score_packets=[]
    for job_path in jobs:
        c=load_json(job_path);dataset=c['dataset'];n=int(c['n']);base_n=int(c['base_n']);out=Path(c['out'])
        require(n==10000 and c['K_values']==[1,100] and tuple(c['L'])==EXPECTED_L,'frozen full test matrix')
        require(c.get('threads')==1 and c.get('cpu')==15 and c.get('no_training') is True,'single thread/no training job')
        complete=load_json(out/'complete.json');require(complete['status']=='PASS_NSG_GT_M5_NATIVE_FULL_PLAIN_SAMPLED_COUNT_LINEAR_ORACLE_V2','full native completion')
        require(complete['wall_rounds']==30*int(c['timing_repeats']),'all dataset wall rounds')
        saved_job=load_json(out/'job.json');require(saved_job==c,'actual job differs from frozen combined job')
        env=load_json(out/'native_environment.json');require(env['threads']==1 and env['no_GT_read'] is True,'native environment')
        audit_n=256;expected_audit_ids=np.arange(audit_n,dtype=np.int64)*(n-1)//(audit_n-1)
        require(complete['count_audit_n']==audit_n and complete['full_plain_return_n']==n and complete['full_M5_linear_merge_audit_n']==n,'declared full returns and sampled counts')
        common_audit_ids=raw(out/'audit_query_ids.i32','<i4',(audit_n,));require(np.array_equal(common_audit_ids,expected_audit_ids),'predeclared uniformly spaced count queries')
        source[str(out/'audit_query_ids.i32')]=sha(out/'audit_query_ids.i32')
        for key,hashkey in [('queries','query_sha256'),('GT','GT_sha256'),('table','table_sha256')]:
            actual=sha(c[key]);require(actual==c[hashkey],f'{dataset} {key} frozen checksum');source[c[key]]=actual
        source[str(job_path)]=sha(job_path);source[str(out/'complete.json')]=sha(out/'complete.json')
        gt=gt_window(c);require(np.all((gt>=0)&(gt<base_n)),'GT ID domain')
        require(all(len(set(row.tolist()))==100 for row in gt),'unique GT100 IDs')
        windows.append({'dataset':dataset,'n':n,'query_first':int(c.get('query_first',0)),'query_last_exclusive':int(c.get('query_first',0))+n,
                        'queries':c['queries'],'GT':c['GT'],'GT_first':int(c.get('GT_first',c.get('query_first',0))),
                        'role':'public test; historically used public benchmark, not a fresh blind population sample',
                        'GT_method':c['anchor']['name'],'table':c['table'],'table_sha256':c['table_sha256']})
        for K in c['K_values']:
            for L in c['L']:
                packets={};gt_targets=gt[:,:K]
                for method in METHODS:
                    folder=out/f'k{K}'/f'{method}_L{L}';receipt=load_json(folder/'complete.json')
                    require(receipt['method']==method and receipt['K']==K and receipt['L']==L and receipt['n']==n,'point receipt identity')
                    require(receipt['threads']==1 and receipt['cpu']==15 and receipt['plain_count_bits_equal'] is True,'point correctness/thread receipt')
                    require(receipt['normal_output_release_before_stop'] is True and receipt['timed_output_retained'] is False,'full lifetime clock receipt')
                    require(receipt['count_audit_n']==audit_n and receipt['full_plain_return_n']==n,'point full-return/count-sample scope')
                    require(receipt['plain_count_parity_scope']=='fixed uniform query sample only' and receipt['stats_scope']=='fixed uniform count-audit queries only, not the full batch','sample-only parity and statistics scope')
                    if method=='M5':require(receipt['independent_original_linear_merge'] is True and receipt['linear_merge_audit_n']==n,'M5 full merge oracle')
                    seconds=np.asarray(receipt['timing_seconds'],dtype=np.float64)
                    require(len(seconds)==int(c['timing_repeats'])==3 and np.all(np.isfinite(seconds)&(seconds>0)),'three valid complete wall rounds')
                    ids=raw(folder/'raw/ids.i32','<i4',(n,K));dist=raw(folder/'raw/distances.f32','<f4',(n,K))
                    entries=raw(folder/'raw/entry_ids.i32','<i4',(n,3));profiles=raw(folder/'raw/profile_distances.f32','<f4',(n,3))
                    audit_ids=raw(folder/'raw/audit_query_ids.i32','<i4',(audit_n,));require(np.array_equal(audit_ids,expected_audit_ids),'point count query alignment')
                    route=raw(folder/'raw/route_ndc.u64','<u8',(audit_n,));graph=raw(folder/'raw/graph_ndc.u64','<u8',(audit_n,))
                    require(np.all((ids==-1)|((ids>=0)&(ids<base_n))),'returned ID domain')
                    require(np.all(np.isfinite(dist)),'finite result distance words')
                    require(np.all(dist[ids==-1]==np.finfo(np.float32).max),'padding score')
                    hits=np.empty(n,dtype=np.int16);members=np.zeros((n,K),dtype=np.bool_);padding=0
                    for i in range(n):
                        valid=ids[i][ids[i]>=0].tolist();returned=set(valid);require(len(valid)==len(returned),f'duplicate returned IDs {dataset} K{K} L{L} {method} row{i}')
                        targets=set(gt_targets[i].tolist());hits[i]=len(returned&targets);members[i]=[int(t) in returned for t in gt_targets[i]];padding+=K-len(valid)
                    require(np.array_equal(hits,members.sum(axis=1)),'independent set/member count agreement')
                    qps=n/seconds;row={'dataset':dataset,'K':K,'L':L,'method':method,'n':n,'recall':float(hits.sum()/(n*K)),
                        'recall_pct':float(hits.sum()/(n*K)*100),'matched_GT_members':int(hits.sum()),'padding_IDs':padding,
                        'wall_seconds':seconds.tolist(),'qps_rounds':qps.tolist(),'qps_median':float(np.median(qps)),
                        'qps_min':float(qps.min()),'qps_max':float(qps.max()),'threads':1,'cpu':15,
                        'count_audit_n':audit_n,'count_audit_scope':'fixed uniform 256 query sample only; not the full batch',
                        'graph_ndc_sample_total':int(graph.sum()),'graph_ndc_sample_mean':float(graph.mean()),'router_ndc_sample_total':int(route.sum()),'router_ndc_sample_mean':float(route.mean()),
                        'post_dots_sample_total':int(receipt['stats']['post_dots']),'post_dots_sample_mean':float(receipt['stats']['post_dots']/audit_n),
                        'post_dots_already_in_graph_ndc':True,'warmup_n':int(receipt['warmup_n']),'warmup_batches':int(receipt['warmup_batches']),
                        'domain_fallbacks_sample':int(receipt['stats']['domain_fallbacks']),'source_packet':str(folder/'raw'),'source_complete':str(folder/'complete.json')}
                    if method=='NSG':require(np.all(entries[:,0]==env['enterpoint']) and np.all(entries[:,1:]==-1) and np.all(route==0),'original NSG enterpoint/no routing')
                    else:require(np.all((entries>=0)&(entries<base_n)),'real GT/M5 route entries')
                    for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32','route_ndc.u64','graph_ndc.u64','audit_query_ids.i32']:source[str(folder/'raw'/name)]=sha(folder/'raw'/name)
                    points.append(row);packets[method]={'row':row,'hits':hits,'members':members,'entries':entries,'profiles':profiles,'route':route,'graph':graph}
                    score_packets.append((f'{dataset}.k{K}.{method}.L{L}.npz',hits,np.packbits(members,axis=1)))
                require(np.array_equal(packets['GT']['entries'],packets['M5']['entries']),'GT/M5 actual route IDs')
                require(np.array_equal(packets['GT']['profiles'].view(np.uint32),packets['M5']['profiles'].view(np.uint32)),'GT/M5 route distance words')
                require(np.array_equal(packets['GT']['route'],packets['M5']['route']),'GT/M5 route dot counts')
                require(np.all(packets['M5']['graph']>=packets['GT']['graph']),'M5 preserves original main search physical scores')
                require(int(packets['M5']['graph'].sum())-int(packets['GT']['graph'].sum())==packets['M5']['row']['post_dots_sample_total'],'sample post dot subset accounting')
                for method,reference in [('GT','NSG'),('M5','GT'),('M5','NSG')]:
                    a,b=packets[method],packets[reference];delta=a['hits'].astype(np.int32)-b['hits'];rescues=(a['members']&~b['members']).sum(axis=1);damages=(b['members']&~a['members']).sum(axis=1)
                    require(np.array_equal(delta,rescues.astype(np.int32)-damages),'paired member rescue/damage net')
                    ratios=np.asarray(a['row']['qps_rounds'])/np.asarray(b['row']['qps_rounds']);key=f'{dataset}|{K}|{L}|{method}|{reference}'
                    comp={'dataset':dataset,'K':K,'L':L,'method':method,'reference':reference,'n':n,
                        'recall_delta_pp':float(delta.sum()/(n*K)*100),'rescue_members':int(rescues.sum()),'damage_members':int(damages.sum()),
                        'queries_net_improved':int(np.count_nonzero(delta>0)),'queries_net_damaged':int(np.count_nonzero(delta<0)),
                        'queries_net_equal':int(np.count_nonzero(delta==0)),'paired_qps_ratio_rounds':ratios.tolist(),
                        'paired_qps_ratio_median':float(np.median(ratios)),'paired_qps_ratio_min':float(ratios.min()),'paired_qps_ratio_max':float(ratios.max()),
                        'paired_qps_change_pct':float((np.median(ratios)-1)*100),'descriptive_delta_ci':paired_ci_pp(delta,K,key),
                        'observed_joint_gain':bool(delta.sum()>0 and np.median(ratios)>1),
                        'method_qps_median':a['row']['qps_median'],'reference_qps_median':b['row']['qps_median'],
                        'all_rounds_faster':bool(np.all(ratios>1))}
                    comparisons.append(comp)
                    if method=='M5' and reference=='GT':
                        for i in range(n):all_pairs.append({'dataset':dataset,'K':K,'L':L,'query_row':i,'source_query_row':int(c.get('query_first',0))+i,
                            'GT_hits':int(b['hits'][i]),'M5_hits':int(a['hits'][i]),'rescue_members':int(rescues[i]),'damage_members':int(damages[i]),'net_members':int(delta[i])})
    require(len(points)==60 and len(comparisons)==60 and len(all_pairs)==200000,'complete two-dataset matrix')
    args.out.mkdir();(args.out/'scored').mkdir()
    for name,hits,members in score_packets:np.savez_compressed(args.out/'scored'/name,hits=hits,GT_member_bits=members)
    result={'status':'COMPLETE_TRUE_PUBLIC_TEST_NSG_GT_M5_60_POINTS','windows':windows,'points':points,'comparisons':comparisons,'source_sha256':source,
            'new_training':False,'new_search_in_analysis':False,'quality_screen_gate_used':False,'default_replacement_decided':False,
            'interpretation':'All five actual L for all methods. Compare measured points; no interpolation, test-feedback tuning, or mixing windows.',
            'bootstrap':{'repeats':BOOTSTRAP_REPEATS,'base_seed':BOOTSTRAP_SEED,'meaning':'descriptive paired query resampling, not a pass/fail gate'},
            'audit_version':'V2: full 10000 returns and full M5 linear merge; count/plain parity and NDC on fixed uniform 256 query sample',
            'graph_ndc_definition':'M5 graph_ndc includes original graph scores and post_dots, for sampled queries only; never add post_dots a second time or claim a full-batch count.'}
    (args.out/'metrics.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    point_fields=['dataset','K','L','method','n','recall_pct','matched_GT_members','qps_median','qps_min','qps_max','padding_IDs','count_audit_n','graph_ndc_sample_mean','router_ndc_sample_mean','post_dots_sample_mean','domain_fallbacks_sample','warmup_n','warmup_batches','threads','cpu']
    write_csv(args.out/'metrics.csv',points,point_fields)
    flat_comps=[]
    for x in comparisons:
        y=dict(x);y['descriptive_delta_ci_low_pp']=x['descriptive_delta_ci']['low_pp'];y['descriptive_delta_ci_high_pp']=x['descriptive_delta_ci']['high_pp'];flat_comps.append(y)
    write_csv(args.out/'comparisons.csv',flat_comps,['dataset','K','L','method','reference','recall_delta_pp','rescue_members','damage_members','queries_net_improved','queries_net_damaged','paired_qps_ratio_median','paired_qps_ratio_min','paired_qps_ratio_max','paired_qps_change_pct','descriptive_delta_ci_low_pp','descriptive_delta_ci_high_pp','observed_joint_gain','all_rounds_faster'])
    write_csv(args.out/'paired_query_metrics.csv',all_pairs,['dataset','K','L','query_row','source_query_row','GT_hits','M5_hits','rescue_members','damage_members','net_members'])
    lookup={(p['dataset'],p['K'],p['L'],p['method']):p for p in points};lines=['# NSG、GT10、M5 正式公共测试复测','',
        '两集各取公共测试文件第 0–9999 行；三方法使用同一原 NSG 图、raw-IP、scalar search_new、单线程 CPU15。M5 在 GT10 路由和搜索结果后调用已冻结 residual posting 表，未新增训练。',
        '','每个 K 分别搜索并返回真实 K；L=200/400/800/1000/1200 对三方法均为实际相同预算。每点三轮完整 wall，固定轮换方法，模型/数据加载、GT 评分、计数与写盘在 wall 外。完整 wall 包含路由、搜索、补全查表、去重、重评分、合并及正常输出内存的分配和释放。','',
        '公共测试集有历史使用记录，本次是完整实际复测，不称全新盲测或独立总体验证。此报告不使用旧 SELECT/CAL 质量门，也不在测试结果上重训、调整表或更换参数。','']
    for window in windows:
        dataset=window['dataset'];label='WebVid' if 'webvid' in dataset else 'Yandex'
        lines+= [f'## {label}：{window["GT_method"]}', '',f'查询：`{window["queries"]}`；GT：`{window["GT"]}`；窗口 [{window["query_first"]}, {window["query_last_exclusive"]})。','']
        for K in [1,100]:
            lines +=[f'### Recall@{K}', '', '| 实际 L | NSG Recall % | NSG QPS | GT Recall % | GT QPS | M5 Recall % | M5 QPS | M5−GT pp | M5/GT 配对速度变化 | 救回 / 损伤成员 |', '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
            for L in EXPECTED_L:
                p=[lookup[(dataset,K,L,m)] for m in METHODS];x=next(x for x in comparisons if (x['dataset'],x['K'],x['L'],x['method'],x['reference'])==(dataset,K,L,'M5','GT'))
                lines.append(f'| {L} | {p[0]["recall_pct"]:.6f} | {p[0]["qps_median"]:.3f} | {p[1]["recall_pct"]:.6f} | {p[1]["qps_median"]:.3f} | {p[2]["recall_pct"]:.6f} | {p[2]["qps_median"]:.3f} | {x["recall_delta_pp"]:+.6f} | {x["paired_qps_change_pct"]:+.3f}% | {x["rescue_members"]} / {x["damage_members"]} |')
            lines+=['']
    lines +=['## 计量与可追溯性','',
        'QPS 表列为三个完整 wall 的 QPS 中位数；最小值/最大值及各轮原值见 metrics.json。配对速度比先对相同 round 求 QPS 比，再取三个比值的中位数，未用两个 QPS 中位数相除代替。',
        '','Recall 按全部 10000 条查询的真实返回集合与对应前 K 个 GT ID 的交集计数，分母固定 n×K。所有 60 点完整返回都完成 ID 域、有效 ID 唯一性和 padding 审计；GT/M5 的全部有序路由 ID、画像距离原 bits 完全一致；M5 的 10000 条独立线性合并审计通过。plain/count 原 bits 和路由/graph 计数只在事先固定的 256 个均匀查询上核验，qid=floor(i×9999/255)，包含两端，保存 audit_query_ids.i32；不把抽样 parity 称为全批 parity。',
        '','comparisons.csv 给出 GT/NSG、M5/GT、M5/NSG 的同 L 成员救回/损伤、净变化和三轮配对速度比。paired_query_metrics.csv 保留 M5/GT 的全部 200000 个 query×K×L 行。描述区间是固定 seed 的 2000 次配对查询 bootstrap，不作为通过门或总体可靠性证明。',
        '','M5 graph_ndc 已包含 post_dots；post_dots 仅作为其中子项披露，不重复加回。所有 NDC、post_dots、domain_fallbacks 和 stats 都只对应上述固定 256 个查询；不将其称为 10000 条的总计或全批均值。完整查询吞吐仍以全部 10000 条三轮 wall/QPS 判定，NDC 不能代替耗时。',
        '','图中连线仅帮助读取五个实测点，不据此插值或宣称整条曲线支配。默认替换需根据本次实际收益及重复稳定性另作明确判断。',
        '','产物：metrics.json、metrics.csv、comparisons.csv、paired_query_metrics.csv、scored/*.npz。源码与数据/冻结表身份由 metrics.json 的 source_sha256 及本实验构建/冻结记录追溯。','']
    (args.out/'report.md').write_text('\n'.join(lines))
    print(json.dumps({'status':result['status'],'points':len(points),'paired_query_rows':len(all_pairs),'out':str(args.out)},ensure_ascii=False))

if __name__=='__main__':main()
