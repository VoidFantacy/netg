#pragma once
#include "optimized.hpp"

namespace exp172::m5 {

// A frozen table is Nx7 little-endian i32: route, winner, count, four IDs.
// Selection and fitting are offline; no GT, query ID, or training lookup is
// available to this helper. Route-only uses winner=-1 in the same format.
struct CompletionTable {
    std::vector<std::array<int32_t, 7>> rows;
    bool conditioned;
    explicit CompletionTable(const std::string& path, bool pair,
                             uint32_t base_n, const Posting& post)
        : conditioned(pair) {
        require(base_n == post.base_n, "completion frozen posting base identity");
        auto words = read_raw<int32_t>(path);
        require(words.size() % 7 == 0, "completion Nx7 layout");
        rows.resize(words.size() / 7);
        if (!words.empty()) memcpy(rows.data(), words.data(), words.size() * 4);
        for (size_t j = 0; j < rows.size(); ++j) {
            const auto& row = rows[j];
            require(row[0] >= 0 && uint32_t(row[0]) < base_n &&
                    std::binary_search(post.sorted_labels.begin(),
                                       post.sorted_labels.end(), row[0]),
                    "completion route belongs to frozen router");
            require(pair ? (row[1] >= 0 && uint32_t(row[1]) < base_n)
                         : row[1] == -1, "completion anchor domain");
            if (pair) {
                auto route_it = std::lower_bound(post.sorted_labels.begin(), post.sorted_labels.end(), row[0]);
                const int slot = post.sorted_slots[size_t(route_it-post.sorted_labels.begin())];
                require(std::find(post.targets.begin()+size_t(slot)*8,
                                  post.targets.begin()+size_t(slot)*8+post.counts[slot], row[1]) !=
                                  post.targets.begin()+size_t(slot)*8+post.counts[slot],
                        "completion winner belongs to its original posting row");
            }
            require(row[2] >= 0 && row[2] <= 4, "completion row cap four");
            if (j) require(std::pair<int32_t,int32_t>{rows[j-1][0], rows[j-1][1]} <
                           std::pair<int32_t,int32_t>{row[0],row[1]},
                           "completion keys unique and strictly sorted");
            std::set<int32_t> seen;
            for (int k = 0; k < 4; ++k) {
                if (k < row[2]) require(row[3+k] >= 0 && uint32_t(row[3+k]) < base_n &&
                                       seen.insert(row[3+k]).second,
                                       "completion target domain and uniqueness");
                else require(row[3+k] == -1, "completion unused padding");
            }
        }
    }
    const std::array<int32_t,7>* lookup(int32_t route, int32_t winner) const {
        const auto key = std::make_pair(route, conditioned ? winner : -1);
        auto it = std::lower_bound(rows.begin(), rows.end(), key,
                [](const auto& row, const auto& k) {
                    return std::make_pair(row[0], row[1]) < k;
                });
        if (it == rows.end() || std::make_pair((*it)[0],(*it)[1]) != key) return nullptr;
        return &*it;
    }
    size_t resident_bytes() const { return sizeof(*this) + rows.capacity()*sizeof(rows[0]) + 64; }
};

inline void applyCompletion(faiss::DistanceComputer& dc,
        const std::array<int32_t,3>& route, int K, faiss::idx_t* I, float* D,
        Posting& post, const CompletionTable& table,
        OptimizedStats* stats=nullptr, CandidateAudit* audit=nullptr) {
    require((K == 1 || K == 100) && !post.global, "completion frozen native contract");
    if (stats) ++stats->queries;
    if (audit) {
        *audit = CandidateAudit{}; audit->K = K;
        for (int j=0;j<K;++j) { audit->r_ids[j]=I[j]; audit->r_distances[j]=D[j]; }
    }
    if (post.empty) return;
    auto* ps = stats ? &stats->post : nullptr;
    std::array<int,3> slots{{-1,-1,-1}};
    std::array<std::array<int,8>,3> maps{};
    for (auto& map : maps) map.fill(-1);
    int nc=0;
    for (int row=0;row<3;++row) {
        int slot=post.lookup(route[row],ps);
        if(slot<0) return;
        slots[row]=slot;
        if(ps) ++ps->row_reads;
        for(int j=0;j<post.counts[slot];++j) {
            const int32_t id=post.targets[size_t(slot)*8+j];
            bool in_r=false;
            for(int r=0;r<K;++r) if(I[r]==id) { in_r=true;break; }
            if(in_r) continue;
            int ci=0; while(ci<nc && post.candidate[ci]!=id) ++ci;
            if(ci==nc) { require(nc<24,"completion preserves original C24"); post.candidate[nc++]=id; }
            maps[row][j]=ci;
        }
    }
    if(ps) ps->candidates+=nc;
    if(audit) audit->planned_candidates=nc;
    if(!nc) return;
    // Caller qualifies main R words against a separate fresh scalar DC for
    // every saved untimed query before timing. This is score reuse only;
    // original main traversal, visited and routing remain unchanged.
    bool reuse = true;
    for(int j=0;j<K;++j) if(I[j] < -1 || (I[j]>=0 && !std::isfinite(D[j]))) reuse=false;
    if(stats) { if(reuse) ++stats->r_cache_queries; else ++stats->r_cache_fallback_queries; }
    for(int j=0;j<K;++j) {
        float value=std::numeric_limits<float>::max();
        if(I[j]>=0) {
            if(reuse) { value=D[j]; if(stats)++stats->r_cache_hits; }
            else { value=dc(I[j]);if(ps)++ps->dots; }
            if(audit && reuse) {
                float checked=dc(I[j]);if(ps)++ps->dots;
                if(stats){++stats->r_word_checks;++stats->r_word_check_dots;}
                const bool equal=optimized_word_equal(value,checked);
                if(!equal && stats)++stats->r_word_mismatches;
                require(equal,"completion cached main R word equals actual fresh scalar");
            }
            if(audit)audit->r_distances[j]=value;
            if(!std::isfinite(value)){if(ps)++ps->nonfinite_failures;return;}
        }
        post.records[j]={I[j],value,uint32_t(j),I[j]<0};
    }
    if(audit) audit->r_rescored_complete=true;
    for(int ci=0;ci<nc;++ci) {
        float value=dc(post.candidate[ci]); if(ps)++ps->dots;
        if(audit) { audit->c_ids[ci]=post.candidate[ci];audit->c_distances[ci]=value;audit->nc=ci+1; }
        if(!std::isfinite(value)) { if(ps)++ps->nonfinite_failures; return; }
        post.records[K+ci]={post.candidate[ci],value,uint32_t(K+ci),false};
    }
    auto merge=[&](const Posting::Record& value) {
        if(post.heap[0].padding || value.distance<post.heap[0].distance) {
            std::pop_heap(post.heap.begin(),post.heap.begin()+K,Posting::better);
            post.heap[K-1]=value;
            std::push_heap(post.heap.begin(),post.heap.begin()+K,Posting::better);
        }
    };
    auto emit=[&]() {
        std::sort(post.heap.begin(),post.heap.begin()+K,Posting::better);
        for(int j=0;j<K;++j) {
            I[j]=post.heap[j].padding?-1:post.heap[j].id;
            D[j]=post.heap[j].padding?std::numeric_limits<float>::max():post.heap[j].distance;
        }
    };
    std::copy(post.records.begin(),post.records.begin()+K,post.heap.begin());
    std::make_heap(post.heap.begin(),post.heap.begin()+K,Posting::better);
    for(int ci=0;ci<nc;++ci) merge(post.records[K+ci]);
    if(ps)++ps->commits;
    if(audit)audit->m5_committed=true;
    const auto m5_heap=post.heap;
    std::array<int32_t,12> x{}; int nx=0;
    for(int row=0;row<3;++row) {
        int best=-1;
        for(int j=0;j<post.counts[slots[row]];++j) {
            int ci=maps[row][j]; if(ci<0)continue;
            if(stats)++stats->seed_candidates;
            if(best<0 || Posting::better(post.records[K+ci],post.records[K+best]))best=ci;
        }
        int32_t winner=best<0?-1:post.candidate[best];
        if(best>=0) {
            if(stats)++stats->seeds_selected;
            if(audit) { audit->seeds[row]=winner;audit->seed_distances[row]=post.records[K+best].distance;
                        audit->seed_route_positions[row]=row;++audit->nseeds; }
        }
        if(table.conditioned && best<0)continue;
        const auto* found=table.lookup(route[row],winner);
        if(!found)continue;
        for(int j=0;j<(*found)[2];++j) {
            const int32_t id=(*found)[3+j]; bool duplicate=false;
            for(int r=0;r<K;++r) if(post.records[r].id==id){duplicate=true;break;}
            for(int c=0;!duplicate && c<nc;++c) if(post.candidate[c]==id)duplicate=true;
            for(int t=0;!duplicate && t<nx;++t) if(x[t]==id)duplicate=true;
            if(duplicate)continue;
            require(nx<12,"completion extra scalar cap twelve");
            float value=dc(id);if(stats)++stats->new_distances;x[nx]=id;
            if(audit){audit->x_ids[nx]=id;audit->x_distances[nx]=value;audit->nx=nx+1;}
            if(!std::isfinite(value)) {
                post.heap=m5_heap;emit();
                if(stats)++stats->extension_nonfinite_failures;
                if(audit)audit->extension_aborted=true;
                return;
            }
            merge({id,value,uint32_t(K+nc+nx),false});++nx;
        }
    }
    emit();
    if(nx && stats)++stats->extension_commits;
}
}
