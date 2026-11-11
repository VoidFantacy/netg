// E188: old scientific implementation is included read-only for controls.
#define main e187_preserved_main
#include "../../20261028_adaptive_completion_pilot_v1/src/pilot.cpp"
#undef main

namespace e188 {
using namespace e183;
using A=e187::Backend::Approx;
constexpr size_t NF=12;
struct Meter {
 std::array<double,10> sec{};uint64_t scans=0,exact=0,blocks=0;
 std::vector<uint64_t> per_query;
};
template<bool P,class F> void measured(Meter& st,int part,F f){if constexpr(P){auto t=Clock::now();f();st.sec[part]+=seconds(t);}else f();}
struct Linear {size_t nf=0;double intercept=0;std::array<double,NF> mean{},scale{},coef{};
 void load(const json& m){nf=m.at("n_features");intercept=m.at("intercept");require(nf<=NF,"feature bounds");for(size_t j=0;j<nf;++j){mean[j]=m.at("mean")[j];scale[j]=m.at("scale")[j];coef[j]=m.at("coef")[j];}}
 double predict(const std::array<double,NF>& x)const{double v=intercept;for(size_t j=0;j<nf;++j)v+=(x[j]-mean[j])/scale[j]*coef[j];return std::max(0.,v);}
};
struct Blocks {
 std::vector<float> cent;std::vector<int32_t> ids;std::vector<uint8_t> codes;std::vector<uint64_t> off,regions;
 Blocks(const json& c){fs::path p=c.at("blocks");if(!fs::exists(p/"blocks.json"))return;
 cent=read_raw<float>((p/"block_centres.f32").string());ids=read_raw<int32_t>((p/"block_ids.i32").string());codes=read_raw<uint8_t>((p/"block_codes.u8").string());off=read_raw<uint64_t>((p/"block_offsets.u64").string());regions=read_raw<uint64_t>((p/"region_blocks.u64").string());
 size_t N=c.at("base").at("n"),d=c.at("base").at("d");require(ids.size()==N&&codes.size()==N*16&&regions.size()==1025&&off.back()==N&&regions.back()+1==off.size()&&cent.size()==regions.back()*d,"block layout");for(size_t i=1;i<off.size();++i)require(off[i]>off[i-1]&&off[i]-off[i-1]<=128,"block size");}
 size_t bytes()const{return cent.size()*4+ids.size()*4+codes.size()+off.size()*8+regions.size()*8;}
};
struct Engine {
 e187::Backend old;Blocks bl;Linear old_r,gain;std::vector<double> costs;
 std::vector<std::pair<float,int>> coarse_buf,block_rank;
 std::vector<A> heap,all;std::vector<int32_t> sorted,candidates;
 std::vector<Posting::Record> merged;std::vector<float> values;
 float lut[16][256];double norm=0;std::array<double,1024> count{},top{},sum{};
 Engine(const json& c):old(c),bl(c){old_r.load(old.models.at("REG-R"));fs::path p=c.at("blocks");if(fs::exists(p/"selector.json")){auto m=read_json(p/"selector.json");gain.load(m.at("gain"));costs=m.at("cost_coef").get<std::vector<double>>();}
 coarse_buf.reserve(1024);heap.reserve(96);all.reserve(8192);candidates.reserve(96);sorted.reserve(100);merged.reserve(196);values.reserve(96);block_rank.reserve(1024);}
 void coarse(const float* q){coarse_buf.resize(1024);for(size_t r=0;r<1024;++r)coarse_buf[r]={old.score(q,old.cent.data()+r*old.d,old.d),int(r)};std::partial_sort(coarse_buf.begin(),coarse_buf.begin()+8,coarse_buf.end());coarse_buf.resize(8);}
 void summaries(const float* q,const int32_t* R,const float* D,size_t K){norm=0;for(size_t j=0;j<old.d;++j)norm+=double(q[j])*q[j];count.fill(0);top.fill(0);sum.fill(0);for(size_t j=0;j<K;++j){int r=old.id_region[R[j]];count[r]++;top[r]+=j<std::min<size_t>(10,K);sum[r]+=D[j];}}
 std::array<double,NF> features(size_t rank,const float* D,size_t K){std::array<double,NF>x{};int r=coarse_buf[rank].second;double scale=std::max(1e-6,std::abs(double(coarse_buf[0].first)));
 x[0]=double(rank)/7;x[1]=(coarse_buf[rank].first-coarse_buf[0].first)/scale;x[2]=std::log1p(double(old.offsets[r+1]-old.offsets[r]))/std::log1p(double(old.N));x[3]=std::sqrt(norm);x[4]=(coarse_buf[7].first-coarse_buf[0].first)/scale;
 double z=std::max(1e-6,std::abs(double(D[K-1])));x[5]=count[r]/K;x[6]=top[r]/std::min<size_t>(10,K);x[7]=count[r]?(sum[r]/count[r]-D[K-1])/z:0;x[8]=(D[K-1]-D[0])/z;x[9]=(D[K-1]-coarse_buf[rank].first)/z;
 if(!bl.regions.empty()){x[10]=std::log1p(double(bl.regions[r+1]-bl.regions[r]));x[11]=double(std::min<uint64_t>(1024,old.offsets[r+1]-old.offsets[r]))/1024.;}return x;}
 double cost(int r)const{double b=bl.regions[r+1]-bl.regions[r],s=std::min<uint64_t>(1024,old.offsets[r+1]-old.offsets[r]);std::array<double,5> x{1,b,b*std::log2(std::max(2.,b)),s,std::min(48.,s)};double v=0;for(size_t j=0;j<5;++j)v+=costs[j]*x[j];return std::max(1e-9,v);}
 template<bool P> std::array<int,2> select(const float* q,const int32_t* R,const float* D,size_t K,const std::string& method,Meter& st){
 measured<P>(st,0,[&]{coarse(q);});std::array<std::pair<double,size_t>,8> ranks;
 measured<P>(st,1,[&]{if(method=="REG-R"){
 for(size_t j=0;j<8;++j){auto f=old.features(q,coarse_buf,j,R,D,K,true);ranks[j]={-old.predict("REG-R",f),j};}}
 else {summaries(q,R,D,K);for(size_t j=0;j<8;++j){auto x=features(j,D,K);double v=method=="BLOCK-C2048"?gain.predict(x)/cost(coarse_buf[j].second):old_r.predict(x);ranks[j]={-v,j};}}
 std::sort(ranks.begin(),ranks.end());});return {{coarse_buf[ranks[0].second].second,coarse_buf[ranks[1].second].second}};}
 template<bool P> void prepare(const float* q,const int32_t* R,size_t K,Meter& st){measured<P>(st,2,[&]{for(size_t m=0;m<16;++m)for(size_t z=0;z<256;++z)lut[m][z]=old.score(q+m*old.sub,old.book.data()+(m*256+z)*old.sub,old.sub);});sorted.assign(R,R+K);std::sort(sorted.begin(),sorted.end());candidates.clear();}
 void offer(int32_t id,const uint8_t* code,uint64_t arrival,size_t cap,bool oracle){if(std::binary_search(sorted.begin(),sorted.end(),id))return;float v=0;for(size_t m=0;m<16;++m)v+=lut[m][code[m]];A a{v,arrival,id};if(oracle)all.push_back(a);else if(heap.size()<cap){heap.push_back(a);std::push_heap(heap.begin(),heap.end(),e187::Backend::Less{});}else if(e187::Backend::approx_less(a,heap.front())){std::pop_heap(heap.begin(),heap.end(),e187::Backend::Less{});heap.back()=a;std::push_heap(heap.begin(),heap.end(),e187::Backend::Less{});}}
 void finish(size_t cap,bool oracle){auto& v=oracle?all:heap;std::sort(v.begin(),v.end(),e187::Backend::approx_less);if(v.size()>cap)v.resize(cap);for(auto& a:v)candidates.push_back(a.id);}
 template<bool P> void full(const std::array<int,2>& rs,Meter& st,bool oracle){heap.clear();all.clear();uint64_t arrival=0;measured<P>(st,4,[&]{for(int r:rs)for(size_t i=old.offsets[r];i<old.offsets[r+1];++i){++st.scans;offer(old.ids[i],old.codes.data()+i*16,arrival++,96,oracle);}finish(96,oracle);});}
 template<bool P> void region(const float* q,int r,size_t budget,Meter& st,bool oracle){require(!bl.regions.empty(),"blocks prepared");heap.clear();all.clear();
 measured<P>(st,3,[&]{block_rank.clear();for(size_t b=bl.regions[r];b<bl.regions[r+1];++b)block_rank.emplace_back(old.score(q,bl.cent.data()+b*old.d,old.d),int(b));std::sort(block_rank.begin(),block_rank.end());st.blocks+=block_rank.size();});
 measured<P>(st,4,[&]{size_t consumed=0;uint64_t arrival=0;for(auto v:block_rank){size_t b=v.second,len=bl.off[b+1]-bl.off[b];if(consumed+len>budget)continue;for(size_t i=bl.off[b];i<bl.off[b+1];++i){offer(bl.ids[i],bl.codes.data()+i*16,arrival++,48,oracle);}consumed+=len;if(consumed==budget)break;}st.scans+=consumed;require(consumed<=budget,"hard scan budget");finish(48,oracle);});}
 template<bool P> void refine(faiss::DistanceComputer& dc,int32_t* R,float* D,size_t K,Meter& st,bool oracle){measured<P>(st,5,[&]{values.clear();for(int id:candidates)values.push_back(dc(id));st.exact+=candidates.size();});
 measured<P>(st,6,[&]{merged.clear();for(size_t j=0;j<K;++j)merged.push_back({R[j],D[j],uint32_t(j),false});if(oracle){for(size_t j=0;j<candidates.size();++j)merged.push_back({candidates[j],values[j],uint32_t(K+j),false});std::stable_sort(merged.begin(),merged.end(),Posting::better);merged.resize(K);}else{std::make_heap(merged.begin(),merged.end(),Posting::better);for(size_t j=0;j<candidates.size();++j)if(values[j]<merged.front().distance){std::pop_heap(merged.begin(),merged.end(),Posting::better);merged.back()={candidates[j],values[j],uint32_t(K+j),false};std::push_heap(merged.begin(),merged.end(),Posting::better);}std::sort(merged.begin(),merged.end(),Posting::better);}for(size_t j=0;j<K;++j){R[j]=merged[j].id;D[j]=merged[j].distance;}});}
 template<bool P> void complete(faiss::DistanceComputer& dc,const float* q,int32_t* R,float* D,size_t K,const std::string& method,Meter& st,bool oracle=false){auto rs=select<P>(q,R,D,K,method,st);
 if(method=="REG-R"){measured<P>(st,2,[&]{/* old candidates called below to preserve allocation path */});
 // Exact legacy phases are profiled by a separate copy of its LUT/scan below.
 prepare<P>(q,R,K,st);full<P>(rs,st,oracle);measured<P>(st,7,[&]{e187::merge(dc,K,R,D,candidates,oracle);st.exact+=candidates.size();});return;}
 prepare<P>(q,R,K,st);if(method=="OPT-R")full<P>(rs,st,oracle);else {size_t budget=method=="BLOCK-R512"?512:method=="BLOCK-R8192"?8192:2048;region<P>(q,rs[0],budget/2,st,oracle);region<P>(q,rs[1],budget/2,st,oracle);require(candidates.size()<=96,"exact cap");}refine<P>(dc,R,D,K,st,oracle);}
};

template<bool P> void run(acsg::IndexACSGFlat& idx,const std::vector<float>& q,int L,const std::string& method,Router& router,Posting& post,Engine& e,Batch& b,Meter& st){
 if constexpr(!P){if(method=="GT10"||method=="B32"||method=="REG-R"){e187::Stats old; e187::run(idx,q,L,method,router,post,e.old,b,old);st.scans=old.scanned;st.exact=old.scored;return;}}
 idx.acsg.search_L=L;std::vector<std::vector<acsg::EnterPoint>> eps(b.n);measured<P>(st,9,[&]{for(size_t i=0;i<b.n;++i){auto r=router.route(q.data()+i*idx.d);for(int j=0;j<3;++j){b.entries[3*i+j]=r.ids[j];b.profile_distances[3*i+j]=r.distances[j];eps[i].emplace_back(r.ids[j],1.f);}}});
 faiss::VisitedTable vt(idx.ntotal);std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx.storage));std::vector<acsg::Neighbor> ret;std::vector<faiss::idx_t> ids(b.k);std::vector<int32_t> current(b.k);st.per_query.reserve(b.n*3);
 for(size_t i=0;i<b.n;++i){const float* qi=q.data()+i*idx.d;dc->set_query(qi);vt.advance();measured<P>(st,8,[&]{idx.acsg.search_new(*dc,b.k,ids.data(),b.distances.data()+i*b.k,vt,2,eps[i],&ret);});for(size_t j=0;j<b.k;++j)current[j]=ids[j];uint64_t ns=st.scans,nb=st.blocks,ne=st.exact;
 if(method!="GT10")e.complete<P>(*dc,qi,current.data(),b.distances.data()+i*b.k,b.k,method,st);for(size_t j=0;j<b.k;++j)b.ids[i*b.k+j]=current[j];st.per_query.insert(st.per_query.end(),{st.scans-ns,st.blocks-nb,st.exact-ne});}
}
__attribute__((noinline)) double timed(acsg::IndexACSGFlat& idx,const std::vector<float>& q,int L,const std::string& m,Router& r,Posting& p,Engine& e,Batch& dest,Meter& st){auto t=Clock::now();{Batch out(dest.n,dest.k);run<false>(idx,q,L,m,r,p,e,out,st);copy_packet(out,dest);asm volatile("" : : "g"(out.ids.data()),"g"(dest.ids.data()) : "memory");}return seconds(t);}
json profile(const json& c){check_threads(c);fs::path out=c.at("output_dir");fresh_dir(out);json binding;auto idx=load_index(c,binding);Matrix qm(c.at("queries"));auto q=qm.copy();Router router(c.at("router"),idx->d,idx->ntotal);Posting post(c.at("table"),idx->ntotal);Engine e(c);json result=json::array();
 for(std::string m:{"REG-R","OPT-R"}){Batch ref(qm.n,100);Meter ss;double normal=timed(*idx,q,200,m,router,post,e,ref,ss);Batch instrumented(qm.n,100);Meter st;auto t=Clock::now();run<true>(*idx,q,200,m,router,post,e,instrumented,st);double diag=seconds(t);all_same(ref,instrumented);json v={{"method",m},{"n",qm.n},{"normal_full_wall",normal},{"diagnostic_body_wall",diag},{"stage_seconds",st.sec},{"scans",st.scans},{"exact",st.exact},{"bits_equal",true}};result.push_back(v);ref.save(out/(m+"_raw"),false);}
 // Legacy instrumentation shares the optimized scan workspace; this is a mechanistic diagnostic, not exact subtraction from legacy wall.
 json r={{"status","PASS_E188_PROFILE"},{"stages",{"coarse","features","PQ_LUT","block_route","scan_heap","exact","merge","legacy_exact_merge","main_search","GT10_route"}},{"measurements",result},{"legacy_profile_uses_reused_scan_scratch",true},{"formal_QPS",false},{"threads",process_threads()},{"evaluation_GT_read",false}};fresh_json(out/"profile.json",r);return r;}

json labels(const json& c){check_threads(c);auto t=Clock::now();json binding;auto idx=load_index(c,binding);Matrix qm(c.at("train_queries"));auto q=qm.copy();Engine e(c);fs::path td=c.at("teacher_dir"),out=c.at("blocks");require(!fs::exists(out/"labels.json"),"fresh labels");auto ids=read_raw<int32_t>((td/"raw/ids.i32").string());auto dist=read_raw<float>((td/"raw/distances.f32").string());auto gt=read_gt(c.at("train_gt"),idx->ntotal);size_t n=12000;
 std::vector<double> f(n*8*NF),times(n*8),ops(n*8*5);std::vector<int32_t> gains(n*8),damages(n*8);std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx->storage));
 for(size_t i=0;i<n;++i){const float* qi=q.data()+i*idx->d;dc->set_query(qi);auto* R=ids.data()+i*100;auto* D=dist.data()+i*100;e.coarse(qi);e.summaries(qi,R,D,100);Meter unused;e.prepare<false>(qi,R,100,unused);std::set<int32_t> truth(gt.begin()+i*100,gt.begin()+(i+1)*100),original(R,R+100);
 for(size_t rank=0;rank<8;++rank){size_t z=i*8+rank;int r=e.coarse_buf[rank].second;auto x=e.features(rank,D,100);std::copy(x.begin(),x.end(),f.begin()+z*NF);std::vector<int32_t> rr(R,R+100);std::vector<float> dd(D,D+100);Meter st;e.candidates.clear();auto start=Clock::now();e.region<false>(qi,r,1024,st,false);e.refine<false>(*dc,rr.data(),dd.data(),100,st,false);times[z]=seconds(start);std::set<int32_t> final(rr.begin(),rr.end());int add=0,damage=0;for(int id:truth){add+=final.count(id)&&!original.count(id);damage+=original.count(id)&&!final.count(id);}gains[z]=add-damage;damages[z]=damage;double b=st.blocks;std::array<double,5> op{1,b,b*std::log2(std::max(2.,b)),double(st.scans),double(st.exact)};std::copy(op.begin(),op.end(),ops.begin()+z*5);}
 if(i%1000==0)std::cout<<json{{"label_query",i},{"seconds",seconds(t)}}.dump()<<std::endl;}
 write_raw(out/"rescue_features.f64",f);write_raw(out/"rescue_gain.i32",gains);write_raw(out/"rescue_damage.i32",damages);write_raw(out/"region_seconds.f64",times);write_raw(out/"region_ops.f64",ops);
 json r={{"status","PASS_E188_FIT_LABELS"},{"n",n},{"regions_per_query",8},{"features",NF},{"scan_budget_per_region",1024},{"exact_cap_per_region",48},{"seconds",seconds(t)},{"threads",1},{"test_or_calibration_GT_used_for_fit",false},{"label","actual net added GT100 members after bounded region completion and native merge"}};fresh_json(out/"labels.json",r);return r;}

json benchmark(const json& c,bool qualify){check_threads(c);auto began=Clock::now();fs::path root=c.at("output_dir");fresh_dir(root);fresh_json(root/"config.json",c);json binding;auto idx=load_index(c,binding);Matrix qm(c.at("queries"));auto q=qm.copy();Router router(c.at("router"),idx->d,idx->ntotal);Posting post(c.at("table"),idx->ntotal);Engine e(c);require(e.gain.nf==12,"trained actual rescue model required");
 fresh_json(root/"environment.json",{{"threads",process_threads()},{"cpu",15},{"binding",binding},{"old_backend_bytes",e.old.bytes()},{"block_backend_bytes",e.bl.bytes()},{"timer","full Batch allocation/init + unchanged route/main + completion + six-array copy + destruction"},{"startup_seconds",seconds(began)}});
 std::set<int> cl;for(int L:c.at("completion_L"))cl.insert(L);json results=json::array(),progress=json::array();size_t ordinal=0,batches=0;int repeats=qualify?1:3;
 for(int L:c.at("main_L")){std::vector<std::string> methods={"GT10"};if(cl.count(L))methods=c.at("methods").get<std::vector<std::string>>();std::vector<std::unique_ptr<Batch>> first(methods.size());std::vector<json> rounds(methods.size(),json::array());std::vector<Meter> meters(methods.size());Batch archive(qm.n,100);
 for(int rep=0;rep<repeats;++rep)for(size_t off=0;off<methods.size();++off){size_t mi=(ordinal+rep+off)%methods.size();auto m=methods[mi];check_threads(c);fs::path point=root/(m+"_L"+std::to_string(L));if(rep==0){Batch warm(std::min<size_t>(qm.n,256),100);Meter st;run<false>(*idx,q,L,m,router,post,e,warm,st);}Meter st;double wall=timed(*idx,q,L,m,router,post,e,archive,st);++batches;check_threads(c);validate(archive,idx->ntotal);auto digest=packet_sha(archive);
 if(rep==0){first[mi]=std::make_unique<Batch>(archive);archive.save(point/"raw",false);meters[mi]=st;if(!st.per_query.empty())write_raw(point/"access.u64",st.per_query);}else all_same(*first[mi],archive);
 json r={{"round",rep},{"wall_seconds",wall},{"qps",qm.n/wall},{"packet_sha256",digest},{"threads",process_threads()},{"scanned_codes",st.scans},{"extra_exact_scores",st.exact},{"block_centres",st.blocks}};if(rep)require(digest==rounds[mi][0].at("packet_sha256"),"round SHA");rounds[mi].push_back(r);fresh_json(point/("round"+std::to_string(rep)+".json"),r);json event={{"dataset",c.at("dataset")},{"method",m},{"L",L},{"round",rep},{"qps",qm.n/wall}};progress.push_back(event);write_json(root/"progress.json",progress);std::cout<<event.dump()<<std::endl;}
 if(cl.count(L)){require(methods[1]=="B32"&&methods[2]=="REG-R"&&methods[3]=="OPT-R","fixed method order");all_same(*first[2],*first[3]);audit_merge(*idx,q,*first[0],*first[1],post);std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx->storage));for(size_t mi=3;mi<methods.size();++mi)for(size_t i=0;i<qm.n;++i){std::vector<int32_t> rr(first[0]->ids.begin()+i*100,first[0]->ids.begin()+(i+1)*100);std::vector<float> dd(first[0]->distances.begin()+i*100,first[0]->distances.begin()+(i+1)*100);dc->set_query(q.data()+i*idx->d);Meter st;
 if(mi==3){auto reg=e.old.select(q.data()+i*idx->d,rr.data(),dd.data(),100,"REG-R");uint64_t scans=0;auto cand=e.old.candidates(q.data()+i*idx->d,rr.data(),100,reg,scans,true);e187::merge(*dc,100,rr.data(),dd.data(),cand,true);}else e.complete<false>(*dc,q.data()+i*idx->d,rr.data(),dd.data(),100,methods[mi],st,true);
 for(size_t j=0;j<100;++j)require(rr[j]==first[mi]->ids[i*100+j]&&equal_float(dd[j],first[mi]->distances[i*100+j]),"actual main + exhaustive bounded PQ + full-sort merge oracle");}}
 for(size_t mi=0;mi<methods.size();++mi){std::vector<double>w;for(auto r:rounds[mi])w.push_back(r.at("wall_seconds"));std::sort(w.begin(),w.end());auto m=methods[mi];fs::path point=root/(m+"_L"+std::to_string(L));json r={{"status","PASS_E188_POINT"},{"dataset",c.at("dataset")},{"method",m},{"K",100},{"L",L},{"n",qm.n},{"qps",qm.n/w[w.size()/2]},{"rounds",rounds[mi]},{"timed_output_retained",true},{"all_round_bits_equal",true},{"merge_oracle_passed",cl.count(L)>0&&mi>0},{"result_dir",point.string()},{"scanned_codes_per_query",double(meters[mi].scans)/qm.n},{"extra_exact_scores_per_query",double(meters[mi].exact)/qm.n},{"block_centres_per_query",double(meters[mi].blocks)/qm.n}};fresh_json(point/"result.json",r);results.push_back(r);}++ordinal;}
 json r={{"status",qualify?"PASS_E188_QUALIFICATION":"PASS_E188_MATRIX"},{"dataset",c.at("dataset")},{"points",results.size()},{"batches",batches},{"n",qm.n},{"results",results},{"outer_seconds",seconds(began)},{"evaluation_GT_read",false},{"threads",1}};fresh_json(root/"complete.json",r);return r;}
}
int e188_preserved_main(int argc,char**argv){try{using namespace e188;require(argc==3,"mode config");auto c=read_json(argv[2]);std::string m=argv[1];json r;if(m=="profile")r=profile(c);else if(m=="labels")r=labels(c);else r=benchmark(c,m=="qualification");std::cout<<r.dump()<<std::endl;return 0;}catch(const std::exception&e){std::cerr<<"FATAL E188 "<<e.what()<<std::endl;return 2;}}
