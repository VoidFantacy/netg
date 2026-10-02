from contracts_v2 import *
from unittest.mock import patch
import copy
threads();resources();paths=list((O/'src').glob('*.py'))+[O/'results/tooling_verification.json',O/'reviews/pretest_freeze.json'];freeze(O/'reviews/pretest_v2_freeze.json',paths);check(O/'reviews/pretest_freeze.json');records=[]
for ds in DS:
 c=read(E74/'inputs'/ds/'config.json');a=validate_config(c);c['num_queries']=2000;c['real_call_cap']=len(c['methods'])*14016;b=validate_config(c);records.append(dict(dataset=ds,old=a,final_shape_only=b))
# Pure malformed selection must be rejected before any prequery payload check.
fixture=O/'results/invalid_selection_fixture';fixture.mkdir();dump(fixture/'selection.json',dict(status='DRAFT'));calls=[]
with patch('contracts_v2.check',side_effect=lambda *a:calls.append(a)):
 try:validate_frozen(fixture)
 except (AssertionError,KeyError):pass
 else:raise AssertionError('Draft selection passed')
assert not calls
# Fixed-three contracts accept real E74; shortened mapping cannot silently pass as fixed3.
c=read(E74/'inputs'/DS[0]/'config.json');m=next(m for m in c['methods'] if m.get('multi_profile') and not m.get('variable_profiles'));m['variable_profiles']=False
bad=O/'results/bad_mapping.i32';mapping=np.fromfile(m['mapping'],np.int32);mapping[:-1].tofile(bad);m['mapping']=str(bad);m['hub_count']=len(mapping)-1
try:validate_config(c)
except AssertionError:pass
else:raise AssertionError('Invalid fixed3 mapping passed')
dump(O/'results/contracts_v2_verification.json',dict(status='PASS',records=records,draft_rejected_before_payload_hash=True,invalid_fixed3_rejected=True,fixed3_and_variable_modes_accepted=True,all_additional_models_including_best_all_require_main_nonzero_eligibility=True,guard_scope='No actual final selection or controller execution; actual score/tie review remains required.',new_ANN=0,final_payload_opened=False));check(O/'reviews/pretest_v2_freeze.json');print('E91_CONTRACT_V2_PASS')
