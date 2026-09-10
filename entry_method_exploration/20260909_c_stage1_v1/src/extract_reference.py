#!/usr/bin/env python3
"""Mechanical observer extraction, with the complete unchanged source snapshot retained."""
from pathlib import Path
import hashlib,json
V=Path(__file__).resolve().parents[1]
source=V/'source_before/ACSG/ACSG.cpp'
s=source.read_text()
a=s.index('    inline int insert_into_pool(Neighbor *addr')
b=s.index('    ACSG::ACSG(',a)
insert=s[a:b]
start=s.index('template <bool collect_fullset, class index_t>\nvoid ACSG::search_on_graph_new(')
body_start=s.index('\n{',start)
body=s[body_start:s.rfind('\n}')].rstrip()
needle='            int n = retset[k].id;'
assert body.count(needle)==1
body=body.replace(needle,needle+'\n            if (observer) observer->expanded_order.push_back(n);')
needle='    auto record_distance = [&](int id, bool neighbor) {'
assert body.count(needle)==1
body=body.replace(needle,needle+'\n        if (observer) observer->distance_order.push_back(id);')
signature='''inline void run(const Graph<int32_t>& graph, DistanceComputer& dis, VisitedTable& vt,
    int L, std::vector<Neighbor>& retset, const std::vector<EnterPoint>& enterpoints,
    int mode, int query_id, SearchTrace* trace, int ntotal, cstage1::Observer* observer)'''
out='#pragma once\n#include "state_machine.hpp"\nnamespace native_reference {\nusing namespace faiss;\nusing namespace acsg;\ninline std::mutex output_mutex;\n'+insert+signature+body+'\n}\n'
p=V/'src/native_reference.hpp';assert not p.exists();p.write_text(out)
(V/'src/native_reference.extraction.json').write_text(json.dumps({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'output_sha256':hashlib.sha256(out.encode()).hexdigest(),'signature_adaptation':'free function; explicit ntotal/mutex/observer; fixed int32 graph',
    'body_changes':['append expanded ID after original n capture','append evaluated ID at original record_distance'],
    'insertion_algorithm':'literal unchanged source extraction'},indent=2)+'\n')
