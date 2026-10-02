import pathlib,shutil,json,hashlib
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent;E=D.parent/'20260916_nsg_search_optimization_v1';F=D.parent/'20260916_search_cost_diagnosis_v1'
for name in ['summary.md','spec.md','s-target.md','s-experiment.md','ACSG/ACSG.cpp','ACSG/ACSG.h','ACSG/detail/CandidatePool.h']:
 p=D/'source_before'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,p)
for sub in ['common','probe_common']:
 p=D/'src'/sub;p.mkdir()
 for n in ['evaluate.cpp','native_common.hpp','topology.hpp']:shutil.copy2(E/'src'/n,p/n)
 shutil.copytree(E/'src/hnswlib',p/'hnswlib')
c=json.loads((E/'configs/webvid2_5m_light_v1.json').read_text());c.update(K=100,L=1250,reference_e99=str(E/'results/webvid2_5m_light_v1'),router=str(D.parent/'20260915_gate_l2_r1_r100_v1/results/webvid2_5m_light_v1/k100/GT10-soft-t1.hnsw'))
c['soft']=next(x for x in c['methods'] if x['name']=='GT10-soft-t1');(D/'config.json').write_text(json.dumps(c,indent=2)+'\n')
s=(F/'src/diagnose.cpp').read_text();a=s.index('static uintptr_t pcs');b=s.index('static json kernel_bench');helpers=s[a:b]
(D/'src/profile_helpers.hpp').write_text('#include <sys/time.h>\n#include <signal.h>\n#include <ucontext.h>\n#include <dlfcn.h>\n'+helpers)
protected=[R/'ACSG/ACSG.cpp',R/'ACSG/detail/CandidatePool.h',R/'build/ACSG/libACSG.a',E/'bin/libACSG.optimized.a',E/'report.md',E/'complete.json',E/'results/metrics.csv',F/'report.md']
(D/'reviews/protected.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected},indent=2)+'\n')
