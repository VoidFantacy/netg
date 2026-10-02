from shared import *
import csv
threads(8)
rows=list(csv.DictReader((O/'results/actions.csv').open()))
records=[]
for ds in DS:
    a=[x for x in rows if x['dataset']==ds]
    positive=[x for x in a if int(x['aux_net_hits'])>0]
    legal=[x for x in positive if x['train_legal']=='True']
    assert not legal
    records.append(dict(dataset=ds,auxiliary_positive_actions=len(positive),auxiliary_positive_and_train_legal=len(legal),
        positive_auxiliary_but_train_hit_loss=sum(int(x['train_net_hits'])<0 for x in positive),
        positive_auxiliary_train_hits_unchanged_J_negative=sum(int(x['train_net_hits'])==0 and float(x['train_delta_J'])<0 for x in positive),
        auxiliary_positive_new_zero_failures=sum(int(x['aux_new_failures']) for x in positive)))
dump(O/'results/support_breakdown.json',dict(status='PASS_DESCRIPTIVE_RULE_INTERSECTION',datasets=records,
    rule_changed=False,extra_native_calls=0,interpretation='The locked conjunction has empty support; distinguish absent auxiliary response from train-J rejection. No claim of whole-space incompatibility.'))
print(records)
