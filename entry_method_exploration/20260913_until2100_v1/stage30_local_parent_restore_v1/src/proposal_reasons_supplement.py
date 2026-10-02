from common import *
import csv,collections
threads();assert all(j['status']=='COMPLETE' for j in read(O/'logs/jobs.json'));rows=[]
for ds in DS:
 events=list(csv.DictReader((O/'inputs'/ds/'proposal_events.csv').open()));votes=collections.Counter();support=collections.defaultdict(set)
 for e in events:votes[int(e['hub'])]+=int(e['weight']);support[int(e['hub'])].add(int(e['fit_index']))
 chosen={x['hub'] for x in read(O/'inputs'/ds/'candidates.json')};eligible={x['hub'] for x in read(O/'inputs'/ds/'eligible_groups.json')};mapping=np.fromfile(read(O/'inputs'/ds/'routes.json')['method']['mapping'],np.int32)
 for h in sorted(set(map(int,mapping))):
  reason='SELECTED' if h in chosen else 'NO_TWO_CHILD_ACTION' if h not in eligible else 'NO_QUALIFYING_EVENT' if not support[h] else 'SUPPORT_BELOW_TWO' if len(support[h])<2 else 'RANK_BEYOND_TOP32'
  rows.append(dict(dataset=ds,hub=h,weighted_votes=votes[h],distinct_support=len(support[h]),reason=reason,identity_scope='post-query explicit reconstruction from frozen proposal inputs; no new selection'))
with (O/'results/proposal_reasons_postfreeze.csv').open('x',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
dump(O/'reviews/proposal_record_scope_correction.json',dict(status='EXPLICIT_REASON_TABLE_ADDED_AFTER_QUERIES',missing_at_freeze='Protocol asked explicit nonselection reasons; original full events, eligibility, candidates and deterministic rules were frozen but separate reason table was absent.',scope='New table reconstructs reasons solely from original frozen inputs; no candidate, model, response or quality rule changed. Original freeze remains valid for its listed inputs.',new_ANN=0,new_training=0))
print('E89_POSTFREEZE_REASONS',len(rows))
