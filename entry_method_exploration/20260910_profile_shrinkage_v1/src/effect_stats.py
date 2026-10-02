"""Generalized retention/loss accounting: a new profile can also create new harm."""
import numpy as np


def effect_stats(h0,h1,ha):
    h0=np.asarray(h0,dtype='int16');h1=np.asarray(h1,dtype='int16');ha=np.asarray(ha,dtype='int16')
    assert h0.shape==h1.shape==ha.shape and h0.size>0
    if h0.ndim==1:h0=h0[:,None];h1=h1[:,None];ha=ha[:,None]
    d1=h1-h0;da=ha-h0
    p1=np.maximum(d1,0);pa=np.maximum(da,0);n1=np.maximum(-d1,0);na=np.maximum(-da,0)
    good=d1>0;bad=d1<0
    pos_events=int(good.sum());neg_events=int(bad.sum());pos_hits=int(p1.sum());neg_hits=int(n1.sum())
    kept_events=int((good & (da>0)).sum());kept_hits=int(np.minimum(p1,pa).sum())
    harm_events=int((da<0).sum());harm_hits=int(na.sum())
    avoid_original_events=int((bad & (da>=0)).sum());avoid_original_hits=int(np.maximum(n1-na,0).sum())
    new_loss=int(na[d1>=0].sum());aggravated_loss=int(np.maximum(na-n1,0)[bad].sum())
    assert harm_hits==neg_hits-avoid_original_hits+new_loss+aggravated_loss
    positive_lost=pos_hits-kept_hits;new_or_amplified_gain=int(pa.sum())-kept_hits
    assert int(pa.sum())==pos_hits-positive_lost+new_or_amplified_gain
    div=lambda a,b:float(a/b) if b else None
    R=div(kept_events,pos_events);Rh=div(kept_hits,pos_hits)
    Aall=1-harm_events/neg_events if neg_events else None
    Ahall=1-harm_hits/neg_hits if neg_hits else None
    terms=[None if v is None else v/t for v,t in [(R,.75),(Rh,.75),(Aall,.25),(Ahall,.25)]]
    S=min(terms) if all(v is not None for v in terms) else 0.
    net=int(da.sum());required=max(0,int(d1.sum()))
    return {'queries':len(h0),'L_count':h0.shape[1],'query_L_events':h0.size,
        'R':R,'Rh':Rh,'A_all':Aall,'Ah_all':Ahall,'S':float(S),
        'target_met':bool(all(v is not None and v>=t for v,t in [(R,.75),(Rh,.75),(Aall,.25),(Ahall,.25)]) and net>=required),
        'original_positive_events':pos_events,'original_negative_events':neg_events,
        'original_positive_hits':pos_hits,'original_negative_hits':neg_hits,
        'original_positive_events_retained':kept_events,'original_positive_events_lost':pos_events-kept_events,
        'original_positive_hits_retained':kept_hits,'original_positive_hits_lost':positive_lost,
        'total_positive_events':int((da>0).sum()),'total_positive_hits':int(pa.sum()),
        'total_negative_events':harm_events,'total_negative_hits':harm_hits,
        'original_negative_events_avoided':avoid_original_events,
        'original_negative_event_avoidance':div(avoid_original_events,neg_events),
        'original_negative_hits_avoided':avoid_original_hits,
        'original_negative_hit_avoidance':div(avoid_original_hits,neg_hits),
        'new_negative_events_on_original_neutral':int(((d1==0)&(da<0)).sum()),
        'original_good_events_flipped_to_bad':int(((d1>0)&(da<0)).sum()),
        'original_bad_events_with_more_loss':int((bad & (da<d1)).sum()),
        'new_negative_hits_on_original_nonnegative':new_loss,
        'aggravated_loss_on_original_negative':aggravated_loss,
        'total_new_or_amplified_negative_hits':new_loss+aggravated_loss,
        'new_positive_events_on_original_neutral':int(((d1==0)&(da>0)).sum()),
        'original_bad_events_flipped_to_good':int(((d1<0)&(da>0)).sum()),
        'new_positive_hits_on_original_nonpositive':int(pa[d1<=0].sum()),
        'amplified_gain_on_original_positive':int(np.maximum(pa-p1,0)[good].sum()),
        'new_or_amplified_positive_hits':new_or_amplified_gain,
        'net_delta_hits':net,'always_A1_net_delta_hits':int(d1.sum()),'net_delta_required':required,
        'delta_recall_pp_vs_A0':float(da.mean()*10),'delta_recall_pp_vs_A1':float((ha-h1).mean()*10),
        'A0_recall':float(h0.mean()/10),'A1_recall':float(h1.mean()/10),'alpha_recall':float(ha.mean()/10),
        'zero_hits_A0':int((h0==0).sum()),'zero_hits_A1':int((h1==0).sum()),'zero_hits_alpha':int((ha==0).sum()),
        'zero_hit_rescues_vs_A0':int(((h0==0)&(ha>0)).sum()),'new_zero_hit_failures_vs_A0':int(((h0>0)&(ha==0)).sum()),
        'unique_query_diagnostics_not_selection':{
            'original_has_positive_at_any_L':int((d1>0).any(axis=1).sum()),
            'original_has_negative_at_any_L':int((d1<0).any(axis=1).sum()),
            'alpha_has_positive_at_any_L':int((da>0).any(axis=1).sum()),
            'alpha_has_negative_at_any_L':int((da<0).any(axis=1).sum()),
            'original_has_both_signs_across_L':int(((d1>0).any(axis=1)&(d1<0).any(axis=1)).sum()),
            'alpha_has_both_signs_across_L':int(((da>0).any(axis=1)&(da<0).any(axis=1)).sum()),
            'retained_original_positive_queries':int(((d1>0).any(axis=1)&(da>0).any(axis=1)).sum()),
            'original_negative_queries_fully_protected_across_L':int(((d1<0).any(axis=1)&~(da<0).any(axis=1)).sum()),
            'note':'positive and negative groups may overlap because one query can have opposite effects at different L'}}


def selftest():
    h0=np.full(5,5);h1=h0+np.asarray([2,-3,0,1,-1]);ha=h0+np.asarray([1,0,-2,1,-2])
    s=effect_stats(h0,h1,ha)
    assert s['R']==1 and s['Rh']==2/3 and s['original_negative_event_avoidance']==.5
    assert s['A_all']==0 and s['Ah_all']==0 and s['original_negative_hits_avoided']==3
    assert s['new_negative_hits_on_original_nonnegative']==2 and s['aggravated_loss_on_original_negative']==1
    assert not s['target_met']
    old=effect_stats(h0,h1,h0);new=effect_stats(h0,h1,h1)
    assert old['R']==0 and old['A_all']==1 and not old['target_met']
    assert new['R']==1 and new['A_all']==0 and not new['target_met']
    choose=np.asarray([1,0,1,1,0],dtype=bool)
    selected=effect_stats(h0,h1,np.where(choose,h1,h0))
    assert selected['R']==selected['Rh']==selected['A_all']==selected['Ah_all']==1 and selected['target_met']
    return {'status':'PASS','new_harm_cannot_hide_behind_original_harm_avoidance':True,
            'loss_and_gain_accounting_identities':True,'endpoints_not_success_by_default':True,
            'reduces_to_binary_gate_definition_when_choices_are_A0_A1':True}
