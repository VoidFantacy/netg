"""Additional cross-window output and report-link checks, outside all timing."""
import csv, hashlib, json, re, time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def main():
    t=time.perf_counter();matched=0
    for ds in json.loads((R/'dense_complete.json').read_text())['datasets']:
        primary=json.loads((R/f'storage/results/{ds}/complete.json').read_text())['results']
        lookup={(x['K'],x['method'],x['L']):Path(x['result_dir']) for x in primary}
        for x in json.loads((R/f'storage/dense_controls/{ds}/complete.json').read_text())['results']:
            key=x['K'],x['method'],x['L']
            if key not in lookup:continue
            for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:
                assert sha(Path(x['result_dir'])/'raw'/name)==sha(lookup[key]/'raw'/name),(ds,key,name)
            matched+=1
    broken=[];links=0
    for doc in [R/'report_zh.md',R.parents[1]/'summary.md',R.parents[1]/'s-target.md',
                R.parents[1]/'s-experiment.md',R.parents[1]/'LOCAL_CODEX_START.md']:
        for target in re.findall(r'!?\[[^\]]*\]\(([^\s)]+)\)',doc.read_text()):
            if '://' in target or target.startswith('#'):continue
            target=target.split('#',1)[0]
            if not target:continue
            links+=1
            if not (doc.parent/target).exists():broken.append((str(doc),target))
    assert not broken,broken
    v=dict(status='PASS_E191_CROSS_WINDOW_AND_LINK_CHECKS',
           overlapping_primary_dense_packets_equal=matched,local_links_checked=links,
           seconds=time.perf_counter()-t,scope='same parameters have identical actual outputs across timing windows')
    (R/'reviews/preseal_checks.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
if __name__=='__main__':main()
