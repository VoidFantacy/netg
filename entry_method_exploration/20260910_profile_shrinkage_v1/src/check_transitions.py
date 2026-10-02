"""When the three actual entries are unchanged, the original graph result must be identical."""
import argparse
import numpy as np
from common import RUN,DATASETS,read,dump,frozen_check
from verify_outputs import load_arrays


def main(stage):
    frozen_check('cal')
    all_results=[]
    for ds in DATASETS:
        folder=RUN/('results' if stage=='validation' else 'diagnostics')/ds
        if stage!='validation':folder/=stage
        r=read(folder/'results.json');assert read(folder/'independent_verification.json')['status']=='PASS'
        n=r['queries'];data={m['name']:load_arrays(folder,m['name'],n) for m in r['methods']}
        records=[]
        for m in r['methods']:
            if m['family'] not in ['alpha025','alpha050','alpha075','shrink']:continue
            base=data[f"fast20k_L{m['L']}"];new=data[f"e24_L{m['L']}"];a=data[m['name']]
            same0=np.all(a['entries']==base['entries'],axis=1);same1=np.all(a['entries']==new['entries'],axis=1)
            for mask,reference in [(same0,base),(same1,new)]:
                for key in ['ids','mask','hits','graph_ndc']:
                    assert np.array_equal(a[key][mask],reference[key][mask]),(ds,m['name'],key)
                assert np.array_equal(a['distances'][mask].view('<u4'),reference['distances'][mask].view('<u4'))
            groups={'same_both':same0&same1,'A0_only':same0&~same1,'A1_only':~same0&same1,'third_entry_set':~same0&~same1}
            group_results={}
            for name,mask in groups.items():
                da=a['hits'][mask]-base['hits'][mask];d1=new['hits'][mask]-base['hits'][mask]
                group_results[name]={'queries':int(mask.sum()),'delta_hits_vs_A0':int(da.sum()),
                    'delta_hits_vs_A1':int((da-d1).sum()),'improved_events_vs_A0':int((da>0).sum()),
                    'harmed_events_vs_A0':int((da<0).sum()),'positive_hits_vs_A0':int(np.maximum(da,0).sum()),
                    'negative_hits_vs_A0':int(np.maximum(-da,0).sum()),
                    'new_harm_events_on_A1_nonnegative':int(((d1>=0)&(da<0)).sum())}
            assert sum(v['queries'] for v in group_results.values())==n
            records.append({'method':m['name'],'family':m['family'],'L':m['L'],'groups':group_results,
                            'same_entries_graph_result_bits_and_NDC':'PASS'})
        all_results.append({'dataset':ds,'records':records})
    dump(RUN/'reviews'/f'{stage}_entry_transitions.json',{'status':'PASS','datasets':all_results,
        'extra_NSG_calls':0,'groups_are_descriptive_not_selection_features':True})
    print(stage.upper()+'_ENTRY_TRANSITIONS_PASS',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['cal','audit','validation']);main(ap.parse_args().stage)
