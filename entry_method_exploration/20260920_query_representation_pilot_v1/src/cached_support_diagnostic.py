"""Post-gate diagnosis on already measured actions; no new model or search."""
from common import *
gate=read(RUN/'reviews/representation_gate.json');assert gate['status']=='STOP_REPRESENTATION'
metrics=read(RUN/'results/quality_metrics.json');records=[]
for ds in DS:
    offset=0
    for split in ['fit','cal']:
        c=read(RUN/'inputs'/ds/split/'config.json');n,d,h=c['n'],c['dimension'],c['hub_count']
        label=RUN/'labels'/ds/(split+'_labels')
        triples=np.fromfile(label/'triples.i32','int32').reshape(n,56,3)
        teacher=np.fromfile(label/'teacher_mask.u8','uint8').reshape(n,56).astype(bool)
        for family in ['Identity','QLinear','QMLP','WFree']:
            path=c['routers'][0]['W'] if family=='Identity' else read(RUN/'models'/ds/family/'model.json')['W']
            w=np.fromfile(path,'float32').reshape(h,d).astype('float64')
            z=np.fromfile(RUN/'results'/ds/'quality'/f'{family}.encoded.f32','float32').reshape(2560,d)[offset:offset+n]
            score=z.astype('float64')@w.T
            logits=np.take_along_axis(score[:,None,:],triples,axis=2).sum(2)
            chosen=logits.argmax(1)
            row=dict(dataset=ds,split=split,family=family,within_C8_teacher_accuracy=float(teacher[np.arange(n),chosen].mean()),K={})
            for K in [1,100]:
                cached=np.fromfile(label/f'k{K}.hits.u8','uint8').reshape(n,56)
                recall=float(cached[np.arange(n),chosen].mean()/K)
                baseline=next(x for x in metrics if x['dataset']==ds and x['split']==split and x['method']=='GT10' and x['K']==K)['recall']
                actual=next(x for x in metrics if x['dataset']==ds and x['split']==split and x['method']==family+'Exact' and x['K']==K)['recall']
                row['K'][str(K)]=dict(cached_C8_selected_recall=recall,delta_gt10_pp=(recall-baseline)*100,
                                     actual_full_H_exact_recall=actual,restriction_minus_full_H_pp=(recall-actual)*100)
            records.append(row)
        offset+=n
dump(RUN/'results/cached_support_diagnostic.json',dict(status='COMPLETE_READ_ONLY',post_gate=True,new_search_calls=0,new_training_runs=0,
     interpretation='All restricted actions were already measured at matching K/L/query/kernel/order; their costs are not online latency measurements. This diagnosis does not reopen the stopped gate.',
     source=identity(Path(__file__)),records=records))
for x in records:
    if x['split']=='cal':print(json.dumps(x))
