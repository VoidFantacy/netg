#pragma once
#include "native_common.hpp"
#include <zlib.h>
using HNSW=hnswlib::HierarchicalNSW<float>;
struct Gzip {
 gzFile f;bool writing;
 Gzip(const fs::path& p,bool w):writing(w){f=gzopen(p.c_str(),w?"wb6":"rb");require(f!=nullptr,"gzip open");gzbuffer(f,1024*1024);}
 void bytes(void* p,size_t z){while(z){unsigned step=std::min<size_t>(z,1<<20);int got=writing?gzwrite(f,p,step):gzread(f,p,step);require(got==int(step),"gzip truncated/write failed");p=(char*)p+step;z-=step;}}
 template<class T> void value(T& v){bytes(&v,sizeof(T));}
 void close(){require(gzclose(f)==Z_OK,"gzip close failed");f=nullptr;}
 ~Gzip(){if(f)gzclose(f);}
};
inline uint64_t fnv(uint64_t h,const void* p,size_t n){auto b=(const uint8_t*)p;for(size_t j=0;j<n;++j){h^=b[j];h*=1099511628211ULL;}return h;}
// Full vectors and ordered valid links, labels and levels are checked for EVERY node.
inline uint64_t digest_graph(HNSW& g,const Fvecs& base){uint64_t hash=1469598103934665603ULL;std::vector<uint8_t> labels(base.n,0);
 require(g.cur_element_count==base.n,"full-base HNSW node count");
 for(size_t i=0;i<base.n;++i){uint64_t label=g.getExternalLabel(i);int level=g.element_levels_[i];require(label<base.n&&!labels[label],"label identity");labels[label]=1;require(std::memcmp(g.getDataByInternalId(i),base.row(label),base.d*4)==0,"vector bytes differ");hash=fnv(hash,&label,8);hash=fnv(hash,&level,4);hash=fnv(hash,g.getDataByInternalId(i),base.d*4);
 for(int l=0;l<=level;++l){auto p=g.get_linklist_at_level(i,l);uint32_t n=g.getListCount(p);require(n<=(l?g.maxM_:g.maxM0_),"degree exceeds capacity");hash=fnv(hash,&n,4);hash=fnv(hash,p+1,n*4);for(uint32_t j=0;j<n;++j)require(p[1+j]<base.n&&p[1+j]!=i,"invalid adjacency");}}
 return hash;
}
inline void save_topology(HNSW& g,const Fvecs& base,const fs::path& p){require(!fs::exists(p),"preserve topology output");Gzip z(p,true);uint64_t magic=0x313654504F543936ULL,n=base.n,d=base.d,m=g.M_,efc=g.ef_construction_,seed=20260828;int32_t level=g.maxlevel_;uint32_t entry=g.enterpoint_node_;z.value(magic);z.value(n);z.value(d);z.value(m);z.value(efc);z.value(seed);z.value(level);z.value(entry);
 for(size_t i=0;i<n;++i){uint64_t label=g.getExternalLabel(i);uint32_t lev=g.element_levels_[i];z.value(label);z.value(lev);for(uint32_t l=0;l<=lev;++l){auto a=g.get_linklist_at_level(i,l);uint32_t count=g.getListCount(a);z.value(count);z.bytes(a+1,count*4);}if(i%100000==0)resources(p.parent_path());}z.close();}
inline std::unique_ptr<HNSW> load_topology(const fs::path& p,Fvecs& base,hnswlib::SpaceInterface<float>* space){Gzip z(p,false);uint64_t magic,n,d,m,efc,seed;int32_t level;uint32_t entry;z.value(magic);z.value(n);z.value(d);z.value(m);z.value(efc);z.value(seed);z.value(level);z.value(entry);require(magic==0x313654504F543936ULL&&n==base.n&&d==base.d&&m==32&&efc==200&&seed==20260828&&entry<n,"topology metadata");auto g=std::make_unique<HNSW>(space,n,m,efc,seed);g->label_lookup_.reserve(n);
 for(size_t i=0;i<n;++i){uint64_t label;uint32_t lev;z.value(label);z.value(lev);require(label<n&&lev<=uint32_t(level),"topology label/level");g->element_levels_[i]=lev;std::memset(g->data_level0_memory_+i*g->size_data_per_element_,0,g->size_data_per_element_);g->setExternalLabel(i,label);std::memcpy(g->getDataByInternalId(i),base.row(label),d*4);require(g->label_lookup_.emplace(label,i).second,"duplicate topology label");g->linkLists_[i]=nullptr;if(lev){g->linkLists_[i]=(char*)calloc(1,lev*g->size_links_per_element_+1);require(g->linkLists_[i],"upper links allocation");}for(uint32_t l=0;l<=lev;++l){uint32_t count;z.value(count);require(count<=(l?g->maxM_:g->maxM0_),"topology degree");auto a=g->get_linklist_at_level(i,l);g->setListCount(a,count);z.bytes(a+1,count*4);}g->cur_element_count=i+1;}
 g->maxlevel_=level;g->enterpoint_node_=entry;char trailing;require(gzread(z.f,&trailing,1)==0,"trailing topology bytes");z.close();return g;}
inline std::vector<std::pair<float,hnswlib::labeltype>> hnsw_result(HNSW& h,const float* q){auto heap=h.searchKnn(q,10);std::vector<std::pair<float,hnswlib::labeltype>> r;while(!heap.empty()){r.push_back(heap.top());heap.pop();}return r;}
