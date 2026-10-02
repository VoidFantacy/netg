#include "base_engine.hpp"
#include <ctime>

uint64_t output_hash(const faiss::idx_t* ids,const float* dist,int K){
 uint64_t h=1469598103934665603ULL;
 for(int j=0;j<K;++j){uint32_t bits;std::memcpy(&bits,dist+j,4);h^=uint64_t(ids[j]);h*=1099511628211ULL;h^=bits;h*=1099511628211ULL;}
 return h;
}
int main(int argc,char**argv){try{
 require(argc==3,"measure config output");threads();json c=read_json(argv[1]);require(c["threads"]==1,"configured one thread");fs::path out=argv[2];require(!fs::exists(out),"new output required");fs::create_directories(out);write_json(out/"config.json",c);
 const size_t n=c["n"],d=c["dimension"],block=c["block"];auto q=read_raw<float>(c["queries"].get<std::string>());auto gt=read_raw<int64_t>(c["gt"].get<std::string>());auto original_entries=read_raw<int32_t>(c["reference_entries"].get<std::string>());auto hashes=read_raw<uint64_t>(c["reference_hashes"].get<std::string>());
 require(q.size()==n*d&&gt.size()==n*100&&original_entries.size()==n*3,"input dimensions");Route router(c["anchor"],d);const size_t H=router.ids.size(),A=H+1;require(hashes.size()==n*A,"reference hashes");
 auto start=Clock::now();auto idx=load_nsg(c["index"]);require(idx->d==d&&idx->ntotal==c["base_n"]&&idx->metric_type==0,"frozen raw IP graph");Fvecs base(c["base"]);require(base.d==d&&base.n==idx->ntotal,"base dimensions");std::vector<float>v(d);
 for(int j=0;j<32;++j){size_t id=(base.n-1)*j/31;idx->storage->reconstruct(id,v.data());require(!std::memcmp(v.data(),base.row(id),4*d),"base/graph bytes");}
 Engine engine(*idx,router);std::vector<std::array<int32_t,3>>routes(n);for(size_t i=0;i<n;++i){routes[i]=router.original(q.data()+i*d);require(!std::memcmp(routes[i].data(),original_entries.data()+i*3,12),"all old default routes");}
 auto entry=[&](size_t i,size_t a){return a?std::array<int32_t,3>{router.ids[a-1],-1,-1}:routes[i];};
 auto guard=[&](){require(double(std::time(nullptr))<c["deadline_unix"].get<double>(),"deadline");require(seconds(start)<c["seconds_cap"].get<double>(),"time cap");require(engine.calls<c["max_search_calls"].get<uint64_t>(),"call cap");require(process_threads()==1,"actual one thread");};
 std::array<faiss::idx_t,100>I,J;std::array<float,100>D,E;uint64_t parity=0,old_matches=0;
 auto smoke=[&](int K,int L,bool old){
  for(size_t i=0;i<4;++i)for(size_t a:std::array<size_t,3>{0,1,H}){
   guard();auto en=entry(i,a);engine.search(q.data()+i*d,en,K,L,I.data(),D.data(),true);uint64_t count=engine.count.count;
   if(old){require(output_hash(I.data(),D.data(),100)==hashes[i*A+a],"old L128 whole return bits hash");++old_matches;}
   engine.search(q.data()+i*d,en,K,L,J.data(),E.data(),false);require(!std::memcmp(I.data(),J.data(),K*sizeof(faiss::idx_t))&&!std::memcmp(D.data(),E.data(),K*4),"plain/counted return bits");
   engine.search(q.data()+i*d,en,K,L,J.data(),E.data(),true,true);require(!std::memcmp(I.data(),J.data(),K*sizeof(faiss::idx_t))&&!std::memcmp(D.data(),E.data(),K*4)&&engine.count.count==count,"linked E99 return bits and NDC");parity+=2;
  }
 };
 smoke(100,128,true);json completed=json::array();
 for(const auto&point:c["points"]){int K=point["K"],L=point["L"];require((K==1||K==100)&&L>=K&&L<=1500,"actual K and frozen L");smoke(K,L,false);fs::path pp=out/("K"+std::to_string(K)+"_L"+std::to_string(L));fs::create_directories(pp);auto ps=Clock::now();
  for(size_t lo=0;lo<n;lo+=block){size_t nb=std::min(block,n-lo);fs::path bp=pp/("block_"+std::to_string(lo));fs::create_directories(bp);std::vector<int32_t>ids(nb*A*K);std::vector<float>dist(nb*A*K);std::vector<uint64_t>ndc(nb*A);std::vector<uint8_t>hits(nb*A);uint64_t before=engine.calls;auto bs=Clock::now();
   for(size_t j=0;j<nb;++j){size_t i=lo+j;guard();std::set<int64_t>truth(gt.begin()+i*100,gt.begin()+(i+1)*100);require(truth.size()==100,"unique GT");
    for(size_t a=0;a<A;++a){auto en=entry(i,a);engine.search(q.data()+i*d,en,K,L,I.data(),D.data(),true);size_t off=(j*A+a)*K;ndc[j*A+a]=engine.count.count;uint8_t hit=0;
     for(int k=0;k<K;++k){require(I[k]>=0&&I[k]<idx->ntotal&&std::isfinite(D[k]),"valid returns");ids[off+k]=I[k];dist[off+k]=D[k];if(K==100&&truth.count(I[k]))++hit;}
     hits[j*A+a]=K==1?uint8_t(I[0]==gt[i*100]):hit;
    }
   }
   write_raw(bp/"ids.i32",ids);write_raw(bp/"distances.f32",dist);write_raw(bp/"ndc.u64",ndc);write_raw(bp/"hits.u8",hits);json done={{"status","PASS"},{"start",lo},{"n",nb},{"A",A},{"K",K},{"L",L},{"search_calls",engine.calls-before},{"seconds",seconds(bs)}};write_json(bp/"complete.json",done);completed.push_back(done);
   resources(out);write_json(out/"progress.json",{{"K",K},{"L",L},{"completed_queries",lo+nb},{"n",n},{"calls",engine.calls},{"seconds",seconds(start)}});std::cout<<"K "<<K<<" L "<<L<<" "<<lo+nb<<"/"<<n<<" seconds "<<seconds(ps)<<std::endl;
  }
 }
 guard();write_json(out/"complete.json",{{"status","PASS"},{"n",n},{"H",H},{"new_search_calls",engine.calls},{"router_calls",router.calls},{"seconds",seconds(start)},{"threads",process_threads()},{"old_full_return_matches",old_matches},{"native_parity_checks",parity},{"blocks",completed},{"complete_online_QPS_measured",false}});return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
