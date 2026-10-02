"""Remove an unused Router object from the generator and audit its dependency-free path.
This is not a new candidate, teacher budget or full label regeneration.
"""
import os,json,time,hashlib,subprocess,difflib
from pathlib import Path
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
import numpy as np
R=Path(__file__).resolve().parents[1];C=json.loads((R/'config.locked.json').read_text());start=time.perf_counter()
assert json.loads((R/'reviews/jobs_complete.json').read_text())['status']=='PASS'
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):assert not p.exists();p.write_text(json.dumps(v,indent=2)+'\n')
teacher='''
struct Teacher {
 acsg::IndexACSGFlat& idx;std::vector<uint8_t> spans;ResearchKernel kernel;std::unique_ptr<faiss::DistanceComputer>plain;ActualCount count;faiss::VisitedTable vt;std::vector<acsg::EnterPoint>ep;std::vector<acsg::Neighbor>legacy;uint64_t calls=0;
 explicit Teacher(acsg::IndexACSGFlat&i):idx(i),spans(make_spans(*i.acsg.final_graph,i.ntotal)),kernel(*i.acsg.final_graph,spans,i.ntotal),plain(acsg::storage_distance_computer(i.storage)),count(acsg::storage_distance_computer(i.storage)),vt(i.ntotal){ep.reserve(3);legacy.reserve(1501);}
 void search(const float*q,const std::array<int32_t,3>&e,int K,int L,faiss::idx_t*I,float*D,bool counting,bool original=false){ep.clear();for(int h:e)if(h>=0)ep.emplace_back(h,1);vt.advance();auto&dis=counting?static_cast<faiss::DistanceComputer&>(count):*plain;dis.set_query(q);if(original){idx.acsg.search_L=L;idx.acsg.search_new(dis,K,I,D,vt,2,ep,&legacy);}else kernel.search<true,false,true>(dis,vt,ep,L,K,I,D);++calls;}
};
'''
src=(R/'src/labels.cpp').read_text();old='Route route(c["anchor"],d);Engine e(*idx,route);';assert src.count(old)==1
new=src.replace('int main(int argc,char**argv)',teacher+'\nint main(int argc,char**argv)').replace(old,'Teacher e(*idx);').replace('route.calls==0&&','').replace('{"GT10_route_calls",route.calls}','{"GT10_route_calls",0},{"GT10_files_read",0}')
assert 'c["anchor"]' not in new and 'Route route' not in new
code=R/'src/labels_without_router.cpp';assert not code.exists();code.write_text(new);(R/'reviews/teacher_dependency.diff').write_text(''.join(difflib.unified_diff(src.splitlines(True),new.splitlines(True),fromfile='labels.cpp',tofile='labels_without_router.cpp')))
dump(R/'reviews/teacher_dependency_frozen.json',{'files':{str(p):ident(p) for p in [Path(__file__),R/'src/labels.cpp',code,R/'protocol.md']},'issue':'Original measured generator instantiated but never called a Router because Engine required it; remove this unused I/O dependency and verify same fixed-medoid labels on 32 fixed evenly spaced queries per dataset. No candidate labels or models replaced.'})
argv=json.loads((R/'reviews/compile_labels.job.json').read_text())['argv'];argv=[str(code) if x==str(R/'src/labels.cpp') else str(R/'bin/labels_without_router') if x==str(R/'bin/labels') else x for x in argv]
with (R/'logs/teacher_dependency_compile.log').open('x') as f:p=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT)
assert p.returncode==0;calls=0;records={}
for ds,dc in C['datasets'].items():
    ip=R/'inputs'/ds/'teacher_dependency';ip.mkdir();conf=dict(dc['labels']);conf.pop('anchor');d=conf['dimension'];positions=np.linspace(0,19999,32,dtype=int);q=np.fromfile(conf['queries'],'<f4').reshape(20000,d);q[positions].tofile(ip/'queries.f32');positions.astype('i8').tofile(ip/'positions.i64');conf.update(n=32,queries=str(ip/'queries.f32'));dump(ip/'config.json',conf);out=R/'results'/ds/'teacher_dependency'
    with (R/'logs'/f'{ds}_teacher_dependency.log').open('x') as f:p=subprocess.run(['taskset','-c','15',str(R/'bin/labels_without_router'),str(ip/'config.json'),str(out)],stdout=f,stderr=subprocess.STDOUT)
    assert p.returncode==0
    for name,t in [('ids.i32','<i4'),('distances.f32','<f4')]:
        original=np.fromfile(R/'results'/ds/'labels'/name,t).reshape(20000,100)[positions];assert original.tobytes()==(out/name).read_bytes()
    done=json.loads((out/'complete.json').read_text());assert done['GT10_route_calls']==0 and done['GT10_files_read']==0 and done['new_NSG_calls']==64;calls+=done['new_NSG_calls'];records[ds]={'same_complete_labels_rows':32,'GT10_input_paths_in_config':False,'new_NSG_calls':64}
assert calls+531968<=C['max_new_NSG']
dump(R/'reviews/teacher_dependency_audit.json',{'status':'PASS','seconds_including_compile_and_load':time.perf_counter()-start,'datasets':records,'new_NSG_calls':calls,'combined_E125_NSG_calls':calls+531968,'candidate_model_changes':0,'full_original_label_set_not_regenerated':True,'original_label_timing_includes_unused_router_load':True})
print('PASS',calls)
