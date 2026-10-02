from build_exact import C,R,load_flat,query_rows,dump,faiss,threadpool_info,os
import json,sys,time
from pathlib import Path
import numpy as np
from common import ident

def main():
    start=time.perf_counter();c=json.loads(Path(sys.argv[1]).read_text());p=Path(c['output']);out=p/'selection'
    for path,v in json.loads((out/'selection_frozen.json').read_text())['files'].items():assert ident(path)==v
    rows=np.fromfile(out/'added_rows.i32','<i4');assert len(rows)==len(np.unique(rows))==1024
    fit=np.fromfile(c['fit_queries'],'<f4').reshape(c['fit_n'],c['dimension'])
    index,load=load_flat(c,start);record=query_rows(index,np.ascontiguousarray(fit[rows]),c,'additional1024',out,start);del index
    dump(out/'additional_complete.json',{'status':'COMPLETE_UNVALIDATED','seconds':time.perf_counter()-start,'new_GT':1024,
        'base_load_flat_build_seconds':load,'affinity':sorted(os.sched_getaffinity(0)),
        'faiss_threads':faiss.omp_get_max_threads(),'threadpools':threadpool_info(),**record})

if __name__=='__main__':main()
