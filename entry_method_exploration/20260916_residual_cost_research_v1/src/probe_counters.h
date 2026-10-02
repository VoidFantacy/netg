#pragma once
#include <cstdint>
struct ProbeCounters {
 uint64_t expansions=0,neighbor_slots=0,invalid_slots=0,visited_skips=0,distances=0;
 uint64_t accepted=0,bound_rejects=0,pool_calls=0,copy_bytes=0,copy_bytes_full=0;
 uint64_t prefetch_valid=0,prefetch_already_visited=0;
 uint64_t h_candidate_pushes=0,h_top_pushes=0,h_top_pops=0,h_candidate_pops=0;
};
inline thread_local ProbeCounters probe_counts;
