#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <map>
int main(int argc,char** argv){try{
 require(argc==3,"propose config new_output");std::ifstream f(argv[1]);json c;f>>c;fs::path out=argv[2];require(!fs::exists(out),"existing proposals");fs::create_directories(out);
 size_t n=c.at("num_queries"),d=c.at("dim"),h=c.at("hub_count");auto q=read_raw<float>(c.at("queries_file")),w=read_raw<float>(c.at("anchor"));auto hubs=read_raw<int32_t>(c.at("hub_ids"));
 require(q.size()==n*d&&w.size()==h*d&&hubs.size()==h,"proposal shapes");std::map<int32_t,int32_t> local;for(size_t j=0;j<h;++j)local[hubs[j]]=j;
 std::vector<std::unique_ptr<Policy>> policies;
 for(auto p:c.at("policies")){p["dim"]=d;policies.push_back(std::make_unique<Policy>(p,out/(p.at("name").get<std::string>()+".hnsw"),false,false));}
 require(policies.size()==2,"proposal policies");
 std::vector<int32_t> candidates(n*8),triples(n*56*3),baseline(n*2*3);hnswlib::InnerProductSpace space(d);auto fn=space.get_dist_func();auto param=space.get_dist_func_param();
 for(size_t i=0;i<n;++i){std::set<int32_t> chosen;
  for(size_t b=0;b<2;++b){auto r=policies[b]->route(q.data()+i*d);for(size_t k=0;k<3;++k){chosen.insert(local.at(r.ids[k]));baseline[(i*2+b)*3+k]=local.at(r.ids[k]);}}
  std::vector<std::pair<float,int32_t>> ranked(h);for(size_t j=0;j<h;++j)ranked[j]={fn(q.data()+i*d,w.data()+j*d,param),int32_t(j)};
  std::sort(ranked.begin(),ranked.end(),[&](auto a,auto b){return a.first<b.first||(a.first==b.first&&hubs[a.second]<hubs[b.second]);});
  for(auto r:ranked){if(chosen.size()==8)break;chosen.insert(r.second);}std::vector<int32_t> ids(chosen.begin(),chosen.end());std::sort(ids.begin(),ids.end(),[&](auto a,auto b){return hubs[a]<hubs[b];});
  std::copy(ids.begin(),ids.end(),candidates.begin()+i*8);size_t t=0;for(size_t a=0;a<8;++a)for(size_t b=a+1;b<8;++b)for(size_t e=b+1;e<8;++e){size_t p=(i*56+t++)*3;triples[p]=ids[a];triples[p+1]=ids[b];triples[p+2]=ids[e];}require(t==56,"triple count");
 }
 write_raw(out/"candidates.i32",candidates);write_raw(out/"triples.i32",triples);write_raw(out/"baseline_triples.i32",baseline);write_json(out/"complete.json",{{"status","COMPLETE"},{"router_calls",n*2},{"exact_score_distances",n*h},{"graph_calls",0},{"GT_read",false}});return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}
