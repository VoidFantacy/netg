#include <cstdint>
#include <cstddef>
// Pure sufficient-statistic aggregation; no graph, query prediction, or GT lookup.
extern "C" void aggregate(int nfit,int actions,const int32_t* query_rows,const int32_t* owner_donors,
    const int64_t* starts,const int32_t* groups,const uint64_t* lows,const uint64_t* highs,const int32_t* counts,
    const uint64_t* hits,const double* time_deltas,int64_t* region_members,int64_t* region_queries,int64_t* region_hits,double* region_time) {
    for(int i=0;i<nfit;++i) {
        int q=query_rows[i],donor=owner_donors[i];
        for(int64_t at=starts[donor];at<starts[donor+1];++at) {
            int g=groups[at],count=counts[at];uint64_t lo=lows[at],hi=highs[at];
            region_members[g]+=count;region_queries[g]++;
            for(int a=0;a<actions;++a) {
                size_t source=(size_t(q)*actions+a)*2,target=size_t(g)*actions+a;
                region_hits[target]+=__builtin_popcountll(hits[source]&lo)+__builtin_popcountll(hits[source+1]&hi);
                region_time[target*2]+=count*time_deltas[source];region_time[target*2+1]+=count*time_deltas[source+1];
            }
        }
    }
}
