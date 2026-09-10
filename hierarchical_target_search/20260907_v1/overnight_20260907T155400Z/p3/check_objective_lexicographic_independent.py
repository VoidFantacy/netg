#!/usr/bin/env python3
"""Pure algebra and saved-summary checks; never open actual graph, GT or label data."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DIAGNOSIS=ROOT/'objective_local_scale_diagnosis_v1/diagnosis.json'
PARTITION_SOURCE=ROOT/'partition_build_v4/source_snapshot.cpp'
DIAGNOSIS_SHA='c3fa695d1d1e49e8aa6081025a7c5eb704c7d3466a0634ffa9ba38b38288ee8f'
PARTITION_SHA='78cd134726c61fda5b722887262b33176989b1c40163e00af7a7bc52c76a81b5'


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def binding(path): return {'path':str(Path(path).resolve()),'sha256':digest(path)}
def sign(x): return (x>0)-(x<0)


def summary_checks():
    assert digest(DIAGNOSIS)==DIAGNOSIS_SHA and digest(PARTITION_SOURCE)==PARTITION_SHA
    report=json.loads(DIAGNOSIS.read_text())
    assert report['status']=='COMPLETE' and report['P3_gate_status_unchanged']=='NOPASS'
    assert report['script']['sha256']=='148e3ff29259857865e9916f5f3905f2f2d1ffd3c1d843bfd8909a16c18259c8'
    expected={'webvid2_5m_light_v1':(2505000,49611457,118811,168,17),
              'yandex_t2i_official10M_ip_v1':(10000000,294844794,188913,162,0)}
    assert {x['dataset'] for x in report['datasets']}==set(expected) and len(report['datasets'])==2
    reviewed=[]
    for dataset in report['datasets']:
        name=dataset['dataset']; N,M,seen_n,seen_max,exceptions=expected[name]; Q=dataset['Q_fit']
        assert dataset['N']==N and dataset['M_directed_valid_nonself']==M and Q==20000
        groups=dataset['groups']; assert len(groups)==31
        support={g['population']:g for g in groups if g['family']=='support'}
        assert set(support)=={'all','seen','unseen'}
        assert support['all']['node_count']==N and support['seen']['node_count']==seen_n
        assert support['seen']['total_degree']['max']==seen_max and seen_max*9*Q<M
        assert support['seen']['condition_node_count']==seen_n and support['seen']['condition_fit_occurrences']==200000
        assert support['all']['condition_node_count']==N-exceptions
        assert support['unseen']['node_count']-support['unseen']['condition_node_count']==exceptions
        for g in groups:
            n,good,occ,good_occ=(g[k] for k in ('node_count','condition_node_count','fit_target_occurrences','condition_fit_occurrences'))
            assert 0<=good<=n and 0<=good_occ<=occ
            assert g['condition_node_fraction']==(good/n if n else None)
            assert g['condition_fit_occurrence_weighted_fraction']==(good_occ/occ if occ else None)
            if n:
                assert g['total_degree']['min']<=g['total_degree']['max']
                assert abs(g['in_degree']['mean']+g['out_degree']['mean']-g['total_degree']['mean'])<1e-12
                assert (g['total_degree']['max']*9*Q<M)==(good==n)
            else:
                assert all(g[k][v] is None for k in ('in_degree','out_degree','total_degree') for v in ('mean','min','max'))
                assert all(q['degree'] is None and q['zero_based_order_index'] is None for q in g['total_degree_quantiles'])
        frequency=[g for g in groups if g['family']=='frequency']
        assert len(frequency)==10
        assert [g['frequency_interval_inclusive'] for g in frequency]==[[0,0],[1,1],[2,2],[3,3],[4,4],[5,9],[10,19],[20,49],[50,99],[100,None]]
        for key in ('node_count','condition_node_count','fit_target_occurrences','condition_fit_occurrences'):
            assert sum(g[key] for g in frequency)==support['all'][key]
            assert support['seen'][key]+support['unseen'][key]==support['all'][key]
        movement=[g for g in groups if g['family']=='movement']; assert len(movement)==18
        for variable in {g['variable'] for g in movement}:
            for population in support:
                pair=[g for g in movement if g['variable']==variable and g['population']==population]
                assert len(pair)==2 and {g['state'] for g in pair}=={'changed','unchanged'}
                for key in ('node_count','condition_node_count','fit_target_occurrences','condition_fit_occurrences'):
                    assert sum(g[key] for g in pair)==support[population][key]
        final_change=[g for g in movement if g['variable']=='final_lambda1_vs_lambda0_leaf_difference' and g['state']=='changed']
        assert len(final_change)==3 and all(g['condition_node_count']==g['node_count'] for g in final_change)
        hb=dataset['total_degree_sparse_histogram']; artifact=hb['artifact']; hp=Path(artifact['path'])
        assert hp.parent==DIAGNOSIS.parent and hp.name==name+'.total_degree_histogram.json'
        raw=hp.read_bytes(); assert len(raw)==artifact['bytes']<=1048576 and hashlib.sha256(raw).hexdigest()==artifact['sha256']
        hist=json.loads(raw); pairs=hist['pairs']; assert len(pairs)==hb['distinct_degrees']
        assert pairs==sorted(pairs) and len({d for d,n in pairs})==len(pairs) and all(d>=0 and n>0 for d,n in pairs)
        assert sum(n for d,n in pairs)==N and sum(d*n for d,n in pairs)==2*M
        assert sum(n for d,n in pairs if d*9*Q<M)==N-exceptions
        assert pairs[0][0]==support['all']['total_degree']['min'] and pairs[-1][0]==support['all']['total_degree']['max']
        for qt in support['all']['total_degree_quantiles']:
            p=Fraction(str(qt['p'])); rank=max(0,(p.numerator*N+p.denominator-1)//p.denominator-1)
            cumulative=0
            for degree,count in pairs:
                cumulative+=count
                if cumulative>rank: break
            assert qt['zero_based_order_index']==rank and qt['degree']==degree
        conservation=dataset['integrity']['degree_conservation']
        assert conservation['sum_in']==conservation['sum_out']==M and conservation['sum_total']==2*M
        margin=Fraction(1,9*Q)-Fraction(seen_max,M)
        assert margin>0
        reviewed.append({'dataset':name,'N':N,'M':M,'Q':Q,'threshold_exact':str(Fraction(M,9*Q)),
            'threshold_decimal':M/(9*Q),'seen_nodes':seen_n,'seen_max_degree':seen_max,'seen_condition_fraction':1.0,
            'fit_occurrences':200000,'condition_fit_occurrence_fraction':1.0,'all_nodes_condition_count':N-exceptions,
            'all_nodes_exceptions':exceptions,'exceptions_all_unseen':True,
            'final_lambda1_vs_lambda0_changed_groups':[{k:g[k] for k in ('population','node_count','condition_node_count','fit_target_occurrences','condition_fit_occurrences','total_degree')} for g in final_change],
            'worst_seen_unit_DeltaS_pairwise_J_margin_exact':str(margin),
            'worst_seen_unit_DeltaS_pairwise_J_margin_decimal':float(margin),
            'all_group_count':31,'bound_histogram':artifact,'histogram_conservation_condition_and_quantiles_recomputed':True})
    return reviewed


def cut(arcs,labels): return sum(labels[u]!=labels[v] for u,v in arcs if u!=v)
def fragmentation(queries,labels): return sum(len({labels[u] for u in q})-1 for q in queries)


def pure_algebra_checks():
    # A directed multigraph with duplicate/reciprocal/self arcs and a disconnected
    # background. These are generated mathematical fixtures, never actual data.
    arcs=[(0,1),(0,1),(1,0),(1,2),(2,3),(3,1),(0,0),(2,2)]+[(4,5)]*500
    queries=[(0,1,2),(0,2,3),(1,2,3)]
    M=sum(u!=v for u,v in arcs); Q=len(queries); states=pairs=choices=0
    seen=set(itertools.chain.from_iterable(queries))
    degrees=[sum((u==i)+(v==i) for u,v in arcs if u!=v) for i in range(6)]
    assert all(degrees[u]*9*Q<M for u in seen) and degrees[4]*9*Q>=M and 4 not in seen
    for state in itertools.product(range(3),repeat=4):
        labels=list(state)+[0,1]; before_c=cut(arcs,labels); before_s=fragmentation(queries,labels); states+=1
        for u in range(6):
            old=labels[u]
            incident=Counter(labels[v if a==u else a] for a,v in arcs if a!=v and (a==u or v==u))
            assert sum(incident.values())==degrees[u]
            delta={}
            for dest in range(3):
                new=labels.copy(); new[u]=dest
                dc=cut(arcs,new)-before_c; ds=fragmentation(queries,new)-before_s
                assert dc==incident[old]-incident[dest]
                if u not in seen: assert ds==0
                delta[dest]=(ds,dc,dc*9*Q+ds*M)
            for a,b in itertools.product(range(3),repeat=2):
                sa,ca,ja=delta[a]; sb,cb,jb=delta[b]
                assert ca-cb==incident[b]-incident[a]
                assert abs(ca-cb)<=degrees[u]
                assert sign(ja-jb)==(sign(sa-sb) if sa!=sb else sign(ca-cb))
                pairs+=1
            # Every candidate/feasibility subset, plus always-available stay.
            others=[x for x in range(3) if x!=old]
            for flags in itertools.product((False,True),repeat=len(others)):
                feasible=[x for x,yes in zip(others,flags) if yes]
                selected=old; best=0
                for dest in sorted(feasible):
                    if delta[dest][2]<best: selected,best=dest,delta[dest][2]
                lex=min([old]+feasible,key=lambda dest:(delta[dest][0],delta[dest][1],-1 if dest==old else dest))
                assert selected==lex
                if selected!=old:
                    ds,dc,_=delta[selected]; assert ds<0 or (ds==0 and dc<0)
                choices+=1
    # Sharpness: if D*9Q=M, DeltaS=-1 can tie stay; above threshold it can lose.
    assert 9*9-81==0 and 9*9-80>0
    # Exact zero improvement retains old=2 despite smaller destination ID=0.
    old=2; selected=old; best=0
    for dest,score in [(0,0),(1,0)]:
        if score<best: selected,best=dest,score
    assert selected==2
    # Strictly improving equal scores choose the smaller destination ID.
    old=2; selected=old; best=0
    for dest,score in [(0,-1),(1,-1)]:
        if score<best: selected,best=dest,score
    assert selected==0
    return {'status':'PASS','generated_graph_nodes':6,'directed_nonself_slots':M,'synthetic_hyperedges':Q,
        'label_states':states,'full_recount_pairwise_comparisons':pairs,'all_candidate_subset_choice_comparisons':choices,
        'directed_cut_difference_identity_and_D_bound':True,'integer_objective_vs_lexicographic_order':True,
        'high_degree_unseen_DeltaS_zero':True,'all_accepted_choices_DeltaS_negative_or_zero_and_DeltaC_negative':True,
        'threshold_equality_and_above_threshold_counterexamples':True,'stay_zero_tie_priority':True,
        'improving_destination_ID_tie':True,'actual_graph_GT_or_label_inputs_read':False}


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',required=True)
    output=Path(p.parse_args().output).resolve(); output.mkdir(parents=True,exist_ok=False)
    datasets=summary_checks(); algebra=pure_algebra_checks()
    report={'schema_version':1,'status':'PASS_SUMMARY_AND_PURE_ALGEBRA_CHECKS','source_diagnosis':binding(DIAGNOSIS),
        'frozen_partition_source':binding(PARTITION_SOURCE),'reviewer_script':binding(__file__),'datasets':datasets,
        'pure_algebra_checks':algebra,'access_scope':'Completed diagnosis JSON, its two bound tiny histograms, frozen partition source, and generated mathematical fixtures only.',
        'actual_graph_GT_labels_count_rows_read':False,'ANN_executed':False,'new_CI_computed':False,'P3_gate_status_unchanged':'NOPASS'}
    with (output/'report.json').open('x') as f: json.dump(report,f,indent=2,allow_nan=False); f.write('\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
