#include "/data/netg/ACSG/entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/src/search_core.hpp"
#include <faiss/IndexFlat.h>
int main(int argc,char**argv){try{
 require(argc==3,"config output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"preserve output");fs::create_directories(out);
 int d=c["dimension"],h=c["H"],n=c["n"];auto q=read_raw<float>(c["queries"]);auto raw=read_raw<float>(c["raw_hubs"]);auto hids=read_raw<int32_t>(c["hub_ids"]);require(raw.size()==size_t(h*d)&&q.size()==size_t(n*d),"shapes");
 faiss::IndexFlatIP storage(d);storage.add(h,raw.data());std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(&storage));uint64_t calls=0;
 for(auto m:c["methods"]){std::string name=m["name"];int count=m["count"];auto entries=read_raw<int32_t>(m["entries"]);require(entries.size()==size_t(n*3),"entry shape");std::vector<int32_t> first(n),sorted(n*3,-1);std::vector<float> distances(n*3,std::numeric_limits<float>::infinity());std::vector<acsg::Neighbor> pool;
  for(int i=0;i<n;++i){dc->set_query(q.data()+i*d);pool.clear();for(int j=0;j<count;++j){int id=entries[i*3+j];auto it=std::lower_bound(hids.begin(),hids.end(),id);require(it!=hids.end()&&*it==id,"hub exists");float dist=(*dc)(it-hids.begin());++calls;distances[i*3+j]=dist;pool.emplace_back(id,dist,true);}std::sort(pool.begin(),pool.end());first[i]=pool[0].id;for(int j=0;j<count;++j)sorted[i*3+j]=pool[j].id;}
  auto p=out/name;fs::create_directories(p);write_raw(p/"first.i32",first);write_raw(p/"sorted.i32",sorted);write_raw(p/"initial_distances.f32",distances);
 }
 write_json(out/"complete.json",{{"status","PASS"},{"distance_calls",calls},{"NSG_calls",0},{"ANN_calls",0},{"threads",1},{"cpu",15},{"initialization_only",true}});return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
