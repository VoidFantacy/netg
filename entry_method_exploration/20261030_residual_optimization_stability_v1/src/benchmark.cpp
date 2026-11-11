#define main e191_embedded_main
#include "../../20261028_seven_dataset_scoring_v1/src/benchmark.cpp"
#undef main

namespace e194 {
using namespace e191;
int fast_plan(Posting& p,const std::array<int32_t,3>& route,const faiss::idx_t* R,int K){
 std::array<int32_t,512> seen;seen.fill(-1);
 auto add=[&](int32_t id){uint32_t s=(uint32_t(id)*2654435761u)&511;while(seen[s]!=-1&&seen[s]!=id)s=(s+1)&511;if(seen[s]==id)return false;seen[s]=id;return true;};
 for(int j=0;j<K;++j)if(R[j]>=0)add(int32_t(R[j]));
 int nc=0;for(int32_t label:route){int slot=p.lookup(label,nullptr);if(slot<0)return -1;for(int j=0;j<p.counts[slot];++j){int32_t id=p.targets[size_t(slot)*p.b+j];if(add(id)){require(nc<96,"fast plan bound");p.candidate[nc++]=id;}}}return nc;
}
void fast_apply(faiss::DistanceComputer& dc,const acsg::Graph<int32_t>& graph,const faiss::VisitedTable& vt,const std::array<int32_t,3>& route,int K,faiss::idx_t*I,float*D,Posting&p){
 for(int j=0;j<K;++j)if(I[j]<0||I[j]>=graph.N||!std::isfinite(D[j])){exp180::cap::apply(dc,graph,vt,route,K,I,D,p);return;}
 if(p.empty)return;int nc=fast_plan(p,route,I,K);if(nc<=0)return;
 for(int j=0;j<K;++j)p.records[j]={I[j],D[j],uint32_t(j),false};
 for(int j=0;j<nc;++j){float v=dc(p.candidate[j]);if(!std::isfinite(v))return;p.records[K+j]={p.candidate[j],v,uint32_t(K+j),false};}
 if(K==1){auto best=p.records[0];for(int j=0;j<nc;++j)if(p.records[K+j].distance<best.distance)best=p.records[K+j];I[0]=best.id;D[0]=best.distance;return;}
 std::copy(p.records.begin(),p.records.begin()+K,p.heap.begin());std::make_heap(p.heap.begin(),p.heap.begin()+K,Posting::better);
 for(int j=0;j<nc;++j){const auto&in=p.records[K+j];if(in.distance<p.heap[0].distance){std::pop_heap(p.heap.begin(),p.heap.begin()+K,Posting::better);p.heap[K-1]=in;std::push_heap(p.heap.begin(),p.heap.begin()+K,Posting::better);}}
 std::sort(p.heap.begin(),p.heap.begin()+K,Posting::better);for(int j=0;j<K;++j){I[j]=p.heap[j].id;D[j]=p.heap[j].distance;}
}
struct FastBackend:Backend {
 explicit FastBackend(const json&c):Backend(c){}
 void fast_complete(faiss::DistanceComputer&dc,const float*q,int32_t*R,float*D,size_t K,const int32_t*h,Stats&st){
  proposals(R,K,h,false);ranked.clear();for(int b:pool)ranked.emplace_back(score(q,centres.data()+size_t(b)*d,d),b);std::sort(ranked.begin(),ranked.end());st.blocks+=ranked.size();sorted.assign(R,R+K);std::sort(sorted.begin(),sorted.end());candidates.clear();all.clear();sqdc->set_query(q);
  size_t consumed=0;uint64_t arrival=0;for(auto[dist,b]:ranked){size_t len=off[b+1]-off[b];if(consumed+len>2048)continue;scanned.push_back(b);for(size_t i=off[b];i<off[b+1];++i,++arrival){int32_t id=ids[i];if(std::binary_search(sorted.begin(),sorted.end(),id))continue;float v=sqdc->query_to_code(sqcodes.data()+i*d);if(metric==0)v=-v;++st.sq;all.push_back({v,arrival,id});}consumed+=len;if(consumed==2048)break;}
  st.scans+=consumed;if(all.size()>96){std::nth_element(all.begin(),all.begin()+96,all.end(),Less{});all.resize(96);}std::sort(all.begin(),all.end(),Less{});for(auto a:all)candidates.push_back(a.id);
  values.clear();for(int id:candidates)values.push_back(dc(id));st.exact+=candidates.size();merged.clear();for(size_t j=0;j<K;++j)merged.push_back({R[j],D[j],uint32_t(j),false});std::make_heap(merged.begin(),merged.end(),Posting::better);
  for(size_t j=0;j<candidates.size();++j)if(values[j]<merged.front().distance){std::pop_heap(merged.begin(),merged.end(),Posting::better);merged.back()={candidates[j],values[j],uint32_t(K+j),false};std::push_heap(merged.begin(),merged.end(),Posting::better);}std::sort(merged.begin(),merged.end(),Posting::better);for(size_t j=0;j<K;++j){R[j]=merged[j].id;D[j]=merged[j].distance;}
 }
};
void run_opt(acsg::IndexACSGFlat&idx,const std::vector<float>&q,int L,const std::string&m,Router&r,Posting&p,FastBackend&e,Batch&b,Stats&st){
 if(m!="OPT-B32"&&m!="OPT-SQ"){e191::run(idx,q,L,m,r,p,e,b,st);return;}
 idx.acsg.search_L=L;std::vector<std::vector<acsg::EnterPoint>>eps(b.n);for(size_t i=0;i<b.n;++i){auto v=r.route(q.data()+i*idx.d);for(int j=0;j<3;++j){b.entries[3*i+j]=v.ids[j];b.profile_distances[3*i+j]=v.distances[j];eps[i].emplace_back(v.ids[j],1.f);}}
 faiss::VisitedTable vt(idx.ntotal);std::unique_ptr<faiss::DistanceComputer>dc(acsg::storage_distance_computer(idx.storage));std::vector<acsg::Neighbor>ret;std::vector<faiss::idx_t>ids(b.k);std::vector<int32_t>cur(b.k);if(m=="OPT-SQ")st.per_query.reserve(b.n*5);
 for(size_t i=0;i<b.n;++i){const float*qi=q.data()+i*idx.d;dc->set_query(qi);vt.advance();idx.acsg.search_new(*dc,b.k,ids.data(),b.distances.data()+i*b.k,vt,2,eps[i],&ret);
  if(m=="OPT-B32"){fast_apply(*dc,*idx.acsg.final_graph,vt,{{b.entries[3*i],b.entries[3*i+1],b.entries[3*i+2]}},b.k,ids.data(),b.distances.data()+i*b.k,p);for(size_t j=0;j<b.k;++j)b.ids[i*b.k+j]=ids[j];}
  else {for(size_t j=0;j<b.k;++j)cur[j]=ids[j];auto a=std::array<uint64_t,5>{st.scans,st.blocks,st.exact,st.pq,st.sq};e.fast_complete(*dc,qi,cur.data(),b.distances.data()+i*b.k,b.k,b.entries.data()+3*i,st);std::copy(cur.begin(),cur.end(),b.ids.begin()+i*b.k);auto z=std::array<uint64_t,5>{st.scans,st.blocks,st.exact,st.pq,st.sq};for(size_t j=0;j<5;++j)st.per_query.push_back(z[j]-a[j]);}
 }
}
__attribute__((noinline)) double time_opt(acsg::IndexACSGFlat&idx,const std::vector<float>&q,int L,const std::string&m,Router&r,Posting&p,FastBackend&e,Batch&dest,Stats&st){auto t=Clock::now();{Batch out(dest.n,dest.k);run_opt(idx,q,L,m,r,p,e,out,st);copy_packet(out,dest);asm volatile(""::"g"(dest.ids.data()),"g"(out.ids.data()):"memory");}return seconds(t);}
json bench(const json&c,bool qualify){
 check_threads(c);auto started=Clock::now();fs::path root=c.at("output_dir");fresh_dir(root);fresh_json(root/"config.json",c);json binding;auto idx=load_index(c,binding);Matrix qm(c.at("queries"));auto q=qm.copy();Router r(c.at("router"),idx->d,idx->ntotal);Posting p(c.at("table"),idx->ntotal);FastBackend e(c);
 fresh_json(root/"environment.json",{{"threads",process_threads()},{"cpu",15},{"binding",binding},{"shared_auxiliary_bytes",e.bytes()},{"GT_read_by_search",false},{"timer","normal Batch lifecycle + route/main/completion + uniform six-array copy/destruction"}});
 json results=json::array();size_t ordinal=0,batches=0;int reps=qualify?1:3;
 for(int K:{1,100})for(int L:c.at("Ls")){
  std::vector<std::string>ms={"GT10","B32"};auto opt=c.at("opt_B32_L").get<std::vector<int>>();auto sq=c.at("sq_L").get<std::vector<int>>();if(std::find(opt.begin(),opt.end(),L)!=opt.end())ms.push_back("OPT-B32");if(std::find(sq.begin(),sq.end(),L)!=sq.end()){ms.push_back("REUSE-SQ");ms.push_back("OPT-SQ");}
  std::map<std::string,size_t>pos;for(size_t j=0;j<ms.size();++j)pos[ms[j]]=j;
  std::vector<std::unique_ptr<Batch>>first(ms.size());std::vector<Stats>meters(ms.size());std::vector<json>rounds(ms.size(),json::array());Batch dest(qm.n,K);
  for(int rep=0;rep<reps;++rep)for(size_t off=0;off<ms.size();++off){size_t mi=(ordinal+rep+off)%ms.size();auto m=ms[mi];check_threads(c);if(rep==0){Batch warm(std::min<size_t>(256,qm.n),K);Stats a;run_opt(*idx,q,L,m,r,p,e,warm,a);}Stats st;double wall=time_opt(*idx,q,L,m,r,p,e,dest,st);++batches;check_threads(c);validate(dest,idx->ntotal);auto digest=packet_sha(dest);fs::path out=root/("k"+std::to_string(K))/(m+"_L"+std::to_string(L));
   if(rep==0){first[mi]=std::make_unique<Batch>(dest);meters[mi]=st;dest.save(out/"raw",false);if(!st.per_query.empty())write_raw(out/"access.u64",st.per_query);}else {all_same(*first[mi],dest);require(st.per_query==meters[mi].per_query,"three-round work equality");}
   json v={{"round",rep},{"qps",qm.n/wall},{"wall_seconds",wall},{"packet_sha256",digest},{"threads",process_threads()}};rounds[mi].push_back(v);fresh_json(out/("round"+std::to_string(rep)+".json"),v);std::cout<<json({{"dataset",c.at("dataset")},{"window",c.at("window")},{"K",K},{"L",L},{"method",m},{"round",rep},{"qps",qm.n/wall}}).dump()<<std::endl;
  }
  auto&main=*first[pos.at("GT10")];auto&b32=*first[pos.at("B32")];audit_merge(*idx,q,main,b32,p);uint64_t pc=0;std::unique_ptr<faiss::DistanceComputer>dc(acsg::storage_distance_computer(idx->storage));
  for(size_t i=0;i<qm.n;++i){std::vector<faiss::idx_t> rr(K);for(int j=0;j<K;++j)rr[j]=main.ids[i*K+j];std::array<int32_t,3>h{main.entries[3*i],main.entries[3*i+1],main.entries[3*i+2]};int nc=p.plan(h,rr.data(),K,nullptr);std::vector<int32_t>a(p.candidate.begin(),p.candidate.begin()+std::max(0,nc));int nf=fast_plan(p,h,rr.data(),K);require(nf==nc&&std::equal(a.begin(),a.end(),p.candidate.begin()),"all-query B32 plan exact order");pc+=std::max(0,nc);}
  if(pos.count("OPT-B32"))all_same(b32,*first[pos.at("OPT-B32")]);
  if(pos.count("REUSE-SQ")){
   auto&sq=*first[pos.at("REUSE-SQ")];all_same(sq,*first[pos.at("OPT-SQ")]);require(meters[pos.at("REUSE-SQ")].per_query==meters[pos.at("OPT-SQ")].per_query,"SQ all-query access parity");
   for(size_t i=0;i<qm.n;++i){dc->set_query(q.data()+i*idx->d);std::vector<int32_t>rr(main.ids.begin()+i*K,main.ids.begin()+(i+1)*K);std::vector<float>dd(main.distances.begin()+i*K,main.distances.begin()+(i+1)*K);Stats st;e.complete(*dc,q.data()+i*idx->d,rr.data(),dd.data(),K,main.entries.data()+3*i,"REUSE-SQ",st,true);auto pool=e.pool,scan=e.scanned,cands=e.candidates;for(int j=0;j<K;++j)require(rr[j]==sq.ids[i*K+j]&&equal_float(dd[j],sq.distances[i*K+j]),"full-sort SQ scalar merge oracle");rr.assign(main.ids.begin()+i*K,main.ids.begin()+(i+1)*K);dd.assign(main.distances.begin()+i*K,main.distances.begin()+(i+1)*K);Stats ss;e.fast_complete(*dc,q.data()+i*idx->d,rr.data(),dd.data(),K,main.entries.data()+3*i,ss);require(pool==e.pool&&scan==e.scanned&&cands==e.candidates,"SQ exact pool/scan/shortlist parity");}
  }
  for(size_t mi=0;mi<ms.size();++mi){std::vector<double>w;for(auto a:rounds[mi])w.push_back(a.at("wall_seconds"));std::sort(w.begin(),w.end());const auto&st=meters[mi];json a={{"dataset",c.at("dataset")},{"window",c.at("window")},{"method",ms[mi]},{"K",K},{"L",L},{"n",qm.n},{"qps",qm.n/w[w.size()/2]},{"rounds",rounds[mi]},{"result_dir",(root/("k"+std::to_string(K))/(ms[mi]+"_L"+std::to_string(L))).string()},{"scans_per_query",double(st.scans)/qm.n},{"SQ_scores_per_query",double(st.sq)/qm.n},{"extra_exact_per_query",(ms[mi]=="B32"||ms[mi]=="OPT-B32")?double(pc)/qm.n:double(st.exact)/qm.n},{"B32_counts_reconstructed_outside_wall",true},{"all_round_bits_equal",true},{"all_oracles_passed",true}};fresh_json(fs::path(a.at("result_dir"))/"result.json",a);results.push_back(a);}++ordinal;
 }
 json a={{"status",qualify?"PASS_E194_QUALIFICATION":"PASS_E194_FORMAL"},{"points",results.size()},{"batches",batches},{"results",results},{"GT_read_by_search",false},{"outer_seconds",seconds(started)}};fresh_json(root/"complete.json",a);return a;
}
}
int main(int argc,char**argv){try{e194::require(argc==3,"mode config");e194::bench(e194::read_json(argv[2]),std::string(argv[1])=="qualification");return 0;}catch(const std::exception&e){std::cerr<<"FATAL E194 "<<e.what()<<std::endl;return 2;}}
