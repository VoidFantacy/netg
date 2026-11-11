#include "e195.inc"
namespace e196 {
using namespace e195;
struct Point{int K,L;std::string method;};
json bench(const json&c){
 check_threads(c);auto start=Clock::now();fs::path root=c.at("output_dir");fresh_dir(root);fresh_json(root/"config.json",c);json binding;auto idx=load_index(c,binding);Matrix qm(c.at("queries"));auto q=qm.copy();Router router(c.at("router"),idx->d,idx->ntotal);Posting post(c.at("table"),idx->ntotal);e194::FastBackend aux(c);Meta meta(c,*idx->acsg.final_graph,post);fresh_json(root/"environment.json",{{"threads",process_threads()},{"cpu",15},{"binding",binding},{"GT_read_by_search",false},{"timer","unchanged E195 complete timed wrapper"}});
 std::vector<Point>points;for(auto p:c.at("points"))points.push_back({p.at("K"),p.at("L"),p.at("method")});std::vector<std::unique_ptr<Batch>>first(points.size());std::vector<Meter>meters(points.size());std::vector<json>rounds(points.size(),json::array());Batch dest1(qm.n,1),dest100(qm.n,100);size_t batches=0;
 for(int rep=0;rep<3;++rep)for(size_t off=0;off<points.size();++off){size_t j=(off+rep*17)%points.size();const auto&p=points[j];require(p.L>=p.K,"real K budget");auto&dest=p.K==1?dest1:dest100;check_threads(c);if(!rep){Batch warm(std::min<size_t>(128,qm.n),p.K);Meter wm;e195::run(*idx,q,p.L,p.method,router,post,aux,meta,warm,wm);}Meter meter;double wall=e195::timed(*idx,q,p.L,p.method,router,post,aux,meta,dest,meter);++batches;check_threads(c);validate(dest,idx->ntotal);fs::path path=root/("k"+std::to_string(p.K))/(p.method+"_L"+std::to_string(p.L));
  if(!rep){first[j]=std::make_unique<Batch>(dest);meters[j]=meter;dest.save(path/"raw",false);if(!meter.work.empty())write_raw(path/"work.u64",meter.work);}else{all_same(*first[j],dest);require(meters[j].work==meter.work,"three-round work parity");}
  json a={{"round",rep},{"wall_seconds",wall},{"qps",qm.n/wall},{"packet_sha256",packet_sha(dest)},{"threads",1}};rounds[j].push_back(a);fresh_json(path/("round"+std::to_string(rep)+".json"),a);std::cout<<json({{"dataset",c.at("dataset")},{"window",c.at("window")},{"K",p.K},{"L",p.L},{"method",p.method},{"round",rep}}).dump()<<std::endl;
 }
 json results=json::array();std::map<std::pair<int,int>,std::unique_ptr<Batch>>main_cache;size_t old_parity=0,linear=0;
 for(size_t j=0;j<points.size();++j){const auto&p=points[j];fs::path path=root/("k"+std::to_string(p.K))/(p.method+"_L"+std::to_string(p.L));auto key=std::make_pair(p.K,p.L);
  if(p.method!="GT10"){
   if(!main_cache.count(key)){auto b=std::make_unique<Batch>(qm.n,p.K);Method mm;mm.route=&router;mm.family="GT10";run_batch(*idx,q,p.L,mm,*b);main_cache.emplace(key,std::move(b));}
   auto&main=*main_cache.at(key);
   if(p.method=="OPT-B32"){audit_merge(*idx,q,main,*first[j],post);++linear;}else if(isnav(p.method)){audit_nav(*idx,q,p.L,p.method,post,meta,main,*first[j],meters[j],path);++linear;}else require(false,"only original fixed policies and strong controls");
  }
  fs::path old=fs::path(c.at("old_output_dir"))/("k"+std::to_string(p.K))/(p.method+"_L"+std::to_string(p.L));bool parity=false;if(fs::exists(old/"round0.json")){auto expected=read_json(old/"round0.json");require(expected.at("packet_sha256")==packet_sha(*first[j]),"full query original E195 packet parity");parity=true;++old_parity;}
  std::vector<double>w;for(auto a:rounds[j])w.push_back(a.at("wall_seconds"));std::sort(w.begin(),w.end());json a={{"dataset",c.at("dataset")},{"window",c.at("window")},{"K",p.K},{"L",p.L},{"method",p.method},{"n",qm.n},{"qps",qm.n/w[1]},{"rounds",rounds[j]},{"result_dir",path.string()},{"old_packet_parity",parity},{"all_round_bits_equal",true}};fresh_json(path/"result.json",a);results.push_back(a);
 }
 json a={{"status","PASS_E196_DENSE_COST_WINDOW"},{"dataset",c.at("dataset")},{"window",c.at("window")},{"points",points.size()},{"batches",batches},{"original_E195_packet_parity_points",old_parity},{"full_query_linear_oracle_points",linear},{"results",results},{"seconds",seconds(start)}};fresh_json(root/"complete.json",a);return a;
}
}
int main(int argc,char**argv){try{e196::require(argc==2,"config");e196::bench(e196::read_json(argv[1]));return 0;}catch(const std::exception&e){std::cerr<<"FATAL E196 "<<e.what()<<std::endl;return 2;}}
