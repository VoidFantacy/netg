import pathlib,subprocess,json,hashlib
R=pathlib.Path('/data/netg/ACSG'); D=pathlib.Path(__file__).resolve().parent.parent; E=R/'entry_method_exploration/20260915_gate_l2_r1_r100_v1'
p=D/'src/evaluate.cpp';s=(E/'src/evaluate.cpp').read_text();start=s.index('graph=std::make_unique<HNSW>(&space,ids.size()');end=s.index('graph->setEf(10);',s.index('else graph->saveIndex',start))+len('graph->setEf(10);');s=s[:start]+'require(fs::exists(out),"frozen router required");graph=std::make_unique<HNSW>(&space,out.string(),false,ids.size());graph->setEf(10);'+s[end:];p.write_text(s)
c=json.loads((E/'inputs/webvid2_5m_light_v1/eval_k100.json').read_text());c['soft']=next(m for m in c['methods'] if m['name']=='GT10-soft-t1');c['router']=str(E/'results/webvid2_5m_light_v1/k100/GT10-soft-t1.hnsw');c['e97_results']=str(E/'results/webvid2_5m_light_v1');(D/'config.json').write_text(json.dumps(c,indent=2)+'\n')
source=(D/'source_before/ACSG.cpp').read_text();flags=['c++','-std=c++17','-O3','-g','-march=native','-fopenmp','-fPIC','-I'+str(R/'build/_deps/json-src/include'),'-I'+str(R),'-I'+str(R/'faiss'),'-I'+str(D/'src')];commands=[]
for name in ['original','prefetch','active_pool','combined']:
 s=source;begin=s.index('void ACSG::search_on_graph_new(');head=s[:begin];body=s[begin:]
 if name in ['prefetch','combined']:
  needle='for (int m = 0; m < graph.K; m++) {\n                int id = (int)graph.at(n, m);';assert body.count(needle)==1
  body=body.replace(needle,'''for (int m = 0; m < graph.K; m++) {
                if (m + 1 < graph.K) {
                    int next_id = (int)graph.at(n, m + 1);
                    if (next_id >= 0 && next_id < ntotal) {
                        __builtin_prefetch(vt.visited.data() + next_id, 0, 3);
                        __builtin_prefetch(diagnosis_base + size_t(next_id) * diagnosis_dim, 0, 3);
                    }
                }
                int id = (int)graph.at(n, m);''')
  head='extern const float* diagnosis_base;\nextern __SIZE_TYPE__ diagnosis_dim;\n'+head
 if name in ['active_pool','combined']:
  needle='insert_into_pool(retset.data(), L, nn)';assert body.count(needle)==1;body=body.replace(needle,'insert_into_pool(retset.data(), std::min(L, num_ids), nn)')
 src=D/f'src/ACSG.{name}.cpp';src.write_text(head+body);obj=D/f'bin/ACSG.{name}.o';cmd=flags+['-c',str(src),'-o',str(obj)];commands.append(cmd);subprocess.run(cmd,check=True)
 cmd=flags+['-no-pie',str(D/'src/diagnose.cpp'),str(obj),str(R/'build/ACSG/libACSG.a'),str(R/'build/faiss/faiss/libfaiss.a'),str(R/'build/MRNN_Descent/libmrnndescent.a'),'-lopenblas','-llapack','-lz','-lpthread','-ldl','-o',str(D/f'bin/diagnose.{name}')];commands.append(cmd);subprocess.run(cmd,check=True);print('BUILT',name,flush=True)
(D/'reviews/build.json').write_text(json.dumps({'commands':commands,'files':{str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['src','bin'] for p in (D/folder).rglob('*') if p.is_file()}},indent=2)+'\n')
