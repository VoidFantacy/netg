import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
os.sched_setaffinity(0,range(8))
import ast,hashlib,json,time,types
from pathlib import Path
import numpy as np,faiss
faiss.omp_set_num_threads(8)
R=Path(__file__).resolve().parent;COST=R.parent/'hybrid_full_build_cost_v1'
C=json.loads((COST/'config.locked.json').read_text());REF=json.loads((COST/'reviews/validation_references.json').read_text())
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
class GTProxy:
    def __init__(self,gt):self.gt=gt;self.shape=gt.shape;self.trace=[];self.rows=set()
    def __getitem__(self,row):
        row=int(row);record={'row':row,'source':'cluster','new_row':row not in self.rows,'ranks_read':0};self.trace.append(record);self.rows.add(row)
        def iterator():
            for v in self.gt[row]:record['ranks_read']+=1;yield v
        return iterator()
    def ravel(self):
        for row in range(len(self.gt)):
            record={'row':row,'source':'fallback','new_row':row not in self.rows,'ranks_read':0};self.trace.append(record);self.rows.add(row)
            for v in self.gt[row]:record['ranks_read']+=1;yield v
class KmeansCapture:
    def __init__(self,*args,**kwargs):self.km=faiss.Kmeans(*args,**kwargs);self.q=None;self.search_result=None
    def train(self,q):self.q=q.copy();return self.km.train(q)
    @property
    def centroids(self):return self.km.centroids
    @property
    def index(self):
        parent=self
        class Index:
            def search(self,q,k):
                parent.search_result=parent.km.index.search(q,k);return parent.search_result
        return Index()
class KmeansReplay:
    def __init__(self,cap):self.cap=cap
    def train(self,q):assert np.array_equal(q,self.cap.q)
    @property
    def centroids(self):return self.cap.centroids
    @property
    def index(self):
        cap=self.cap
        class Index:
            def search(self,q,k):assert k==1 and np.array_equal(q,cap.q);return cap.search_result
        return Index()
def main():
    # This analysis is barred until the complete timed pipeline and its audit finish.
    assert json.loads((COST/'reviews/independent_audit.json').read_text())['status']=='PASS'
    start=time.perf_counter();(R/'results').mkdir();(R/'reviews').mkdir();records={};paths=[Path(__file__),R/'protocol.md',R/'theory.md']
    for ds,c in C['datasets'].items():paths += [Path(c['qgt_queries']),Path(c['selector_source']),Path(REF[ds]['qgt_gt']),Path(REF[ds]['model']['ids'])]
    dump(R/'reviews/frozen.json',{'inputs':{str(p):ident(p) for p in dict.fromkeys(paths)},'unix':time.time()})
    for ds,c in C['datasets'].items():
        t=time.perf_counter();d=c['dimension'];q=np.fromfile(c['qgt_queries'],'<f4').reshape(5000,d+1)[:,1:].copy()
        g=np.fromfile(REF[ds]['qgt_gt'],'<i4').reshape(5000,101);assert (g[:,0]==100).all();gt=g[:,1:]
        source=Path(c['selector_source']);nodes=[x for x in ast.parse(source.read_text()).body if isinstance(x,ast.FunctionDef) and x.name in ['normalize','choose_unique_gt_hubs']]
        captures=[]
        def factory(*a,**kw):cap=KmeansCapture(*a,**kw);captures.append(cap);return cap
        scope={'np':np,'faiss':types.SimpleNamespace(Kmeans=factory)};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),scope)
        proxy=GTProxy(gt);h,details=scope['choose_unique_gt_hubs'](q,proxy,c['H'],20260828,25);cap=captures[0];assert len(captures)==1
        assert h.tobytes()==Path(REF[ds]['model']['ids']).read_bytes()
        scope['faiss']=types.SimpleNamespace(Kmeans=lambda *a,**kw:KmeansReplay(cap));full,fulldetail=scope['choose_unique_gt_hubs'](q,gt,c['H'],20260828,25)
        assert np.array_equal(h,full) and details==fulldetail
        assignment=cap.search_result[1][:,0];centroids=scope['normalize'](cap.centroids.astype('f4'));first=[];used=set();selected=[];expected_trace=[];max_first_ties=0
        for cluster in range(c['H']):
            members=np.flatnonzero(assignment==cluster)
            if not len(members):continue
            s=cap.q[members]@centroids[cluster];order=members[np.argsort(-s)];first.append(int(order[0]));max_first_ties=max(max_first_ties,int(np.sum(s==s.max())))
            found=False
            for row in order:
                expected_trace.append(int(row))
                for candidate in gt[row]:
                    if int(candidate) not in used:used.add(int(candidate));selected.append(int(candidate));found=True;break
                if found:break
        if len(selected)<c['H']:
            for row in range(5000):
                expected_trace.append(row)
                for candidate in gt[row]:
                    if int(candidate) not in used:used.add(int(candidate));selected.append(int(candidate))
                    if len(selected)==c['H']:break
                if len(selected)==c['H']:break
        assert np.array_equal(np.array(sorted(selected),dtype='i4'),h)
        assert [x['row'] for x in proxy.trace]==expected_trace
        unique=np.array(sorted(proxy.rows),dtype='i4');fallback=[x for x in proxy.trace if x['source']=='fallback']
        record={'H':len(h),'unique_GT_rows_read':len(unique),'total_row_accesses':len(proxy.trace),'fallback_row_accesses':len(fallback),
            'first_representatives':len(first),'only_first_representatives':set(first)==proxy.rows,'unused_GT_rows':5000-len(unique),
            'ranks_read_max':max(x['ranks_read'] for x in proxy.trace),'ranks_read_sum':sum(x['ranks_read'] for x in proxy.trace),
            'representative_max_score_ties':max_first_ties,'exact_H_recovery':True,'full_vs_proxy_same_H':True,'seconds':time.perf_counter()-t}
        dump(R/'results'/f'{ds}.trace.json',proxy.trace)
        np.savez(R/'results'/f'{ds}.npz',unique_rows=unique,first_representatives=np.array(first,dtype='i4'),assignment=assignment,centroids=cap.centroids,selected_hubs=h)
        records[ds]=record;print(ds,record,flush=True)
    for p,v in json.loads((R/'reviews/frozen.json').read_text())['inputs'].items():assert ident(p)==v
    dump(R/'results/summary.json',{'status':'TRACE_AND_REPLAY_VERIFIED','datasets':records,'new_kmeans_fits':2,'new_exact_GT':0,'new_NSG':0,'new_ANN':0,'new_profiles':0,
        'seconds':time.perf_counter()-start,'default_changed':False,'wall_savings_measured':False})
if __name__=='__main__':main()
