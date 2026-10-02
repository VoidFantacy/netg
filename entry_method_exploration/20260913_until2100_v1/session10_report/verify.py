from pathlib import Path
import sys,csv
S=Path(__file__).resolve().parent;C=S.parent;sys.path.insert(0,str(C/'stage32_final_tooling_v1/src'))
from common import *
threads();check(S/'input_freeze_v2.json');rows=list(csv.DictReader((S/'failure_queries.csv').open()));assert len(rows)==428 and sum(r['changed_zero_status']=='True' for r in rows)==194
for r in rows:
 gt=set(map(int,r['GT10'].split()));assert len(gt)==10
 for name in ['P','compact','E84','E89','E89_random','E90','E90_random']:
  ids=list(map(int,r[name+'_returned'].split()));assert len(ids)==len(set(ids))==10 and len(set(ids)&gt)==int(r[name+'_hits']);assert len(set(map(int,r[name+'_entries'].split())))==3
 assert any(int(r[n+'_hits'])==0 for n in ['P','compact','E84','E89','E89_random','E90','E90_random'])
 if r['dataset']==DS[1]:assert r['E90_hits']==r['compact_hits'] and r['E90_returned']==r['compact_returned'] and r['E90_entries']==r['compact_entries'] and r['E90_random_returned']==r['compact_returned']
dump(S/'verification.json',dict(status='PASS',failure_queries=428,changed_zero_queries=194,complete_cells=2996,independent_return_set_cells=2996,Y_zero_alias_rechecked=True,all_raw_source_identities_unchanged=True,new_ANN=0,final_payload_opened=False));print('SESSION10_REPORT_VERIFIED')
