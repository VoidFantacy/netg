#include "hnswlib/hnswlib.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <array>
#include <set>
#include <iostream>
#include <chrono>
#include <sys/resource.h>
#include <sched.h>
using namespace hnswlib;
using json=nlohmann::json;namespace fs=std::filesystem;
using HNSW=HierarchicalNSW<float>;
struct Observed:public HNSW{
 using HNSW::HNSW;using dist_t=float;
     std::priority_queue<std::pair<dist_t, labeltype >>
    searchObserved(const void *query_data, size_t k, BaseFilterFunctor* isIdAllowed = nullptr) const {
        std::priority_queue<std::pair<dist_t, labeltype >> result;
        if (cur_element_count == 0) return result;

        tableint currObj = enterpoint_node_;
        dist_t curdist = fstdistfunc_(query_data, getDataByInternalId(enterpoint_node_), dist_func_param_);

        for (int level = maxlevel_; level > 0; level--) {
            bool changed = true;
            while (changed) {
                changed = false;
                unsigned int *data;

                data = (unsigned int *) get_linklist(currObj, level);
                int size = getListCount(data);
                metric_hops++;
                metric_distance_computations+=size;

                tableint *datal = (tableint *) (data + 1);
                for (int i = 0; i < size; i++) {
                    tableint cand = datal[i];
                    if (cand < 0 || cand > max_elements_)
                        throw std::runtime_error("cand error");
                    dist_t d = fstdistfunc_(query_data, getDataByInternalId(cand), dist_func_param_);

                    if (d < curdist) {
                        curdist = d;
                        currObj = cand;
                        changed = true;
                    }
                }
            }
        }

        std::priority_queue<std::pair<dist_t, tableint>, std::vector<std::pair<dist_t, tableint>>, CompareByFirst> top_candidates;
        bool bare_bone_search = !num_deleted_ && !isIdAllowed;
        if (bare_bone_search) {
            top_candidates = searchBaseLayerST<true,true>(
                    currObj, query_data, std::max(ef_, k), isIdAllowed);
        } else {
            top_candidates = searchBaseLayerST<false,true>(
                    currObj, query_data, std::max(ef_, k), isIdAllowed);
        }

        while (top_candidates.size() > k) {
            top_candidates.pop();
        }
        while (top_candidates.size() > 0) {
            std::pair<dist_t, tableint> rez = top_candidates.top();
            result.push(std::pair<dist_t, labeltype>(rez.first, getExternalLabel(rez.second)));
            top_candidates.pop();
        }
        return result;
    }

};
void require(bool x,const std::string&m){if(!x)throw std::runtime_error(m);}
template<class T>std::vector<T> raw(const fs::path&p){std::ifstream f(p,std::ios::binary|std::ios::ate);require(bool(f),"open "+p.string());auto n=f.tellg();require(n>=0&&size_t(n)%sizeof(T)==0,"shape");std::vector<T>v(size_t(n)/sizeof(T));f.seekg(0);f.read((char*)v.data(),n);require(bool(f),"read");return v;}
struct Counter{DISTFUNC<float>fn;void*param;uint64_t n=0;};
float count_fn(const void*a,const void*b,const void*p){auto*c=(Counter*)p;++c->n;return c->fn(a,b,c->param);}
template<class Q>std::vector<std::pair<float,labeltype>> unheap(Q h){std::vector<std::pair<float,labeltype>>v;while(!h.empty()){v.push_back(h.top());h.pop();}return v;}
void single(){cpu_set_t s;CPU_ZERO(&s);require(sched_getaffinity(0,sizeof(s),&s)==0&&CPU_COUNT(&s)==1&&CPU_ISSET(15,&s),"CPU15");std::ifstream f("/proc/self/status");std::string l;while(std::getline(f,l))if(l.rfind("Threads:",0)==0)require(std::stoi(l.substr(8))==1,"single thread");for(auto k:{"OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"})require(getenv(k)&&std::string(getenv(k))=="1","env");}
int main(int argc,char**argv){try{
 require(argc==3,"config fresh output");single();json c;std::ifstream(argv[1])>>c;fs::path out=argv[2];require(!fs::exists(out),"fresh output");fs::create_directory(out);auto start=std::chrono::steady_clock::now();
 std::ofstream csv(out/"queries.csv");csv<<"dataset,method,query,ndc,upper_expansions,upper_neighbor_scans,base_expansions,base_neighbor_scans,base_first_visit_distances,base_visited_skips\n";
 uint64_t ann=0,rows=0;json summary=json::array();
 for(auto ds:c["datasets"]){size_t d=ds["dimension"],H=ds["H"];auto q=raw<float>(ds["queries"].get<std::string>());require(q.size()==4096*d,"4096 queries");
  for(auto m:ds["methods"]){single();require(std::time(nullptr)<c["no_new_search_after_unix"].get<double>(),"search cutoff");InnerProductSpace space(d);Observed g(&space,m["graph"].get<std::string>(),false,H);g.setEf(10);require(g.num_deleted_==0&&g.cur_element_count==H,"no deletion");Counter counter{space.get_dist_func(),space.get_dist_func_param(),0};g.fstdistfunc_=count_fn;g.dist_func_param_=&counter;
   auto ids=raw<int32_t>(m["ids"].get<std::string>());auto w=raw<float>(m["W"].get<std::string>());require(ids.size()==H&&w.size()==H*d,"W IDs");for(size_t z=0;z<H;++z)require(g.getExternalLabel(z)==size_t(ids[z])&&!memcmp(g.getDataByInternalId(z),w.data()+z*d,d*4),"frozen rows");
   fs::path ref=m["reference"];auto entries=raw<int32_t>(ref/"entry_ids.i32");auto ndc=raw<uint64_t>(ref/"route_ndc.u64");require(entries.size()==4096*3&&ndc.size()==4096,"reference shape");std::array<uint64_t,8>sums{};
   for(size_t i=0;i<4096;++i){counter.n=0;g.metric_hops=0;g.metric_distance_computations=0;auto a=unheap(g.searchKnn(q.data()+i*d,3));++ann;uint64_t n=counter.n,uh=g.metric_hops,us=g.metric_distance_computations;
    counter.n=0;g.metric_hops=0;g.metric_distance_computations=0;auto b=unheap(g.searchObserved(q.data()+i*d,3));++ann;uint64_t th=g.metric_hops,ts=g.metric_distance_computations;
    require(a.size()==3&&b.size()==3&&counter.n==n&&n==ndc[i],"NDC parity");std::array<int32_t,3> e;for(int z=0;z<3;++z){require(a[z].second==b[z].second&&!memcmp(&a[z].first,&b[z].first,4),"full result parity");e[z]=a[z].second;}std::sort(e.begin(),e.end());require(!memcmp(e.data(),entries.data()+i*3,12),"E115 entries");
    require(th>=uh&&ts>=us&&n>=us+2,"nonnegative");uint64_t bh=th-uh,bs=ts-us,bnew=n-us-2;require(bs>=bnew&&bnew<=H-1,"visited identity");uint64_t skip=bs-bnew;std::array<uint64_t,8>v{n,uh,us,bh,bs,bnew,skip,1};for(int z=0;z<8;++z)sums[z]+=v[z];
    csv<<ds["dataset"].get<std::string>()<<','<<m["name"].get<std::string>()<<','<<i;for(int z=0;z<7;++z)csv<<','<<v[z];csv<<'\n';++rows;
   }
   json s={{"dataset",ds["dataset"]},{"method",m["name"]},{"n",4096}};std::array<std::string,7>keys{"ndc","upper_expansions","upper_neighbor_scans","base_expansions","base_neighbor_scans","base_first_visit_distances","base_visited_skips"};for(int z=0;z<7;++z)s[keys[z]]=double(sums[z])/4096;summary.push_back(s);
  }
 }
 single();require(ann==65536&&rows==32768,"exact costs");csv.close();std::ofstream(out/"summary.json")<<summary.dump(2)<<'\n';struct rusage ru;getrusage(RUSAGE_SELF,&ru);double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();json done={{"status","PASS"},{"ANN_calls",ann},{"NSG_calls",0},{"rows",rows},{"seconds",sec},{"maxrss_kib",ru.ru_maxrss},{"threads",1},{"cpu",sched_getcpu()},{"GT_read",false},{"formal_QPS",false},{"all_entry_distance_NDC_parity",true}};std::ofstream(out/"complete.json")<<done.dump(2)<<'\n';std::cout<<done.dump()<<std::endl;return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
