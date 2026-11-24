#pragma once

#include <faiss/utils/distances.h>

namespace e216 {
using namespace e183;
constexpr size_t projected_dim = 64;
constexpr size_t vote_neighbors = 16;
constexpr size_t extra_limit = 16;

struct RowBank {
    std::vector<uint64_t> offsets;
    std::vector<int32_t> ids;
    explicit RowBank(const fs::path& path)
        : offsets(read_raw<uint64_t>(path.string()+".offsets.u64")),
          ids(read_raw<int32_t>(path.string()+".ids.i32")) {
        require(!offsets.empty() && offsets.front()==0 && offsets.back()==ids.size() &&
                std::is_sorted(offsets.begin(),offsets.end()),"valid row bank");
    }
    size_t size() const {return offsets.size()-1;}
    auto row(size_t i) const {
        return std::make_pair(ids.begin()+offsets[i],ids.begin()+offsets[i+1]);
    }
};

template<size_t N>
class IdSet {
    std::array<int32_t,N> keys;
    size_t position(int32_t id) const {
        size_t pos=(uint32_t(id)*2654435761u)&(N-1);
        while (keys[pos]!=-1 && keys[pos]!=id) pos=(pos+1)&(N-1);
        return pos;
    }
public:
    IdSet() {keys.fill(-1);}
    bool has(int32_t id) const {return keys[position(id)]==id;}
    void add(int32_t id) {keys[position(id)]=id;}
};

class Neighbors {
    using Ranked = std::pair<float,int32_t>;
    struct Vote {int32_t id; double score;};
    static constexpr size_t hash_size=4096;
    size_t d;
    std::vector<float> axes,unit;
    RowBank omissions,cache;
    hnswlib::InnerProductSpace space;
    HNSW graph;
    std::array<int32_t,hash_size> keys;
    std::array<double,hash_size> values;
    std::vector<size_t> used;
    std::vector<Vote> ranked_votes;

    std::array<Ranked,32> nearest(const float* query, bool cached) {
        std::array<float,projected_dim> projected;
        for (size_t j=0;j<projected_dim;++j)
            projected[j]=faiss::fvec_inner_product(query,axes.data()+j*d,d);
        const size_t ask=cached?4:32;
        auto small=graph.searchKnn(projected.data(),ask);
        require(small.size()==ask,"fixed approximate shortlist");
        std::array<Ranked,32> reranked;
        size_t i=0;
        while (!small.empty()) {
            const size_t index=small.top().second;
            small.pop();
            require(index<omissions.size(),"fit neighbor slot");
            reranked[i++]={-faiss::fvec_inner_product(query,unit.data()+index*d,d),int32_t(index)};
        }
        std::sort(reranked.begin(),reranked.begin()+ask);
        return reranked;
    }
public:
    Neighbors(const fs::path& model,size_t dim)
        :d(dim),axes(read_raw<float>(model/"axes.f32")),unit(read_raw<float>(model/"unit.f32")),
         omissions(model/"omissions"),cache(model/"cache"),space(projected_dim),
         graph(&space,(model/"fit.hnsw").string(),false,omissions.size()) {
        require(axes.size()==projected_dim*d && unit.size()==omissions.size()*d &&
                cache.size()==omissions.size() && graph.cur_element_count==omissions.size(),"online model shapes");
        keys.fill(-1);
        used.reserve(1600);
        ranked_votes.reserve(1600);
    }
    void set_mode(bool cached) {graph.setEf(cached?16:32);}

    size_t propose(const float* query, bool cached, const IdSet<512>& forbidden,
                   std::array<int32_t,extra_limit>& result, size_t limit) {
        if (!limit) return 0;
        const auto neighbor=nearest(query,cached);
        size_t n=0;
        if (cached) {
            const auto row=cache.row(neighbor[0].second);
            for (auto p=row.first;p!=row.second && n<limit;++p)
                if (!forbidden.has(*p)) result[n++]=*p;
            return n;
        }
        used.clear();
        ranked_votes.clear();
        for (size_t j=0;j<vote_neighbors;++j) {
            const auto row=omissions.row(neighbor[j].second);
            const double score=1.0/(j+1);
            for (auto p=row.first;p!=row.second;++p) {
                const int32_t id=*p;
                if (forbidden.has(id)) continue;
                size_t pos=(uint32_t(id)*2654435761u)&(hash_size-1);
                while (keys[pos]!=-1 && keys[pos]!=id) pos=(pos+1)&(hash_size-1);
                if (keys[pos]==-1) {
                    keys[pos]=id;
                    values[pos]=0;
                    used.push_back(pos);
                }
                values[pos]+=score;
            }
        }
        for (const size_t pos:used) {
            ranked_votes.push_back({keys[pos],values[pos]});
            keys[pos]=-1;
        }
        n=std::min(limit,ranked_votes.size());
        std::partial_sort(ranked_votes.begin(),ranked_votes.begin()+n,ranked_votes.end(),
            [](const Vote& a,const Vote& b){return a.score!=b.score?a.score>b.score:a.id<b.id;});
        for (size_t i=0;i<n;++i) result[i]=ranked_votes[i].id;
        return n;
    }
};

size_t replace_tail(Posting& table,size_t count,const std::array<int32_t,3>& route,
                    const faiss::idx_t* main,int k,Neighbors& neighbors,const float* q,bool cached) {
    IdSet<512> blocked,prefix;
    for (int i=0;i<k;++i) blocked.add(main[i]);
    for (size_t j=0;j<count;++j) blocked.add(table.candidate[j]);
    for (const int32_t label:route) {
        const int r=table.lookup(label,nullptr);
        require(r>=0,"existing routed table row");
        for (int i=0;i<std::min(16,int(table.counts[r]));++i)
            prefix.add(table.targets[size_t(r)*32+i]);
    }
    size_t tails=0;
    for (size_t j=0;j<count;++j) tails+=!prefix.has(table.candidate[j]);
    std::array<int32_t,extra_limit> more;
    const size_t n=neighbors.propose(q,cached,blocked,more,std::min(tails,extra_limit));
    if (!n) return 0;
    size_t j=0, tail_keep=tails-n;
    for (size_t i=0;i<count;++i) {
        const int32_t id=table.candidate[i];
        if (prefix.has(id)) table.candidate[j++]=id;
        else if (tail_keep>0) {
            table.candidate[j++]=id;
            --tail_keep;
        }
    }
    require(j+n==count,"actual distinct score budget is unchanged");
    std::copy_n(more.begin(),n,table.candidate.begin()+j);
    return n;
}

bool put(Posting& t,int k,int i,float d) {
    if (!std::isfinite(d)) return false;
    t.records[k+i]={t.candidate[i],d,uint32_t(k+i),false};
    return true;
}

void score_merge(Posting& t,faiss::DistanceComputer& dc,int k,int n,faiss::idx_t* ids,float* distances) {
    for (int j=0;j<k;++j) t.records[j]={ids[j],distances[j],uint32_t(j),false};
    int i=0;
    for (;i+3<n;i+=4) {
        auto* ids=&t.candidate[i];
        float d[4];
        dc.distances_batch_4(ids[0],ids[1],ids[2],ids[3],d[0],d[1],d[2],d[3]);
        for (int j=0;j<4;++j) if (!put(t,k,i+j,d[j])) return;
    }
    for (;i<n;++i) if (!put(t,k,i,dc(t.candidate[i]))) return;
    if (k==1) {
        auto best=t.records[0];
        for (int j=0;j<n;++j) if (t.records[1+j].distance<best.distance) best=t.records[1+j];
        ids[0]=best.id;
        distances[0]=best.distance;
        return;
    }
    auto end=t.heap.begin()+k;
    std::copy_n(t.records.begin(),k,t.heap.begin());
    std::make_heap(t.heap.begin(),end,Posting::better);
    for (int j=0;j<n;++j) {
        const auto& item=t.records[k+j];
        if (item.distance<t.heap[0].distance) {
            std::pop_heap(t.heap.begin(),end,Posting::better);
            t.heap[k-1]=item;
            std::push_heap(t.heap.begin(),end,Posting::better);
        }
    }
    std::sort(t.heap.begin(),end,Posting::better);
    for (int j=0;j<k;++j) {
        ids[j]=t.heap[j].id;
        distances[j]=t.heap[j].distance;
    }
}
}
