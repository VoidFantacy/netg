"""Cal-only selection among exactly three alpha profiles, including failed outcomes."""
import time
from pathlib import Path
import numpy as np
from common import RUN,DATASETS,NAMES,read,dump,identity,check_lock,frozen_check,update_state
from effect_stats import effect_stats


def load_stage(ds,stage):
    folder=RUN/'diagnostics'/ds/stage
    assert read(folder/'independent_verification.json')['status']=='PASS'
    n=read(folder/'config.json')['num_queries']
    h={name:np.column_stack([np.fromfile(folder/f'{name}_L{L}/hits.u8',dtype='u1') for L in [64,128]]).astype('int16')
       for name in ['fast20k','e24',*NAMES]}
    entries={}
    for name in h:
        e=np.fromfile(folder/f'{name}_L64/entry_ids.i32',dtype='<i4').reshape(n,3)
        assert np.array_equal(e,np.fromfile(folder/f'{name}_L128/entry_ids.i32',dtype='<i4').reshape(n,3))
        entries[name]=e
    return folder,h,entries


def candidates_for(ds,stage):
    folder,h,entries=load_stage(ds,stage);profiles=read(RUN/'models'/ds/'profiles.json')
    candidates=[]
    for name in NAMES:
        candidates.append({'name':name,'alpha':profiles[name]['alpha'],
            'pooled':effect_stats(h['fast20k'],h['e24'],h[name]),
            'per_L':{str(L):effect_stats(h['fast20k'][:,j],h['e24'][:,j],h[name][:,j]) for j,L in enumerate([64,128])},
            'entry_changes_vs_A0':int((entries[name]!=entries['fast20k']).any(axis=1).sum()),
            'entry_changes_vs_A1':int((entries[name]!=entries['e24']).any(axis=1).sum())})
    return folder,candidates


def select(candidates):
    feasible=[c for c in candidates if c['pooled']['target_met']]
    def key(c):
        s=c['pooled'];tail=(s['net_delta_hits'],-s['total_negative_events'],-s['total_negative_hits'],-c['entry_changes_vs_A0'],-c['alpha'])
        return tail if feasible else (s['S'],*tail)
    chosen=max(feasible or candidates,key=key)
    return chosen,'CAL_TARGET_MET' if feasible else 'CAL_TARGET_NOT_MET'


def selftest():
    def c(name,alpha,net,feasible=True,S=1,harm=2,loss=3,changes=5):
        return {'name':name,'alpha':alpha,'entry_changes_vs_A0':changes,
                'pooled':{'target_met':feasible,'S':S,'net_delta_hits':net,'total_negative_events':harm,'total_negative_hits':loss}}
    assert select([c('failed',.25,100,False),c('passed',.5,4)])[0]['name']=='passed'
    assert select([c('lowS',.25,100,False,.1),c('highS',.5,4,False,.8)])[0]['name']=='highS'
    assert select([c('large_alpha',.75,5),c('small_alpha',.25,5)])[0]['name']=='small_alpha'
    assert select([c('harmful',.25,5,harm=3),c('safer',.5,5,harm=2)])[0]['name']=='safer'
    return {'status':'PASS','feasibility_before_net_hits':True,'closest_S_before_net_when_failed':True,
            'negative_event_and_alpha_ties':True}


def main():
    lock=check_lock();frozen_check('cal')
    assert read(RUN/'reviews/cal_verification.json')['status']=='PASS'
    assert not (RUN/'models/frozen_before_audit.json').exists()
    assert not any(j['status']=='RUNNING' for j in read(RUN/'reviews/search_jobs.json'))
    dump(RUN/'reviews/selection_selftest.json',selftest())
    selections={};files=[]
    for ds in DATASETS:
        folder,candidates=candidates_for(ds,'cal');chosen,status=select(candidates)
        record={'status':status,'selected':chosen['name'],'alpha':chosen['alpha'],'selected_candidate':chosen,
                'candidates':candidates,'QPS_used_for_selection':False,'audit_or_validation_used_for_selection':False}
        path=RUN/'models'/ds/'selection.json';dump(path,record);files.append(path);selections[ds]=record
        files.extend([p for p in folder.rglob('*') if p.is_file()])
        print(ds,chosen['name'],status,chosen['pooled'],flush=True)
    dump(RUN/'models/selections.json',selections)
    files.extend([RUN/p for p in ['models/selections.json','models/frozen_before_cal.json','reviews/cal_verification.json',
        'reviews/selection_selftest.json','reviews/effect_accounting_selftest.json','src/select_alpha.py','src/effect_stats.py','src/verify_outputs.py']])
    files.extend([Path(item['path']) for item in read(RUN/'models/frozen_before_cal.json')['files']])
    unique={str(p):p for p in files}
    dump(RUN/'models/frozen_before_audit.json',{'status':'FROZEN_BEFORE_AUDIT_AND_VALIDATION','frozen_unix':time.time(),
        'protocol_sha256':lock['protocol_sha256'],'files':[identity(p) for p in unique.values()],
        'selected_alpha':{ds:selections[ds]['alpha'] for ds in DATASETS}})
    update_state(status='CAL_SELECTION_FROZEN_BEFORE_AUDIT')
    print('ALL_ALPHA_SELECTIONS_FROZEN',flush=True)


if __name__=='__main__':main()
