import ast, types
from pathlib import Path
import numpy as np

def selector_scope(source, kmeans_factory):
    nodes=[x for x in ast.parse(Path(source).read_text()).body if isinstance(x,ast.FunctionDef) and x.name in ['normalize','choose_unique_gt_hubs']]
    assert len(nodes)==2
    scope={'np':np,'faiss':types.SimpleNamespace(Kmeans=kmeans_factory)}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),scope)
    return scope

class Replay:
    def __init__(self,q,centroids,search):self.q=q;self.centroids=centroids;self.search_result=search
    def train(self,q):assert np.array_equal(q,self.q)
    @property
    def index(self):
        parent=self
        class Index:
            def search(self,q,k):
                assert k==1 and np.array_equal(q,parent.q)
                return parent.search_result
        return Index()

class LazyGT:
    def __init__(self,n,k,search_rows,batch=256):
        self.shape=(n,k);self.search_rows=search_rows;self.batch=batch
        self.ids=np.full((n,k),-1,dtype='i8');self.dist=np.full((n,k),np.nan,dtype='f4')
        self.cached=np.zeros(n,dtype=bool);self.trace=[];self.generated=[];self.computed=0;self.overlap_checks=0
    def generate(self,rows,phase):
        rows=np.asarray(rows,dtype='i4');assert len(rows)>0
        dd,ii=self.search_rows(rows,phase)
        assert dd.shape==ii.shape==(len(rows),self.shape[1]) and np.isfinite(dd).all() and (ii>=0).all()
        overlap=self.cached[rows]
        if overlap.any():
            assert np.array_equal(self.ids[rows[overlap]],ii[overlap]),'overlap ID mismatch'
            assert np.array_equal(self.dist[rows[overlap]].view('u4'),dd[overlap].view('u4')),'overlap distance bit mismatch'
        self.overlap_checks+=int(overlap.sum());self.computed+=len(rows)
        self.ids[rows]=ii;self.dist[rows]=dd;self.cached[rows]=True
        self.generated.append({'phase':phase,'rows':rows.tolist(),'overlap_rows':int(overlap.sum())})
    def prefetch(self,rows):
        rows=np.unique(np.asarray(rows,dtype='i4'))
        for lo in range(0,len(rows),self.batch):self.generate(rows[lo:lo+self.batch],'representative_prefetch')
    def row(self,row,source):
        row=int(row);hit=bool(self.cached[row]);record={'row':row,'source':source,'cache_hit':hit,'ranks_read':0};self.trace.append(record)
        if not hit:
            lo=row//self.batch*self.batch;hi=min(lo+self.batch,self.shape[0])
            self.generate(np.arange(lo,hi,dtype='i4'),'fallback_source_block')
        for node in self.ids[row]:record['ranks_read']+=1;yield node
    def __getitem__(self,row):return self.row(row,'cluster')
    def ravel(self):
        for row in range(self.shape[0]):yield from self.row(row,'fallback')
