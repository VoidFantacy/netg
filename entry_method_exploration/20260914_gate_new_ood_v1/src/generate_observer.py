from common import *
import difflib
s=(ROOT/'ACSG/ACSG.cpp').read_text()
def body_at(pos):
    a=s.index('{',pos);depth=1;b=a+1
    while depth:
        if s[b]=='{':depth+=1
        if s[b]=='}':depth-=1
        b+=1
    return s[a:b]
insert=body_at(s.index('inline int insert_into_pool(Neighbor'))
body=body_at(s.index('void ACSG::search_on_graph_new('))
changed=body.replace('    RandomGenerator gen(0x1234);','    uint32_t current_depth = 0;\n    RandomGenerator gen(0x1234);').replace('        if (!trace) return;','        depth[id] = neighbor ? current_depth + 1 : 0;\n        if (!trace) return;').replace('            int n = retset[k].id;','            int n = retset[k].id;\n            current_depth = depth[n];')
assert changed!=body
header='''#pragma once
#include <mutex>
#include <faiss/impl/AuxIndexStructures.h>
#include <faiss/utils/random.h>
#include <ACSG/ACSG.h>
namespace e96_observer {
using namespace faiss; using namespace acsg;
inline std::mutex output_mutex;
inline int insert_into_pool(Neighbor* addr,int K,Neighbor nn)
'''+insert+'''
inline void run(const Graph<int32_t>& graph, DistanceComputer& dis, VisitedTable& vt,
 int L, std::vector<Neighbor>& retset, const std::vector<EnterPoint>& enterpoints,
 int mode, int query_id, SearchTrace* trace, int ntotal, std::vector<uint32_t>& depth)
'''+changed+'\n}\n'
(RUN/'src/observer.hpp').write_text(header)
(RUN/'reviews/observer_body.diff').write_text(''.join(difflib.unified_diff(body.splitlines(True),changed.splitlines(True),fromfile='original_ACSG_search_on_graph_new',tofile='first_discovery_depth_observer')))
dump(RUN/'reviews/observer_source.json',dict(source_sha256=sha(ROOT/'ACSG/ACSG.cpp'),generated_sha256=sha(RUN/'src/observer.hpp'),injected_statements=3))
