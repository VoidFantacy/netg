from common import *
import shutil
t=time.perf_counter();assets=[]
for ds in DS:
    c=read(OLD/'configs'/f'{ds}.json');q=view(c['queries']);g=gt(c['test_gt'])
    perm=np.random.Generator(np.random.PCG64(19520261101)).permutation(len(q));half=min(512,len(q)//2)
    for window,sel in [('A',perm[:half]),('B',perm[half:2*half]),('qualification',np.arange(32))]:
        d=R/'storage/inputs'/ds/window;d.mkdir(parents=True,exist_ok=False)
        np.asarray(q[sel],dtype='<f4').tofile(d/'queries.f32');np.asarray(g[sel],dtype='<i4').tofile(d/'gt.i32');np.asarray(sel,dtype='<i4').tofile(d/'source_rows.i32')
        conf=dict(c);conf.update(window=window,queries=dict(path=str(d/'queries.f32'),format='raw_f32',n=len(sel),d=c['base']['d']),test_gt=dict(path=str(d/'gt.i32'),format='raw_i32',n=len(sel),k=100),output_dir=str(R/'storage'/('qualification' if window=='qualification' else 'results')/ds/window),Ls=LS,nav_methods=NAV,meta_dir=str(R/'storage/meta'/ds))
        dump(R/'configs'/f'{ds}.{window}.json',conf)
        assets += [ident(x) for x in d.iterdir()]
    for p in [c['index'],c['base']['path']]:assets.append(ident(p,False))
    for p in [c['table'],*c['router'].values()]:
        if isinstance(p,str) and Path(p).is_file():assets.append(ident(p))
    model=read(Path(c['models'])/'model.json');assets.append(ident(Path(c['models'])/'model.json'))
    for p in model['files'].values():
        if isinstance(p,str) and Path(p).is_file():assets.append(ident(p,Path(p).stat().st_size<32<<20))
dump(R/'input_freeze.json',dict(seed=19520261101,files=assets,seconds=time.perf_counter()-t,public_exposed=True,training=False,new_GT=False))
# The exact local replay body is generated from the current, read-only production source.
s=(REPO/'ACSG/ACSG.cpp').read_text();at=s.index('void ACSG::search_on_graph_new(');start=s.index('{',at);depth=0
for end in range(start,len(s)):
    if s[end]=='{':depth+=1
    if s[end]=='}':
        depth-=1
        if depth==0:break
body=s[start:end+1]
assert body.count('++trace->distance_evaluations;')==1
body=body.replace('++trace->distance_evaluations;','++trace->distance_evaluations; rec.scored.push_back(id);')
body=body.replace('if (trace) ++trace->expanded_count;','if (trace) ++trace->expanded_count; rec.expanded.push_back(n);')
body=body.replace('if (trace) ++trace->rejected_by_pool_bound_count;','if (trace) ++trace->rejected_by_pool_bound_count; rec.rejected.push_back(id);')
prefix='void replay_search(const acsg::Graph<int32_t>& graph, faiss::DistanceComputer& dis, faiss::VisitedTable& vt, int L, std::vector<acsg::Neighbor>& retset, const std::vector<acsg::EnterPoint>& enterpoints, Replay& rec)\n'
body=body.replace('{','{\n const int ntotal=graph.N, mode=2, query_id=1; acsg::SearchTrace tr; auto* trace=&tr;',1)
(R/'src/replay.inc').write_text(prefix+body+'\n')
(R/'src/e194.inc').write_text((E194/'src/benchmark.cpp').read_text().replace('int main(int argc,char**argv)','int e194_embedded_main(int argc,char**argv)'))
dump(R/'reviews/preparation.json',dict(status='PASS_PREPARED_SEVEN_DATASETS',seconds=time.perf_counter()-t,input_files=len(assets),source_kernel_sha=sha(REPO/'ACSG/ACSG.cpp'),replay_sha=sha(R/'src/replay.inc')))
print('PREPARED',len(assets),flush=True)
