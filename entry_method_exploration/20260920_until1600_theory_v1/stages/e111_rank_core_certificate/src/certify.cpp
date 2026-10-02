#include "/data/netg/ACSG/entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/src/search_core.hpp"
#include <bitset>
#include <unordered_map>
using Bits=std::bitset<100>;
int main(int argc,char**argv){try{
 require(argc==3,"config output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"preserve output");fs::create_directories(out);auto start=Clock::now();int n=c["n"],d=c["dimension"],h=c["H"];require(n==4096,"full exposed query rows");
 auto gt=read_raw<int32_t>(c["GT"]);auto q=read_raw<float>(c["queries"]);auto hids=read_raw<int32_t>(c["hub_ids"]);require(gt.size()==size_t(n*100)&&q.size()==size_t(n*d)&&hids.size()==size_t(h),"input shapes");auto idx=load_nsg(c["index"]);require(idx->ntotal==c["base_n"]&&idx->d==d&&idx->metric_type==0,"fixed NSG");const auto& graph=*idx->acsg.final_graph;
 std::unordered_map<int,int> hcol;std::unordered_map<int,std::vector<int>> reverse;uint64_t hub_slots=0,core_slots=0,initial_distance_calls=0;
 for(int a=0;a<h;++a){hcol[hids[a]]=a;reverse[hids[a]].push_back(a);for(int j=0;j<graph.K;++j){int v=graph.at(hids[a],j);++hub_slots;if(v>=0){require(v<idx->ntotal,"valid neighbor");reverse[v].push_back(a);}}}
 struct Method{std::string name;int count;bool forced;std::vector<int32_t> entries,primary,first;std::map<int,std::vector<uint64_t>> masks;};std::vector<Method> methods;
 std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx->storage));
 for(auto x:c["methods"]){Method m;m.name=x["name"];m.count=x["entry_count"];m.forced=x["forced"];m.entries=read_raw<int32_t>(x["entries"]);require(m.entries.size()==size_t(n*3),"method entries");if(m.forced)m.primary=read_raw<int32_t>(x["primary"]);m.first.resize(n);
  for(int i=0;i<n;++i){dc->set_query(q.data()+i*d);std::vector<acsg::Neighbor> pool;for(int j=0;j<m.count;++j){int id=m.entries[i*3+j];require(id>=0&&id<idx->ntotal,"entry");pool.emplace_back(id,(*dc)(id),true);++initial_distance_calls;}std::sort(pool.begin(),pool.end());m.first[i]=m.forced?m.primary[i]:pool[0].id;require(std::any_of(pool.begin(),pool.end(),[&](auto v){return v.id==m.first[i];}),"first in entries");}
  for(int size:{64,100})m.masks[size].resize(n*2);methods.push_back(std::move(m));}
 std::map<int,std::vector<uint8_t>> counts,gt1;for(int m:{64,100}){counts[m].resize(n*h);gt1[m].resize(n*h);}uint64_t bfs_checks=0;
 for(int i=0;i<n;++i){if(i%64==0)require(std::time(nullptr)<c["deadline_unix"].get<double>()&&seconds(start)<c["seconds_cap"].get<double>(),"diagnostic deadline");
  for(int m:{64,100}){std::unordered_map<int,int> local;for(int j=0;j<m;++j){int id=gt[i*100+j];require(id>=0&&id<idx->ntotal,"GT id");require(local.emplace(id,j).second,"unique GT");}
   std::vector<Bits> adj(m),reach(m);for(int j=0;j<m;++j){reach[j].set(j);int id=gt[i*100+j];for(int z=0;z<graph.K;++z){int v=graph.at(id,z);++core_slots;auto it=local.find(v);if(it!=local.end()){adj[j].set(it->second);reach[j].set(it->second);}}}
   for(int k=0;k<m;++k)for(int j=0;j<m;++j)if(reach[j][k])reach[j]|=reach[k];
   if(i%256==0)for(int j=0;j<m;++j){Bits check;check.set(j);std::vector<int> todo{j};for(size_t z=0;z<todo.size();++z)for(int v=0;v<m;++v)if(adj[todo[z]][v]&&!check[v]){check.set(v);todo.push_back(v);}require(check==reach[j],"independent BFS closure");++bfs_checks;}
   std::vector<Bits> hub_masks(h);for(int j=0;j<m;++j){auto it=reverse.find(gt[i*100+j]);if(it!=reverse.end())for(int a:it->second)hub_masks[a]|=reach[j];}
   for(int a=0;a<h;++a){counts[m][i*h+a]=hub_masks[a].count();gt1[m][i*h+a]=hub_masks[a][0];}
   for(auto& method:methods){int first=method.first[i];Bits cert;auto hi=hcol.find(first);if(hi!=hcol.end())cert=hub_masks[hi->second];else{auto own=local.find(first);if(own!=local.end())cert|=reach[own->second];for(int z=0;z<graph.K;++z){auto it=local.find(graph.at(first,z));if(it!=local.end())cert|=reach[it->second];}}
    for(int j=0;j<method.count;++j){auto it=local.find(method.entries[i*3+j]);if(it!=local.end())cert|=reach[it->second];}
    uint64_t lo=0,hiword=0;for(int j=0;j<m;++j)if(cert[j]){if(j<64)lo|=uint64_t(1)<<j;else hiword|=uint64_t(1)<<(j-64);}method.masks[m][i*2]=lo;method.masks[m][i*2+1]=hiword;
   }
  }
 }
 for(int m:{64,100}){write_raw(out/("all_H_m"+std::to_string(m)+"_count.u8"),counts[m]);write_raw(out/("all_H_m"+std::to_string(m)+"_GT1.u8"),gt1[m]);}
 for(auto& m:methods){fs::create_directories(out/m.name);write_raw(out/m.name/"first.i32",m.first);for(int size:{64,100})write_raw(out/m.name/("m"+std::to_string(size)+".mask.u64"),m.masks[size]);}
 struct rusage ru;getrusage(RUSAGE_SELF,&ru);require(ru.ru_maxrss<=40LL*1024*1024,"RSS cap");write_json(out/"complete.json",{{"status","PASS"},{"n",n},{"H",h},{"NSG_calls",0},{"ANN_calls",0},{"new_GT",0},{"new_graphs",0},{"new_training",0},{"graph_derived_labels",true},{"hub_adjacency_slots",hub_slots},{"core_adjacency_slots",core_slots},{"initial_distance_calls",initial_distance_calls},{"independent_BFS_checks",bfs_checks},{"seconds",seconds(start)},{"threads",1},{"cpu",15},{"maxrss_kib",ru.ru_maxrss}});return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
