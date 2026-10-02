import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
os.sched_setaffinity(0,range(8))
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;OLD=R.parent/'routing_bridge_v1';P=R.parent/'hybrid_temperature_factorial_v1'

def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    started=time.perf_counter();C=json.loads((P/'config.locked.json').read_text());S=json.loads((OLD/'results/summary.json').read_text())
    paths=[R/'protocol.md',Path(__file__),OLD/'analyze.py',OLD/'audit.py',OLD/'report.md',OLD/'results/summary.json',OLD/'reviews/seal.json',P/'config.locked.json']
    for ds,c in C['datasets'].items():
        e=c['evaluate'];point=next(p for p in e['points'] if p['K']==100)
        paths += [Path(e['gt']),OLD/'results'/f'{ds}.npz']
        paths += [P/'results'/ds/'evaluation'/'k100'/f'{m["name"]}_L{point["L"]}'/'ids.i32' for m in e['methods']]
    frozen={str(p):ident(p) for p in paths}
    with (R/'frozen.json').open('x') as f:json.dump({'unix':time.time(),'files':frozen},f,indent=2)
    results={};cells=0;rows=[]
    for ds,c in C['datasets'].items():
        e=c['evaluate'];n=e['n'];point=next(p for p in e['points'] if p['K']==100);z=np.load(OLD/'results'/f'{ds}.npz')
        gt=np.fromfile(e['gt'],'<i4').reshape(n,100);correct={};encoded={};good={};offset=np.arange(n,dtype='i8')[:,None]*e['base_n']
        for m in e['methods']:
            name=m['name'];ids=np.fromfile(P/'results'/ds/'evaluation'/'k100'/f'{name}_L{point["L"]}'/'ids.i32','<i4').reshape(n,100)
            correct[name]=[set(a.tolist())&set(b.tolist()) for a,b in zip(ids,gt)]
            encoded[name]=ids.astype('i8')+offset;good[name]=np.isin(encoded[name],(gt.astype('i8')+offset).ravel(),assume_unique=True)
        pairs=[]
        for pair in S['datasets'][ds]['comparisons']:
            name,ref=pair['method'],pair['reference'];key=name+'_vs_'+ref
            gain=np.array([len(a-b) for a,b in zip(correct[name],correct[ref])]);loss=np.array([len(b-a) for a,b in zip(correct[name],correct[ref])]);delta=gain-loss
            gain2=(good[name]&~np.isin(encoded[name],encoded[ref].ravel(),assume_unique=True)).sum(1)
            loss2=(good[ref]&~np.isin(encoded[ref],encoded[name].ravel(),assume_unique=True)).sum(1)
            np.testing.assert_array_equal(gain,gain2);np.testing.assert_array_equal(loss,loss2)
            np.testing.assert_array_equal(delta,z[key+'_K100_delta_hits'])
            category=z[key+'_category'];near=z[name+'_near_float_boundary']|z[ref+'_near_float_boundary'];groups=[]
            oldpoint=next(p for p in pair['points'] if p['K']==100)
            for item in oldpoint['groups']:
                mask=category==item['category']
                if item['numeric_group']=='near':mask&=near
                if item['numeric_group']=='away':mask&=~near
                pos=int(delta[mask][delta[mask]>0].sum());neg=int(-delta[mask][delta[mask]<0].sum())
                assert pos==item['rescues'] and neg==item['damages'] and int(mask.sum())==item['n']
                g,l=int(gain[mask].sum()),int(loss[mask].sum());cancel=int(np.minimum(gain[mask],loss[mask]).sum())
                assert g-pos==l-neg==cancel
                groups.append({'category':item['category'],'numeric_group':item['numeric_group'],'n':item['n'],
                    'old_per_query_net_positive':pos,'old_per_query_net_negative':neg,'true_rescue_members':g,'true_damage_members':l,
                    'within_query_cancelled_members_per_side':cancel,'net_member_difference_unchanged':g-l});cells+=1
                if item['numeric_group']=='all' and item['category'] in [1,3] and name in ['HybridPilotTemperature','HybridFixedTemperature']:
                    label='Web' if ds.startswith('web') else 'Y';rows.append(f'| {label} {name} / {ref} | {item["category"]} | {pos} / {neg} | {g} / {l} | {cancel} | {g-l:+d} |')
            pairs.append({'method':name,'reference':ref,'K':100,'L':point['L'],'groups':groups})
        results[ds]=pairs;assert time.perf_counter()-started<60
    for p,v in frozen.items():assert ident(p)==v
    result={'status':'PASS','seconds':time.perf_counter()-started,'datasets':results,'group_cells':cells,'input_identities':len(frozen),
        'independent_scope':'same agent; Python correct-member sets versus query-encoded numpy membership',
        'old_numeric_values_changed':False,'Recall_changed':False,'new_GT':0,'new_NSG':0,'new_ANN':0}
    with (R/'results.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    text='''# 记录145的R100救回／损伤用语澄清

原145组内字段`rescues`和`damages`分别是每query净命中差的正／负累计。K100可在一条query上同时救回和损伤若干正确成员，旧字段会将这部分抵消；应称“每query净增加／净减少成员累计”。原净Recall、事件分解和停止结论保持，原代码／报告／JSON／seal均未修改。

本补充按正确返回成员集合差统计真实救回／损伤，另以带query编号的向量化ID编码逐query复核。以下展示原主候选，全部方法对及near/away组均在results.json中保存。事件1为精确top3相同、实际入口改变；事件3为两者都改变。

| 原方法对 | 事件 | 旧净增加 / 净减少 | 真救回 / 真损伤 | 每侧被抵消 | 净差保持 |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+f'''

全部{cells}个组单元、{len(frozen)}项身份通过，计算{result['seconds']:.3f}秒。K1不会在同query同时救回与损伤，原两类计数相同。本补充0新GT／NSG／ANN／模型／性能；没有改变任何旧标签、query或返回。新的158连接诊断已将真实成员差与每query净差分开存储。
'''
    (R/'report.md').write_text(text)
    print('PASS',cells,'cells',result['seconds'],'seconds',flush=True)

if __name__=='__main__':main()
