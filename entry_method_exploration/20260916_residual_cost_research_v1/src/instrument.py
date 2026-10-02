import pathlib
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent
s=(R/'ACSG/ACSG.cpp').read_text();i=s.index('void ACSG::search_on_graph_new(');head,body=s[:i],s[i:]
def rep(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
body=rep(body,'int n = retset[k].id;','int n = retset[k].id;\n            ++probe_counts.expansions;')
body=rep(body,'for (int m = 0; m < graph.K; m++) {','for (int m = 0; m < graph.K; m++) {\n                ++probe_counts.neighbor_slots;')
body=rep(body,'if (next_id >= 0 && next_id < ntotal) {','if (next_id >= 0 && next_id < ntotal) {\n                        ++probe_counts.prefetch_valid;\n                        if(vt.get(next_id)) ++probe_counts.prefetch_already_visited;')
body=rep(body,'''if (id < 0 || id >= ntotal || vt.get(id)) {
                    continue;
                }''','''if (id < 0 || id >= ntotal) { ++probe_counts.invalid_slots; continue; }
                if (vt.get(id)) { ++probe_counts.visited_skips; continue; }
                ++probe_counts.distances;''')
body=rep(body,'if (num_ids >= L && dist >= retset[L - 1].distance) {','if (num_ids >= L && dist >= retset[L - 1].distance) {\n                    ++probe_counts.bound_rejects;')
body=rep(body,'if (r < L) {','if (r < L) {\n                    ++probe_counts.accepted;')
(D/'src/ACSG.probe.cpp').write_text('#include "probe_counters.h"\n'+head+body)
s=(R/'ACSG/detail/CandidatePool.h').read_text();s=s.replace('#pragma once','#pragma once\n#include "probe_counters.h"')
s=rep(s,'int left = 0, right = capacity - 1;','++probe_counts.pool_calls;\n    int left = 0, right = capacity - 1;')
s=rep(s,'std::memmove(addr + 1, addr, live_count * sizeof(Neighbor));','probe_counts.copy_bytes += live_count * sizeof(Neighbor);\n        if(live_count==capacity) probe_counts.copy_bytes_full += live_count * sizeof(Neighbor);\n        std::memmove(addr + 1, addr, live_count * sizeof(Neighbor));')
s=rep(s,'std::memmove(addr + right + 1, addr + right,','probe_counts.copy_bytes += std::max(0, live_count - right) * sizeof(Neighbor);\n    if(live_count==capacity) probe_counts.copy_bytes_full += std::max(0, live_count - right) * sizeof(Neighbor);\n    std::memmove(addr + right + 1, addr + right,')
p=D/'src/probe_include/ACSG/detail/CandidatePool.h';p.parent.mkdir(parents=True);p.write_text(s)
p=D/'src/probe_common/hnswlib/hnswalg.h';s=p.read_text();s='#include "probe_counters.h"\n'+s
start=s.index('searchBaseLayerST(');end=s.index('getExternalLabel',s.index('return top_candidates;',start)) if False else s.index('return top_candidates;',start)
pre,body,post=s[:start],s[start:end],s[end:]
body=rep(body,'candidate_set.pop();','candidate_set.pop();\n            if(collect_metrics) ++probe_counts.h_candidate_pops;')
body=rep(body,'candidate_set.emplace(-dist, candidate_id);','candidate_set.emplace(-dist, candidate_id);\n                        if(collect_metrics) ++probe_counts.h_candidate_pushes;')
body=rep(body,'top_candidates.emplace(dist, candidate_id);','top_candidates.emplace(dist, candidate_id);\n                            if(collect_metrics) ++probe_counts.h_top_pushes;')
body=rep(body,'top_candidates.pop();','top_candidates.pop();\n                            if(collect_metrics) ++probe_counts.h_top_pops;')
s=pre+body+post
# Turn on original counters only for full searchKnn; routing graphs also count,
# but query-level reported full HNSW members are a separate object.
start=s.index('searchKnn(const void *query_data');pre,body=s[:start],s[start:]
body=rep(body,'searchBaseLayerST<true>(', 'searchBaseLayerST<true, true>(')
p.write_text(pre+body)
