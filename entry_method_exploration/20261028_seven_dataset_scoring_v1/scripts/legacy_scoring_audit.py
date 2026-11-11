from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];checks=[]
for ds in ['coco','deep10m_l2_v1']:
 for L in [100,200]:
  for m in ['REUSE-PQ']+(['REUSE-SQ'] if ds=='coco' else []):
   old=R.parent/('20261028_coco_fixed_candidate_scoring_v1' if ds=='coco' else '20261028_reuse_completion_routing_v1');om='REUSE-BLOCK' if m=='REUSE-PQ' else 'SQ8-96';new=R/f'storage/qualification/{ds}/k100/{m}_L{L}/raw';previous=old/f'results/{ds}/{om}_L{L}/raw'
   for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:
    b=(new/name).read_bytes();assert (previous/name).open('rb').read(len(b))==b,(ds,L,m,name)
   checks.append(dict(dataset=ds,K=100,L=L,method=m,queries=128,historical_packet_prefix_equal=True))
(R/'reviews/legacy_scoring_audit.json').write_text(json.dumps(dict(status='PASS_E191_LEGACY_SCORING_PARITY',checks=checks),indent=2)+'\n');print('PASS',len(checks),'legacy candidate packets')
