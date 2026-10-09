#include "runtime.hpp"
using namespace exp172;
namespace {
struct Stats {m5::PostStats post;uint64_t domain_checks=0,domain_fallbacks=0;};
bool legal_query(const float*q,size_t d){
 if((_mm_getcsr()&0xffc0U)!=0x1f80U)return false;
 for(size_t j=0;j<d;++j){uint32_t bits;memcpy(&bits,q+j,4);if((bits&0x7fffffffU)>0x49800000U)return false;}
 return true;
}
// GT and M5 retain the original v9 heap-pop route and scalar search_new body.
// NSG uses the same graph's original enterpoint and the same search_new call.
void run(acsg::IndexACSGFlat&idx,NativeRouter&r,const std::vector<float>&q,int L,
 Batch&b,bool nsg,m5::Posting*post,bool counting,Stats*stats){
 const size_t d=idx.d;idx.acsg.search_L=L;r.counting(counting);
 std::vector<std::vector<acsg::EnterPoint>> eps(b.n);
 for(size_t i=0;i<b.n;++i){
  if(nsg){eps[i].emplace_back(idx.acsg.enterpoint,1.f);b.entries[3*i]=idx.acsg.enterpoint;b.entries[3*i+1]=b.entries[3*i+2]=-1;}
  else {const auto route=r.route(q.data()+i*d);for(int j=0;j<3;++j){eps[i].emplace_back(route.ids[j],1.f);b.entries[3*i+j]=route.ids[j];b.profile_distances[3*i+j]=route.distances[j];}if(counting)b.route_ndc[i]=r.counter.calls;}
 }
 faiss::VisitedTable vt(idx.ntotal);std::unique_ptr<faiss::DistanceComputer> computer;CounterDC* count=nullptr;
 if(counting){count=new CounterDC(acsg::storage_distance_computer(idx.storage));computer.reset(count);}else computer.reset(acsg::storage_distance_computer(idx.storage));
 auto&dc=*computer;std::vector<acsg::Neighbor>ret;std::vector<faiss::idx_t>out(b.k);
 for(size_t i=0;i<b.n;++i){const float*current=q.data()+i*d;dc.set_query(current);vt.advance();
  idx.acsg.search_new(dc,int(b.k),out.data(),b.distances.data()+i*b.k,vt,2,eps[i],&ret);
  if(post){if(stats)++stats->domain_checks;if(legal_query(current,d)){post->apply(dc,{b.entries[3*i],b.entries[3*i+1],b.entries[3*i+2]},int(b.k),out.data(),b.distances.data()+i*b.k,m5::Mode::POST,stats?&stats->post:nullptr);}else if(stats)++stats->domain_fallbacks;}
  for(size_t j=0;j<b.k;++j)b.ids[i*b.k+j]=int32_t(out[j]);
  if(counting){b.graph_ndc[i]=count->count;if(nsg)require(count->first[0]==idx.acsg.enterpoint,"NSG original entry score order");else require(count->first==std::array<int32_t,3>{b.entries[3*i],b.entries[3*i+1],b.entries[3*i+2]},"actual original GT entry score order");}
 }
}
inline void publish_normal_packet(const Batch&b){asm volatile("" : : "g"(b.ids.data()),"g"(b.distances.data()),"g"(b.entries.data()),"g"(b.profile_distances.data()),"g"(b.route_ndc.data()),"g"(b.graph_ndc.data()),"g"(b.n),"g"(b.k) : "memory");}
__attribute__((noinline)) double timed_normal_batch(acsg::IndexACSGFlat&idx,NativeRouter&r,
 const std::vector<float>&q,int L,size_t n,size_t K,bool nsg,m5::Posting*post){
 const auto started=Clock::now();{Batch output(n,K);run(idx,r,q,L,output,nsg,post,false,nullptr);publish_normal_packet(output);}asm volatile("" : : : "memory");return seconds(started);
}
// The original v9 independent linear merge oracle, without runtime heap/apply.
void audit_merge(acsg::IndexACSGFlat&idx,const std::vector<float>&q,const Batch&before,
 const Batch&after,m5::Posting*post){
 require(before.entries==after.entries&&!memcmp(before.profile_distances.data(),after.profile_distances.data(),before.profile_distances.size()*4),"post cannot alter route packet");
 if(!post||post->empty){same(before,after);return;}
 std::unique_ptr<faiss::DistanceComputer>dc(acsg::storage_distance_computer(idx.storage));struct Item{int32_t id;float distance;int priority;};
 for(size_t i=0;i<before.n;++i){const float*current=q.data()+i*idx.d;dc->set_query(current);std::vector<faiss::idx_t>original(before.k);for(size_t j=0;j<before.k;++j)original[j]=before.ids[i*before.k+j];
  const int nc=post->empty?0:post->plan({before.entries[3*i],before.entries[3*i+1],before.entries[3*i+2]},original.data(),int(before.k),nullptr);
  if(nc<=0||!legal_query(current,idx.d)){for(size_t j=0;j<before.k;++j){require(before.ids[i*before.k+j]==after.ids[i*before.k+j],"empty/fallback ID parity");require(!memcmp(before.distances.data()+i*before.k+j,after.distances.data()+i*before.k+j,4),"empty/fallback score bits");}continue;}
  std::vector<Item>packet;for(size_t j=0;j<before.k;++j){int32_t id=before.ids[i*before.k+j];packet.push_back({id,id<0?std::numeric_limits<float>::max():(*dc)(id),int(j)});}
  auto worse=[](const Item&a,const Item&b){if(a.id<0||b.id<0)return a.id<0&&b.id>=0;if(a.distance!=b.distance)return a.distance>b.distance;return a.priority>b.priority;};
  for(int j=0;j<nc;++j){Item candidate{post->candidate[j],(*dc)(post->candidate[j]),int(before.k)+j};size_t worst=0;for(size_t t=1;t<packet.size();++t)if(worse(packet[t],packet[worst]))worst=t;if(packet[worst].id<0||candidate.distance<packet[worst].distance)packet[worst]=candidate;}
  std::sort(packet.begin(),packet.end(),[&](const Item&a,const Item&b){return worse(b,a);});for(size_t j=0;j<before.k;++j){require(packet[j].id==after.ids[i*before.k+j],"independent linear merge ID");require(!memcmp(&packet[j].distance,after.distances.data()+i*before.k+j,4),"independent linear merge score word");}
 }
}
json stats_json(const Stats&s){return {{"domain_checks",s.domain_checks},{"domain_fallbacks",s.domain_fallbacks},{"lookups",s.post.lookups},{"probes",s.post.probes},{"fallbacks",s.post.fallbacks},{"row_reads",s.post.row_reads},{"candidate_count",s.post.candidates},{"post_dots",s.post.dots},{"commits",s.post.commits},{"nonfinite_failures",s.post.nonfinite_failures}};}
}
int main(int argc,char**argv){try{
 require(argc==2,"benchmark JOB.json");const auto c=read_json(argv[1]);threads();const fs::path dest=c.at("out").get<std::string>();require(!fs::exists(dest),"preserve output");fs::create_directories(dest);write_json(dest/"job.json",c);
 const auto started=Clock::now();const size_t n=c.at("n"),d=c.at("dimension");require(n>0,"nonempty queries");std::vector<float>q(n*d);
 if(c.value("query_format",std::string("fvecs"))=="fvecs"){Fvecs input(c.at("queries"));size_t first=c.value("query_first",size_t(0));require(input.d==d&&first<=input.n&&n<=input.n-first,"test query source shape");for(size_t i=0;i<n;++i)std::copy(input.row(first+i),input.row(first+i)+d,q.data()+i*d);}
 else {auto input=read_raw<float>(c.at("queries").get<std::string>());size_t first=c.value("query_first",size_t(0));require(input.size()%d==0&&first<=input.size()/d&&n<=input.size()/d-first,"raw test query source shape");std::copy(input.begin()+first*d,input.begin()+(first+n)*d,q.begin());}
 for(float v:q)require(std::isfinite(v),"finite test query");
 NativeRouter router(c.at("anchor"),d);auto index=load_nsg(c.at("index").get<std::string>());require(index->ntotal==c.at("base_n").get<int64_t>()&&index->d==int(d),"loaded identity");for(auto id:router.ids)require(id>=0&&id<index->ntotal,"real hub loaded base domain");
 auto*flat=dynamic_cast<faiss::IndexFlat*>(index->storage);require(flat,"actual original flat base");
 if(c.value("verify_loaded_base_words",true)){Fvecs base(c.at("base"));require(base.n==size_t(index->ntotal)&&base.d==d,"registered base shape");for(size_t i=0;i<base.n;++i)require(!memcmp(flat->get_xb()+i*d,base.row(i),d*4),"actual loaded base words differ from registered fvecs");}
 m5::Posting posting(c.at("table").get<std::string>(),false,uint32_t(index->ntotal));require(posting.labels==router.ids,"posting exact frozen real labels");
 std::ifstream boot_file("/proc/sys/kernel/random/boot_id");std::string boot;std::getline(boot_file,boot);
 write_json(dest/"native_environment.json",{{"router",router.binding()},{"mxcsr",_mm_getcsr()},{"threads",process_threads()},{"pid",getpid()},{"boot_id",boot},{"no_GT_read",true},{"startup_seconds",seconds(started)},{"enterpoint",index->acsg.enterpoint},{"loaded_base_words_checked",c.value("verify_loaded_base_words",true)},{"loaded_base_words",uint64_t(index->ntotal)*d},{"main_kernel","original E172 current scalar search_new; identical for NSG GT M5"},{"whole_wall","normal Batch allocate/init/release, original routes/vt/DC/pool, every query guard/post/merge/output; model/index/query loading and audits separate"},{"posting_pairs",posting.pairs},{"posting_resident_bytes",posting.resident_bytes()}});
 const int repeats=c.value("timing_repeats",3),warmups=c.value("warmup_batches",1);const size_t warm_n=std::min(n,c.value("warmup_n",size_t(256)));require(repeats>=1&&warmups>=0,"repetition counts");
 // Count audits use this fixed uniform sample, selected without any responses.
 const size_t audit_n=std::min(n,size_t(256));std::vector<int32_t>audit_ids(audit_n);std::vector<float>audit_q(audit_n*d);
 for(size_t i=0;i<audit_n;++i){audit_ids[i]=audit_n==1?0:int32_t(i*(n-1)/(audit_n-1));std::copy(q.begin()+size_t(audit_ids[i])*d,q.begin()+(size_t(audit_ids[i])+1)*d,audit_q.begin()+i*d);}
 write_raw(dest/"audit_query_ids.i32",audit_ids);
 const std::array<std::string,3>names{"NSG","GT","M5"};json rounds=json::array(),results=json::array();size_t point_ordinal=0;uint64_t native_calls=0;
 for(int K:c.at("K_values"))for(int L:c.at("L")){
  require((K==1||K==100)&&L>=K,"actual K/L");const fs::path group=dest/("k"+std::to_string(K));std::array<std::vector<double>,3>timings;
  for(int w=0;w<warmups;++w)for(size_t vi=0;vi<3;++vi){Batch warm(warm_n,K);run(*index,router,q,L,warm,vi==0,vi==2?&posting:nullptr,false,nullptr);publish_normal_packet(warm);native_calls+=warm_n;}
  for(int round=0;round<repeats;++round)for(size_t offset=0;offset<3;++offset){const size_t vi=(point_ordinal+size_t(round)+offset)%3;threads();const double wall=timed_normal_batch(*index,router,q,L,n,K,vi==0,vi==2?&posting:nullptr);timings[vi].push_back(wall);native_calls+=n;resource_guard(c,dest);json row={{"K",K},{"L",L},{"method",names[vi]},{"round",round},{"seconds",wall},{"qps",n/wall},{"n",n},{"threads",process_threads()},{"cpu",15},{"native_calls",native_calls}};rounds.push_back(row);write_json(dest/"timing_progress.json",rounds);std::cout<<row.dump()<<std::endl;}
  std::array<std::unique_ptr<Batch>,3>full_plain;
  for(size_t vi=0;vi<3;++vi){full_plain[vi]=std::make_unique<Batch>(n,K);run(*index,router,q,L,*full_plain[vi],vi==0,vi==2?&posting:nullptr,false,nullptr);native_calls+=n;}
  // Every method still saves the full 10000-query return packet. The full M5
  // linear oracle reuses the already computed same-L GT packet as its before.
  audit_merge(*index,q,*full_plain[1],*full_plain[2],&posting);
  for(size_t vi=0;vi<3;++vi){const Batch&plain=*full_plain[vi];Batch sample_plain(audit_n,K),counted(audit_n,K);Stats stats;
   for(size_t i=0;i<audit_n;++i){size_t src=size_t(audit_ids[i]);for(size_t j=0;j<size_t(K);++j){sample_plain.ids[i*K+j]=plain.ids[src*K+j];sample_plain.distances[i*K+j]=plain.distances[src*K+j];}for(size_t j=0;j<3;++j){sample_plain.entries[3*i+j]=plain.entries[3*src+j];sample_plain.profile_distances[3*i+j]=plain.profile_distances[3*src+j];}}
   run(*index,router,audit_q,L,counted,vi==0,vi==2?&posting:nullptr,true,&stats);native_calls+=audit_n;same(sample_plain,counted);
   const fs::path out=group/(names[vi]+"_L"+std::to_string(L));plain.save(out/"raw",false);counted.save(out/"raw",true);write_raw(out/"raw/audit_query_ids.i32",audit_ids);
   json result={{"method",names[vi]},{"K",K},{"L",L},{"n",n},{"timing_seconds",timings[vi]},{"warmup_batches",warmups},{"warmup_n",warm_n},{"plain_count_bits_equal",true},{"plain_count_parity_scope","fixed uniform query sample only"},{"count_audit_n",audit_n},{"audit_query_ids_formula","floor(i*(n-1)/(audit_n-1)), endpoints included; frozen before any feedback"},{"stats_scope","fixed uniform count-audit queries only, not the full batch"},{"independent_original_linear_merge",vi==2},{"linear_merge_audit_n",vi==2?n:0},{"full_plain_return_n",n},{"threads",1},{"cpu",15},{"normal_output_release_before_stop",true},{"timed_output_retained",false},{"audit_scope","full saved plain packet and full M5 linear oracle; plain/count word parity and NDC on fixed 256 query sample; timed rounds use unchanged normal body"},{"stats",stats_json(stats)}};write_json(out/"complete.json",result);results.push_back(result);resource_guard(c,dest);
  }
  ++point_ordinal;write_json(dest/"progress.json",{{"completed_KL",point_ordinal},{"native_calls",native_calls},{"seconds_including_startup_and_audits",seconds(started)}});
 }
 write_json(dest/"complete.json",{{"status","PASS_NSG_GT_M5_NATIVE_FULL_PLAIN_SAMPLED_COUNT_LINEAR_ORACLE_V2"},{"results",results},{"wall_rounds",rounds.size()},{"native_calls",native_calls},{"formal_order",rounds},{"rotation","(KL ordinal + round) mod 3; fixed before feedback"},{"wall_boundary","complete owned normal Batch lifetime; loading GT scoring serialization counts and linear audits excluded"},{"count_audit_n",audit_n},{"count_audit_scope","fixed uniform sample only; not full NDC"},{"full_plain_return_n",n},{"full_M5_linear_merge_audit_n",n},{"seconds_with_startup_and_audits",seconds(started)},{"no_quality_claim_before_GT_evaluation",true}});return 0;
}catch(const std::exception&e){std::cerr<<"FATAL "<<e.what()<<'\n';return 2;}}
