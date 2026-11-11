from common import *
import faiss
faiss.omp_set_num_threads(8)
receipts=[]
for ds in DS:
    c=read(R/f'configs/{ds}.confirmation.json');q=np.asarray(view(c['queries']),dtype='<f4');x=np.asarray(view(c['base']),dtype='<f4');t=time.perf_counter()
    index=faiss.IndexFlatIP(x.shape[1]);index.add(x);D,I=index.search(q,101)
    np.asarray(I[:,:100],dtype='<i4').tofile(c['test_gt']['path'])
    s=Path(c['test_gt']['path']).parent;D[:,:100].astype('<f4').tofile(s/'confirmation.gt.scores.f32')
    checks=[]
    for row in np.linspace(0,len(q)-1,8,dtype=int):
        scores=np.empty(len(x),np.float64)
        for lo in range(0,len(x),32768):scores[lo:lo+32768]=np.asarray(x[lo:lo+32768],dtype=np.float64)@np.asarray(q[row],dtype=np.float64)
        order=np.lexsort((np.arange(len(scores)),-scores))[:100]
        equal=set(order)==set(I[row,:100]);threshold=float(scores[order[-1]])
        missing=[int(v) for v in order if v not in I[row,:100]]
        extra=[int(v) for v in I[row,:100] if v not in order]
        max_tie_gap=max([abs(float(scores[v])-threshold) for v in missing+extra] or [0.])
        assert equal or max_tie_gap<2e-6,(ds,row,max_tie_gap)
        checks.append(dict(row=int(row),set_equal=equal,missing=missing,extra=extra,max_boundary_score_gap=max_tie_gap,top1_equal=int(order[0])==int(I[row,0])))
        assert checks[-1]['top1_equal'],checks[-1]
    rec=dict(dataset=ds,status='PASS_EXACT_IP_GT_AND_FLOAT64_CHECKS',n=len(q),base_n=len(x),metric='raw_IP',threads=8,seconds=time.perf_counter()-t,gt=ident(c['test_gt']['path']),checks=checks,near_boundary_queries=int(np.count_nonzero(D[:,99]-D[:,100]<2e-6)),index_flat_library=faiss.__version__,normalization='none')
    receipts.append(rec);dump(R/f'reviews/exact_gt_{ds}.json',rec);print(json.dumps(rec),flush=True)
    del index,x
dump(R/'reviews/exact_gt_all.json',receipts)
