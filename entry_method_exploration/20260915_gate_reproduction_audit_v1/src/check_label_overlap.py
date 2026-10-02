"""Diagnose contradictory cached release labels, without changing E96."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import ast
import json
from pathlib import Path
import numpy as np

ROOT = Path('/data/netg/ACSG')
E96 = ROOT/'entry_method_exploration/20260914_gate_new_ood_v1'
OUT = Path(__file__).resolve().parents[1]
tree = ast.parse((E96/'src/train_gate.py').read_text())
env = {'np':np}
defs = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='release_samples']
exec(compile(ast.Module(body=defs,type_ignores=[]),'frozen_labels','exec'),env)
samples = env['release_samples']

# Ten equally good successful hubs, all other searches failed.
fixture = np.full((1,512),999,dtype='i4')
fixture[0,:10] = 1
fp,fn = samples(fixture)
assert set(fp[0]) == set(fn[0]) == set(range(10))
records = []
for ds in json.loads((E96/'config.locked.json').read_text())['datasets']:
    inp = E96/'inputs'/ds
    hops = np.concatenate([np.fromfile(inp/'labels'/f'rows_{s}.hop.i32','i4').reshape(-1,512)
                           for s in range(0,11024,128)])
    pos,neg = samples(hops)
    good = [10<=len(b)<=500 for b in neg]
    overlaps = [len(set(a)&set(b)) if ok else 0
                for a,b,ok in zip(pos[:10000],neg[:10000],good[:10000])]
    pairs = np.fromfile(inp/'gate.triplets.i32','i4').reshape(-1,3)
    minimum = hops.min(axis=1)
    conflicting = hops[pairs[:,2],pairs[:,0]] == minimum[pairs[:,2]]
    records.append(dict(dataset=ds,training_queries_with_positive_negative_overlap=sum(n>0 for n in overlaps),
                        overlap_query_hub_pairs=sum(overlaps),
                        accepted_positive_query_hub_pairs=sum(len(a) for a,ok in zip(pos[:10000],good[:10000]) if ok),
                        triplets=len(pairs),triplets_with_negative_also_positive=int(conflicting.sum()),
                        conflicting_negative_fraction=float(conflicting.mean()),
                        identical_positive_negative_query_triplets=int((pairs[:,1]==pairs[:,2]).sum())))
result = dict(status='CONFIRMED_OVERLAPPING_POSITIVE_NEGATIVE_LABELS',datasets=records,
              synthetic_fixture=dict(hubs=512,successful_hubs=10,successful_hop=1,positive_hubs=fp[0],negative_hubs=fn[0]),
              proposed_minimal_repair='Remove positive hubs from each negative set before usability filtering and triplet pairing. Reuse compatible hop caches; regenerate triples and retrain only in a successor version.',
              new_training=0,new_ANN=0,new_graph_build=0,new_GT=0,new_QPS=0)
(OUT/'results/label_overlap_verified.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
