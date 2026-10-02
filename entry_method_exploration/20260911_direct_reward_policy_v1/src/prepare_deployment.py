from common import *

assert read(O/'results/cache_gate.json')['status']=='PASS_REAL_DEVELOPMENT_ALLOWED'
assert read(O/'reviews/model_and_cache_verification.json')['status']=='PASS'
check_freeze(O/'models/frozen_after_training.json')
for name in ['evaluate.cpp','benchmark_with_nsg.cpp','legacy_reference.cpp']:
    assert not (O/'src'/name).exists();shutil.copy2(E30/'src'/name,O/'src'/name)
s=(O/'src/benchmark_with_nsg.cpp').read_text()
s=s.replace('uint32_t ndc=0;','uint32_t ndc=0;\n    std::array<int32_t,8> candidates{-1,-1,-1,-1,-1,-1,-1,-1};\n    int32_t action_slot=-1;',1)
s=s.replace('mutable hnswlib::InnerProductSpace exact_space;', '''mutable hnswlib::InnerProductSpace exact_space;
    bool c8=false;
    std::vector<float> anchor;
    std::vector<std::unique_ptr<Policy>> candidate_policies;
    std::map<int32_t,int32_t> real_to_local;''',1)
s=s.replace('        if(exact)return;', '''        c8=c.value("family",std::string())=="c8";
        if(c8) {
            require(k==3 && canonical_order && !slot_labels,"invalid C8 policy");
            anchor=read_raw<float>(c.at("c8_anchor"));require(anchor.size()==h*dim,"anchor shape");
            for(size_t j=0;j<h;++j)real_to_local[mapping[j]]=int32_t(j);
            size_t i=0;
            for(auto kid:c.at("c8_policies")) {
                kid["dim"]=dim;
                require(kid.at("family")=="profile" && kid.at("k")==3,"fixed candidate policy required");
                require(read_raw<int32_t>(kid.at("mapping"))==mapping,"candidate mapping mismatch");
                candidate_policies.push_back(std::make_unique<Policy>(kid,index_file.string()+"."+std::to_string(i++),counted,load));
            }
            require(candidate_policies.size()==2,"two fixed proposal policies required");return;
        }
        if(exact)return;''',1)
needle='        if(exact) {\n            auto fn=exact_space.get_dist_func();'
replacement='''        if(c8) {
            std::set<int32_t> chosen;uint64_t count=0;
            for(const auto& policy:candidate_policies) {
                auto proposal=policy->route(q);count+=proposal.ndc;
                for(int32_t id:proposal.ids)chosen.insert(real_to_local.at(id));
            }
            auto fn=exact_space.get_dist_func();void* param=exact_space.get_dist_func_param();
            std::vector<std::pair<float,int32_t>> ranked(h);
            for(size_t j=0;j<h;++j)ranked[j]={fn(q,anchor.data()+j*dim,param),int32_t(j)};
            std::sort(ranked.begin(),ranked.end(),[&](auto a,auto b){return a.first<b.first||(a.first==b.first&&mapping[a.second]<mapping[b.second]);});
            for(auto r:ranked){if(chosen.size()==8)break;chosen.insert(r.second);}
            std::vector<int32_t> ids(chosen.begin(),chosen.end());
            std::sort(ids.begin(),ids.end(),[&](int32_t a,int32_t b){return mapping[a]<mapping[b];});
            require(ids.size()==8,"C8 size mismatch");
            double norm=0;for(size_t j=0;j<dim;++j)norm+=double(q[j])*q[j];norm=std::sqrt(norm);
            require(norm>0 && std::isfinite(norm),"invalid query norm");
            std::array<double,8> scores{};
            for(size_t j=0;j<8;++j) {
                result.candidates[j]=ids[j];
                double value=0;for(size_t v=0;v<dim;++v)value+=(double(q[v])/norm)*double(w[ids[j]*dim+v]);
                scores[j]=value/.05;
            }
            double best=-std::numeric_limits<double>::infinity();int32_t slot=0;
            for(size_t a=0;a<8;++a)for(size_t b=a+1;b<8;++b)for(size_t e=b+1;e<8;++e,++slot) {
                double value=(scores[a]+scores[b])+scores[e];
                if(value>best) {
                    best=value;result.action_slot=slot;
                    result.labels={ids[a],ids[b],ids[e]};result.ids={mapping[ids[a]],mapping[ids[b]],mapping[ids[e]]};
                }
            }
            require(slot==56 && result.action_slot>=0,"action enumeration mismatch");
            result.ndc=counted?uint32_t(count+h+8):0;return result;
        }
        if(exact) {
            auto fn=exact_space.get_dist_func();'''
assert s.count(needle)==1;s=s.replace(needle,replacement)
s=s.replace('#undef main','#undef main\n#include <map>',1)
(O/'src/benchmark_with_nsg.cpp').write_text(s)
s=(O/'src/evaluate.cpp').read_text()
# Exactly one full warmup per point, then five rotated independent wall runs.
assert s.count('2*reps+1')==2;s=s.replace('2*reps+1','reps+2')
s=s.replace('if(measured){plain(*index,*p.p,q,d,worker,warm);calls+=n;}','if(measured && rep==0){plain(*index,*p.p,q,d,worker,warm);calls+=n;}')
s=s.replace('if(measured)bit_compare(warm,timed);','if(measured && rep==0)bit_compare(warm,timed);')
s=s.replace('    write_raw(out/"ids.i32",ids);write_raw(out/"distances.f32",distances);write_raw(out/"entry_ids.i32",entries);', '''    write_raw(out/"ids.i32",ids);write_raw(out/"distances.f32",distances);write_raw(out/"entry_ids.i32",entries);
    std::vector<int32_t> candidates(a.routes.size()*8),slots(a.routes.size());
    for(size_t i=0;i<a.routes.size();++i) {
        std::copy(a.routes[i].candidates.begin(),a.routes[i].candidates.end(),candidates.begin()+i*8);
        slots[i]=a.routes[i].action_slot;
    }
    write_raw(out/"candidates.i32",candidates);write_raw(out/"action_slots.i32",slots);''')
s=s.replace('    compare(a,b);','    compare(a,b);\n    for(size_t i=0;i<a.routes.size();++i)require(a.routes[i].candidates==b.routes[i].candidates && a.routes[i].action_slot==b.routes[i].action_slot,"candidate/action parity failed");',1)
s=s.replace('One raw-query profile route, mapping/canonicalization, original NSG, preallocated output;', 'Raw query through full method: fixed HNSW proposals plus full-H candidate fill plus learned C8 scores and complete-action argmax for C8 methods, mapping/canonicalization, original NSG, preallocated output;')
(O/'src/evaluate.cpp').write_text(s)
(O/'bin').mkdir()
build=read(E28/'bin/evaluate.build.json')
argv=[x.replace(str(E28/'src/evaluate.cpp'),str(O/'src/evaluate.cpp')).replace(str(E28/'bin/evaluate'),str(O/'bin/evaluate')) for x in build['argv']]
start=time.time()
with (O/'logs/build.log').open('x') as log:result=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0,'see build.log'
dump(O/'bin/evaluate.build.json',dict(argv=argv,seconds=time.time()-start,exit_code=result.returncode,
    sources=[identity(O/'src'/x) for x in ['evaluate.cpp','benchmark_with_nsg.cpp','legacy_reference.cpp']],binary=identity(O/'bin/evaluate'),
    changes='C8 policy and parity output; one warmup then five wall repetitions; original kernel and direct3 paths retained'))
dump(O/'reviews/deployment_build.json',dict(status='PASS',NSG_calls=0,query_calls=0))
print('DEPLOYMENT_BUILD_PASS',flush=True)
