#pragma once
#include "common/native_common.hpp"
#include <ACSG/detail/CandidatePool.h>
#include <faiss/impl/DistanceComputer.h>

// Research-only multi-entry adaptation of the Faiss NSG loop.
// Faiss NSG.cpp is MIT licensed; its insertion order is retained through the
// project's equivalent helper with live_count=capacity for the minimal mode.
// This is deliberately distinct from the linked, unmodified Faiss baseline.
struct ResearchKernel {
    const acsg::Graph<int32_t>& graph;
    const std::vector<uint8_t>& spans;
    int ntotal;
    std::vector<acsg::Neighbor> pool;
    int first_expanded=-1;
    ResearchKernel(const acsg::Graph<int32_t>& g,const std::vector<uint8_t>& s,int n)
        :graph(g),spans(s),ntotal(n){pool.reserve(1501);}

    template<bool Span,bool Filter,bool Batch4,bool Prefetch=true,bool Compact=true,bool ForcePrimary=false>
    void search(faiss::DistanceComputer& dis,faiss::VisitedTable& vt,
                const std::vector<acsg::EnterPoint>& entries,int L,int K,
                faiss::idx_t* ids,float* distances,int primary=-1) {
        using acsg::Neighbor;
        faiss::DistanceComputer* stored=&dis;
        while(auto* neg=dynamic_cast<faiss::NegativeDistanceComputer*>(stored))stored=neg->basedis;
        auto* flat=dynamic_cast<faiss::FlatCodesDistanceComputer*>(stored);
        const uint8_t* codes=flat?flat->codes:nullptr;
        const size_t stride=flat?flat->code_size:0;
        faiss::RandomGenerator gen(0x1234);
        pool.resize(L+1);
        for(auto& v:pool){v.distance=std::numeric_limits<float>::max();v.id=-1;v.flag=false;}
        int live=0;
        for(size_t i=0;i<std::min<size_t>(3,entries.size())&&live<L;++i){
            int id=entries[i].id;
            if(id<0||id>=ntotal)throw std::runtime_error("invalid research entry");
            if(!vt.get(id)){vt.set(id);pool[live++]=Neighbor(id,dis(id),true);}
        }
        if(!live){int id;do{id=gen.rand_int(ntotal);}while(vt.get(id));vt.set(id);pool[live++]=Neighbor(id,dis(id),true);}
        std::sort(pool.begin(),pool.begin()+live);
        bool compact=Compact&&std::all_of(pool.begin(),pool.begin()+live,[](const Neighbor& v){return std::isfinite(v.distance)&&v.distance<std::numeric_limits<float>::max();});
        int k=0; first_expanded=-1; bool first_iteration=true;
        if constexpr(ForcePrimary){while(k<live&&pool[k].id!=primary)++k;if(k==live)throw std::runtime_error("primary absent");}
        while(k<L&&k<live){
            int updated=L;
            if(pool[k].flag){
                pool[k].flag=false;
                const int node=pool[k].id;
                if(first_expanded<0)first_expanded=node;
                const int width=Span?spans[node]:graph.K;
                auto insert=[&](int id,float distance){
                    if(live>=L&&distance>=pool[L-1].distance)return;
                    if(live<L&&(!std::isfinite(distance)||distance>=std::numeric_limits<float>::max()))compact=false;
                    int r=acsg::detail::insert_into_pool_live(pool.data(),L,compact?std::min(L,live):L,Neighbor(id,distance,true));
                    if(r<L){updated=std::min(updated,r);if(live<L)++live;}
                };
                if constexpr(Batch4){
                    int m=0;
                    while(m<width){
                        int batch_ids[4],count=0;
                        while(m<width&&count<4){
                            int id=graph.at(node,m++);
                            if(id<0||id>=ntotal||vt.get(id))continue;
                            vt.set(id);batch_ids[count++]=id;
                            if(codes&&stride)__builtin_prefetch(codes+size_t(id)*stride,0,3);
                        }
                        float values[4];
                        if(count==4)dis.distances_batch_4(batch_ids[0],batch_ids[1],batch_ids[2],batch_ids[3],values[0],values[1],values[2],values[3]);
                        else for(int j=0;j<count;++j)values[j]=dis(batch_ids[j]);
                        for(int j=0;j<count;++j)insert(batch_ids[j],values[j]);
                    }
                }else{
                    for(int m=0;m<width;++m){
                        if constexpr(Prefetch){
                            if(m+1<width){int next=graph.at(node,m+1);
                                if(next>=0&&next<ntotal){
                                    __builtin_prefetch(vt.visited.data()+next,0,3);
                                    if(codes&&stride&&(!Filter||!vt.get(next)))__builtin_prefetch(codes+size_t(next)*stride,0,3);
                                }
                            }
                        }
                        int id=graph.at(node,m);
                        if(id<0||id>=ntotal||vt.get(id))continue;
                        vt.set(id);insert(id,dis(id));
                    }
                }
            }
            if constexpr(ForcePrimary){if(first_iteration){k=0;first_iteration=false;}else k=updated<=k?updated:k+1;}
            else k=updated<=k?updated:k+1;
        }
        for(int i=0;i<K;++i){ids[i]=pool[i].id;distances[i]=pool[i].id<0?std::numeric_limits<float>::max():pool[i].distance;}
    }
};

using KernelCall=void(ResearchKernel::*)(faiss::DistanceComputer&,faiss::VisitedTable&,const std::vector<acsg::EnterPoint>&,int,int,faiss::idx_t*,float*);
inline KernelCall kernel_call(const std::string& name){
    if(name=="GT10-minimal")return &ResearchKernel::search<false,false,false,false,false>;
    if(name=="GT10-core")return &ResearchKernel::search<false,false,false>;
    if(name=="GT10-span")return &ResearchKernel::search<true,false,false>;
    if(name=="GT10-prefetch-filter")return &ResearchKernel::search<false,true,false>;
    if(name=="GT10-batch4")return &ResearchKernel::search<false,false,true>;
    if(name=="GT10-span-batch4")return &ResearchKernel::search<true,false,true>;
    throw std::runtime_error("unknown research kernel "+name);
}

inline std::vector<uint8_t> make_spans(const acsg::Graph<int32_t>& graph,int ntotal){
    require(graph.K>0&&graph.K<=255,"uint8 span capacity");
    std::vector<uint8_t> spans(graph.N);
    for(int n=0;n<graph.N;++n)for(int m=graph.K-1;m>=0;--m){int id=graph.at(n,m);if(id>=0&&id<ntotal){spans[n]=m+1;break;}}
    return spans;
}
