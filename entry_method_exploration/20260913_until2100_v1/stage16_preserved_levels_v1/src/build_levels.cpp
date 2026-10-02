#include "benches/hnswlib/hnswlib.h"
#include <nlohmann/json.hpp>
#include <fstream>
#include <filesystem>
#include <iostream>
#include <random>
#include <set>
#include <chrono>
#include <sched.h>
using json=nlohmann::json; namespace fs=std::filesystem;
using Graph=hnswlib::HierarchicalNSW<float>;
void req(bool x,const std::string& s){if(!x)throw std::runtime_error(s);}
template<class T> std::vector<T> readraw(const std::string& p){std::ifstream f(p,std::ios::binary|std::ios::ate);req(bool(f),p);size_t b=f.tellg();req(b%sizeof(T)==0,"raw size");std::vector<T>x(b/sizeof(T));f.seekg(0);f.read((char*)x.data(),b);req(bool(f),"raw read");return x;}
void valid_keep(const std::vector<int32_t>& keep,size_t n){req(!keep.empty(),"empty keep");int32_t prev=-1;for(auto k:keep){req(k>prev && k>=0 && size_t(k)<n,"invalid keep");prev=k;}}
std::vector<int> stream(size_t n,size_t seed){std::default_random_engine rng(seed);std::vector<int> r(n);for(auto& level:r){std::uniform_real_distribution<double> u(0.,1.);level=int(-log(u(rng))*(1.0/log(16.)));}return r;}
std::vector<int> levels_by_label(Graph& g){std::vector<int> out(g.cur_element_count,-1);for(size_t i=0;i<g.cur_element_count;++i){auto label=g.getExternalLabel(i);req(label<out.size() && out[label]<0,"source labels");out[label]=g.element_levels_[i];}return out;}
void fill(Graph& g,const std::vector<float>& w,size_t d,const std::vector<int32_t>& keep,size_t source_n,bool preserve,size_t label_offset=0){valid_keep(keep,source_n);size_t next=0;for(size_t i=0;i<source_n;++i){if(next<keep.size() && keep[next]==int32_t(i)){g.addPoint(w.data()+next*d,label_offset+next);++next;}else if(preserve)g.getRandomLevel(g.mult_);}req(next==keep.size(),"fill count");}
void contract(){cpu_set_t c;CPU_ZERO(&c);req(sched_getaffinity(0,sizeof(c),&c)==0 && CPU_COUNT(&c)==1 && CPU_ISSET(15,&c),"CPU15");std::ifstream f("/proc/self/status");std::string l;int t=0;while(std::getline(f,l))if(l.rfind("Threads:",0)==0)t=std::stoi(l.substr(8));req(t==1,"threads1");}
json synthetic(){
 const size_t n=256,d=8,seed=20260828;hnswlib::InnerProductSpace s(d);auto seq=stream(n,seed);
 std::vector<float>w(n*d,0);for(size_t i=0;i<n;++i)w[i*d]=1; // exact distance ties
 Graph full(&s,n,16,200,seed);for(size_t i=0;i<n;++i)full.addPoint(w.data()+i*d,1000+i);
 req(full.element_levels_==seq,"synthetic source RNG");size_t entry=full.enterpoint_node_;
 std::vector<int32_t> keep;for(size_t i=0;i<n;++i)if(i!=entry && i%3!=1)keep.push_back(i);
 std::vector<float>small(keep.size()*d);for(size_t i=0;i<keep.size();++i)std::copy_n(w.data()+keep[i]*d,d,small.data()+i*d);
 Graph ord(&s,keep.size(),16,200,seed),a(&s,keep.size(),16,200,seed),b(&s,keep.size(),16,200,seed);
 fill(ord,small,d,keep,n,false,2000);fill(a,small,d,keep,n,true,2000);fill(b,small,d,keep,n,true,2000);
 size_t zeros=0,positive=0,changed=0;for(size_t i=0;i<keep.size();++i){req(a.element_levels_[i]==seq[keep[i]] && a.element_levels_[i]==b.element_levels_[i],"preserved level");zeros+=seq[keep[i]]==0;positive+=seq[keep[i]]>0;changed+=a.element_levels_[i]!=ord.element_levels_[i];req(a.getExternalLabel(i)==2000+i,"external labels");}
 req(zeros && positive && changed,"synthetic coverage");req(a.element_levels_[a.enterpoint_node_]==a.maxlevel_,"legal new entry");
 size_t rejected=0;for(auto bad:std::vector<std::vector<int32_t>>{{},{-1},{0,256},{3,2},{2,2}}){try{valid_keep(bad,n);}catch(const std::exception&){++rejected;}}req(rejected==5,"negative mapping coverage");
 for(size_t q=0;q<128;++q){auto ha=a.searchKnn(w.data(),7),hb=b.searchKnn(w.data(),7);req(ha.size()==hb.size(),"repeat heap size");auto ho=ord.searchKnn(w.data(),7);auto hf=full.searchKnn(w.data(),7);req(ho.size()==7 && hf.size()==7,"query size");while(!ha.empty()){req(ha.top()==hb.top(),"repeat tie queries");hb.pop();req(ha.top().second>=2000 && ha.top().second<2000+keep.size(),"query external label");ha.pop();}}
 return {{"status","PASS"},{"builds",4},{"HNSW",512},{"NSG",0},{"zero_levels",zeros},{"positive_levels",positive},{"ordinary_level_changes",changed},{"source_highest_entry_deleted",entry},{"invalid_keep_rejections",rejected},{"nonidentity_external_labels",true},{"tie_repeat_queries",128}};
}
int main(int argc,char**argv){try{contract();req(argc>=2,"mode");std::string mode=argv[1];if(mode=="synthetic"){std::cout<<synthetic().dump()<<std::endl;return 0;}req(argc==4,"inspect/build config output");req(!fs::exists(argv[3]),"refuse overwrite");std::ifstream f(argv[2]);json c;f>>c;size_t n=c.at("source_count"),d=c.at("dim"),seed=c.at("seed");auto expected=stream(n,seed);auto keep=readraw<int32_t>(c.at("original_slots"));valid_keep(keep,n);
 if(mode=="inspect") { // reads serialized levels with no graph object/construction/search
  auto raw=readraw<char>(c.at("source_graph"));req(raw.size()>=96,"header");auto u64=[&](size_t p){uint64_t x;memcpy(&x,raw.data()+p,8);return x;};req(u64(16)==n,"source n");size_t sz=u64(24),label=u64(32),cursor=96+n*sz;std::vector<int> observed(n,-1);for(size_t i=0;i<n;++i){uint32_t bytes;req(cursor+4<=raw.size(),"upper bounds");memcpy(&bytes,raw.data()+cursor,4);cursor+=4;req(bytes%68==0 && cursor+bytes<=raw.size(),"upper shape");size_t external=u64(96+i*sz+label);req(external<n && observed[external]<0,"source slot labels");observed[external]=bytes/68;cursor+=bytes;}req(cursor==raw.size() && observed==expected,"full source RNG mismatch");std::ofstream o(argv[3]);o<<json({{"status","PASS"},{"source_levels",observed},{"source_count",n},{"retained_count",keep.size()},{"builds",0},{"HNSW",0},{"NSG",0},{"seed",seed}}).dump(2)<<std::endl;
 } else {req(mode=="build","unknown mode");auto w=readraw<float>(c.at("W"));req(w.size()==keep.size()*d,"W shape");auto start=std::chrono::steady_clock::now();hnswlib::InnerProductSpace s(d);Graph g(&s,keep.size(),16,200,seed);fill(g,w,d,keep,n,true);for(size_t i=0;i<keep.size();++i){req(g.element_levels_[i]==expected[keep[i]],"level invariant");req(g.getExternalLabel(i)==i && !memcmp(g.getDataByInternalId(i),w.data()+i*d,d*4),"graph bytes");}req(g.element_levels_[g.enterpoint_node_]==g.maxlevel_,"entry level");g.saveIndex(argv[3]);double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();std::cout<<json({{"status","PASS"},{"builds",1},{"HNSW",0},{"NSG",0},{"build_seconds",seconds},{"levels",g.element_levels_},{"entry",g.enterpoint_node_},{"entry_original_slot",keep[g.enterpoint_node_]},{"maxlevel",g.maxlevel_},{"process_threads",1},{"CPU",15}}).dump()<<std::endl;}
 return 0;}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
