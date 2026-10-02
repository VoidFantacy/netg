#pragma once
#include "common/native_common.hpp"
#include <ACSG/detail/CandidatePool.h>
#include <faiss/impl/DistanceComputer.h>

// Research-only multi-entry adaptation of the Faiss NSG loop.
// Faiss NSG.cpp is MIT licensed; its insertion order is retained through the
// project's equivalent helper with live_count=capacity for the minimal mode.
// This is deliberately distinct from the linked, unmodified Faiss baseline.
struct TraceKernel {
    const acsg::Graph<int32_t>& graph;
    const std::vector<uint8_t>& spans;
    int ntotal;
    ComparisonRecorder recorder;
    std::vector<acsg::Neighbor> pool;
    TraceKernel(const acsg::Graph<int32_t>& g,const std::vector<uint8_t>& s,int n)
        :graph(g),spans(s),ntotal(n){pool.reserve(1501);}

    template<bool Span,bool Filter,bool Batch4,bool Prefetch=true,bool Compact=true>
    void search(faiss::DistanceComputer& dis,faiss::VisitedTable& vt,
                const std::vector<acsg::EnterPoint>& entries,int L,int K,
                faiss::idx_t* ids,float* distances) {
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
        std::sort(pool.begin(),pool.begin()+live,[&](const Neighbor&a,const Neighbor&b){recorder.compare(a.id,a.distance,b.id,b.distance,1);return a<b;});
        bool compact=Compact&&std::all_of(pool.begin(),pool.begin()+live,[](const Neighbor& v){return std::isfinite(v.distance)&&v.distance<std::numeric_limits<float>::max();});
        int k=0;
        while(k<L&&k<live){
            int updated=L;
            if(pool[k].flag){
                pool[k].flag=false;
                const int node=pool[k].id;
                const int width=Span?spans[node]:graph.K;
                auto insert=[&](int id,float distance){
                    if(live>=L)recorder.compare(id,distance,pool[L-1].id,pool[L-1].distance,2);
                    if(live>=L&&distance>=pool[L-1].distance)return;
                    if(live<L&&(!std::isfinite(distance)||distance>=std::numeric_limits<float>::max()))compact=false;
                    int r=traced_insert_into_pool_live(pool.data(),L,compact?std::min(L,live):L,Neighbor(id,distance,true),recorder);
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
            k=updated<=k?updated:k+1;
        }
        for(int i=0;i<K;++i){ids[i]=pool[i].id;distances[i]=pool[i].id<0?std::numeric_limits<float>::max():pool[i].distance;}
    }
};
