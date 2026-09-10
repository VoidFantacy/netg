#!/usr/bin/env python3
"""Independently reconcile completed summary/histograms, without raw data reads."""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

EXPECTED_SHA='c3fa695d1d1e49e8aa6081025a7c5eb704c7d3466a0634ffa9ba38b38288ee8f'
EXPECTED_SOURCE='148e3ff29259857865e9916f5f3905f2f2d1ffd3c1d843bfd8909a16c18259c8'
LEVELS=(0,.25,.5,.75,.9,.95,.99,1)
FREQUENCIES=((0,0),(1,1),(2,2),(3,3),(4,4),(5,9),(10,19),(20,49),(50,99),(100,None))
VARIABLES=('lambda0_final_leaf_changed_from_initial','lambda1_final_leaf_changed_from_initial','final_lambda1_vs_lambda0_leaf_difference')
ADDITIVE=('node_count','fit_target_occurrences','condition_node_count','condition_fit_occurrences')


def require(ok,message):
    if not ok: raise ValueError(message)


def close(a,b,message):
    require(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9),message)


def binding(path):
    data=Path(path).read_bytes()
    return {'path':str(Path(path).resolve()),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)},data


def check_group(g):
    for field in ADDITIVE:
        require(type(g[field]) is int and g[field]>=0,'Negative/noninteger group count')
    n,f,good,wgood=(g[x] for x in ADDITIVE)
    require(good<=n and wgood<=f,'Condition counts exceed denominators')
    for field,numerator,denominator in (('condition_node_fraction',good,n),('condition_fit_occurrence_weighted_fraction',wgood,f)):
        if denominator: close(g[field],numerator/denominator,'Group fraction/denominator mismatch')
        else: require(g[field] is None,'Zero denominator must be null')
    for field in ('in_degree','out_degree','total_degree'):
        value=g[field]
        if n:
            require(type(value['min']) is int and type(value['max']) is int and 0<=value['min']<=value['mean']<=value['max'],
                    'Degree min/mean/max ordering')
        else:
            require(all(value[x] is None for x in ('min','mean','max')),'Empty degree statistics must be null')
    if n:
        close(g['in_degree']['mean']+g['out_degree']['mean'],g['total_degree']['mean'],'Mean total degree addition')
        require(g['out_degree']['max']<=64 and g['total_degree']['max']<=g['in_degree']['max']+g['out_degree']['max'],
                'Degree bound mismatch')
    quantiles=g['total_degree_quantiles']
    require([x['p'] for x in quantiles]==list(LEVELS),'Fixed quantile coverage')
    prior=-1
    for row,p in zip(quantiles,LEVELS):
        if not n:
            require(row['degree'] is None and row['zero_based_order_index'] is None,'Empty quantile must be null')
        else:
            frac=Fraction(str(p)); rank=max(0,(frac.numerator*n+frac.denominator-1)//frac.denominator-1)
            require(row['zero_based_order_index']==rank and g['total_degree']['min']<=row['degree']<=g['total_degree']['max'] and row['degree']>=prior,
                    'Empirical quantile rank/order/bounds mismatch')
            prior=row['degree']
    if n:
        require(quantiles[0]['degree']==g['total_degree']['min'] and quantiles[-1]['degree']==g['total_degree']['max'],
                'Quantile endpoint mismatch')


def partition_sum(children,parent):
    for field in ADDITIVE:
        require(sum(x[field] for x in children)==parent[field],'Group partition count conservation: '+field)
    for degree in ('in_degree','out_degree','total_degree'):
        if parent['node_count']:
            close(sum(x['node_count']*(x[degree]['mean'] or 0) for x in children)/parent['node_count'],parent[degree]['mean'],
                  'Group partition mean conservation')
            nonempty=[x for x in children if x['node_count']]
            require(min(x[degree]['min'] for x in nonempty)==parent[degree]['min'] and
                    max(x[degree]['max'] for x in nonempty)==parent[degree]['max'],'Group partition min/max conservation')


def check_dataset(ds,source_directory):
    require(ds['status']=='COMPLETE' and ds['P3_gate_status_unchanged']=='NOPASS','Incomplete dataset or changed gate')
    n,M,q=ds['N'],ds['M_directed_valid_nonself'],ds['Q_fit']
    groups=ds['groups']; require(len(groups)==31,'Expected all 31 groups')
    for row in groups: check_group(row)
    support={x['population']:x for x in groups if x['family']=='support'}
    frequency={tuple(x['frequency_interval_inclusive']):x for x in groups if x['family']=='frequency'}
    movement={(x['variable'],x['state'],x['population']):x for x in groups if x['family']=='movement'}
    require(set(support)=={'all','seen','unseen'} and len(support)==3 and tuple(frequency)==FREQUENCIES and len(frequency)==10 and
            set(movement)=={(v,s,p) for v in VARIABLES for s in ('changed','unchanged') for p in support} and len(movement)==18,
            'Missing, duplicate or extra fixed group')
    require(support['all']['node_count']==n and support['all']['fit_target_occurrences']==10*q,'N/Q support counts mismatch')
    require(support['unseen']['fit_target_occurrences']==0 and support['seen']['fit_target_occurrences']==10*q,'Seen occurrence conservation')
    partition_sum([support['seen'],support['unseen']],support['all'])
    partition_sum(list(frequency.values()),support['all'])
    require(all(frequency[(0,0)][k]==support['unseen'][k] for k in ADDITIVE),'f0 bin differs from unseen')
    for (lo,hi),group in frequency.items():
        require(group['node_count']*lo<=group['fit_target_occurrences'] and
                (hi is None or group['fit_target_occurrences']<=group['node_count']*hi),'Frequency interval occurrence bounds')
    for variable in VARIABLES:
        for population in support:
            partition_sum([movement[(variable,state,population)] for state in ('changed','unchanged')],support[population])
            stored=ds['integrity']['support_and_movement']['movement_groups'][variable][population]
            require(stored['changed']==movement[(variable,'changed',population)]['node_count'] and
                    stored['unchanged']==movement[(variable,'unchanged',population)]['node_count'] and
                    stored['denominator']==support[population]['node_count'] and stored['matches_completed_target_diagnosis'] is True,
                    'Movement stored integrity counts differ from groups')
        for state in ('changed','unchanged'):
            partition_sum([movement[(variable,state,p)] for p in ('seen','unseen')],movement[(variable,state,'all')])
    counts=ds['integrity']['P0_slot_counts']; conservation=ds['integrity']['degree_conservation']
    require(counts['invalid_edges']==0 and counts['valid_nonself_edges']==M and counts['valid_edges']==M+counts['self_edges'] and
            counts['padding']+counts['valid_edges']==64*n and conservation['sum_in']==conservation['sum_out']==M and
            conservation['sum_total']==2*M and conservation['numeric_bytes_read']==n*64*4 and conservation['read_past_adjacency'] is False,
            'Saved P0 slot/degree/read-bound conservation mismatch')
    close(support['all']['in_degree']['mean'],M/n,'Mean in conservation')
    close(support['all']['out_degree']['mean'],M/n,'Mean out conservation')
    hbinding=ds['total_degree_sparse_histogram']; require(hbinding['included'] is True,'Tiny bound histogram required')
    hp=Path(hbinding['artifact']['path']).resolve()
    require(hp.parent==source_directory,'Histogram escapes completed diagnostic directory')
    actual,raw=binding(hp)
    require(actual==hbinding['artifact'] and len(raw)<=hbinding['limit_bytes']==1048576,'Histogram full-byte/hash mismatch')
    histogram=json.loads(raw)
    require(histogram['included'] is True and histogram['distinct_degrees']==hbinding['distinct_degrees']==len(histogram['pairs']),
            'Histogram metadata mismatch')
    pairs=histogram['pairs']; require(all(type(a) is int and type(b) is int and a>=0 and b>0 for a,b in pairs) and
                                     all(a[0]<b[0] for a,b in zip(pairs,pairs[1:])),'Histogram degree/count order invalid')
    require(sum(b for a,b in pairs)==n and sum(a*b for a,b in pairs)==2*M,'Independent histogram N/2M conservation mismatch')
    good=sum(count for degree,count in pairs if degree*(9*q)<M)
    require(good==support['all']['condition_node_count'],'Histogram sufficient-condition coverage mismatch')
    require(pairs[0][0]==support['all']['total_degree']['min'] and pairs[-1][0]==support['all']['total_degree']['max'],
            'Histogram max/min differ from all-base summary')
    for row in support['all']['total_degree_quantiles']:
        target=row['zero_based_order_index']; cumulative=0; expected=None
        for value,count in pairs:
            cumulative+=count
            if cumulative>target: expected=value; break
        require(row['degree']==expected,'Independent histogram empirical quantile mismatch')
    cutoff=(M+9*q-1)//(9*q)
    require(ds['integrity']['support_and_movement']['first_integer_degree_not_satisfying']==cutoff,'Strict integer cutoff mismatch')
    for g in groups:
        if g['node_count'] and g['total_degree']['max']*(9*q)<M:
            require(g['condition_node_count']==g['node_count'] and g['condition_fit_occurrences']==g['fit_target_occurrences'],
                    'Group maximum proves full sufficient-condition coverage but stored count differs')
    seen=support['seen']; changed=movement[(VARIABLES[-1],'changed','all')]
    changed_seen=movement[(VARIABLES[-1],'changed','seen')]
    return {'dataset':ds['dataset'],'validation':'PASS_SUMMARY_AND_HISTOGRAM_CONSISTENCY','groups_checked':31,
            'M':M,'Q':q,'strict_threshold_fraction':str(Fraction(M,9*q)),'strict_threshold':M/(9*q),'first_failing_integer_degree':cutoff,
            'all_nodes':n,'all_satisfying':good,'all_not_satisfying':n-good,'all_max_total_degree':pairs[-1][0],
            'fit_seen_unique_nodes':seen['node_count'],'fit_seen_satisfying':seen['condition_node_count'],
            'fit_seen_fraction':seen['condition_node_fraction'],'fit_seen_max_total_degree':seen['total_degree']['max'],
            'fit_target_occurrences':seen['fit_target_occurrences'],'fit_occurrence_weighted_satisfying_fraction':seen['condition_fit_occurrence_weighted_fraction'],
            'final_lambda1_vs_lambda0_changed_all':changed['node_count'],'changed_all_satisfying':changed['condition_node_count'],
            'changed_all_max_total_degree':changed['total_degree']['max'],
            'changed_seen_nodes':changed_seen['node_count'],'changed_seen_satisfying':changed_seen['condition_node_count'],
            'histogram':actual,'group_count_fraction_and_partition_checks':True,'all_base_histogram_and_quantiles_reconciled':True,
            'subgroup_quantile_scope':'Ranks/order/bounds and partition aggregate consistency checked; subgroup values cannot be independently recomputed from an all-base histogram.',
            'raw_degree_or_incidence_or_label_reconstruction_performed':False}


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input',required=True); p.add_argument('--output-prefix',required=True)
    args=p.parse_args(); ip=Path(args.input).resolve(); src,raw=binding(ip)
    require(src['sha256']==EXPECTED_SHA,'Completed local-scale diagnosis SHA differs')
    report=json.loads(raw)
    require(report['status']=='COMPLETE' and report['stage']=='P3_POST_NOGO_OBJECTIVE_LOCAL_SCALE' and
            report['script']['sha256']==EXPECTED_SOURCE and report['P3_gate_status_unchanged']=='NOPASS' and
            report['new_CI_computed'] is False,'Completed source/status/semantics mismatch')
    require([x['dataset'] for x in report['datasets']]==['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'],'Dataset coverage differs')
    results=[check_dataset(ds,ip.parent) for ds in report['datasets']]
    require(all(x['fit_seen_fraction']==1 and x['fit_occurrence_weighted_satisfying_fraction']==1 and
                x['changed_all_satisfying']==x['final_lambda1_vs_lambda0_changed_all'] for x in results),
            'Expected completed descriptive conclusions did not reproduce')
    interpretation={'status':'PASS_DESCRIPTIVE_SUMMARY_REVIEW','source':src,'datasets':results,'groups_checked_total':62,
        'scope':'Only completed diagnostic summary and its two tiny checksum-bound histogram files were read.',
        'confirmed':'The measured strict sufficient degree condition covers every unique fit-seen target and every fit target occurrence on both datasets; it also covers every final lambda1-vs-lambda0 changed node.',
        'conditional_meaning':'For a node satisfying this condition, a feasible candidate with integer DeltaS<=-1 strictly lowers the frozen lambda1 objective regardless of cut increment. The audit measures the condition coverage only.',
        'limits':['No feasible GT-improving candidate existence, actual selection, accepted-move delta or temporal trajectory is reconstructed.',
                  'Summary reconciliation inherits raw-degree/GT/label integrity from the completed bound diagnostic; it does not independently rerun those reads.',
                  'This establishes the scope of the sufficient local-scale condition; it does not identify a cause of failed retrieval transfer.',
                  'No candidate-ranking theorem, parameter tuning, new representation, new model or gate reopening is asserted.'],
        'P3_gate_status_unchanged':'NOPASS','new_CI_or_search_or_model':False,'command':sys.argv}
    prefix=Path(args.output_prefix).resolve(); prefix.parent.mkdir(parents=True,exist_ok=True)
    with Path(str(prefix)+'.json').open('x') as f: json.dump(interpretation,f,indent=2,allow_nan=False); f.write('\n')
    lines=['# 局部目标量级：已完成摘要复核','',
           '两组数据的全部 fit 已见目标，都满足预注册的严格充分条件 `D(u) × 9Q < M`。按 fit 目标出现次数加权，覆盖率也都是 100%。这项结论来自已完成诊断；本次仅复核摘要和两个小型度直方图。','',
           '| 数据 | 已见目标数 / 满足条件 | 已见目标最大 D | 严格阈值 M/(9Q) | 全库未满足数 | λ1/λ0 最终标签不同且满足条件 |',
           '| --- | --- | --- | --- | --- | --- |']
    for x in results:
        name='WebVid' if x['dataset'].startswith('webvid') else 'Yandex'
        lines.append(f"| {name} | {x['fit_seen_unique_nodes']} / {x['fit_seen_satisfying']} | {x['fit_seen_max_total_degree']} | {x['strict_threshold']:.6f} | {x['all_not_satisfying']} / {x['all_nodes']} | {x['changed_all_satisfying']} / {x['final_lambda1_vs_lambda0_changed_all']} |")
    lines+=['','含义限于已有充分条件：对满足条件的节点，如果存在可行候选且其整数 `ΔS ≤ −1`，该候选会降低固定 λ=1 目标，即使图割项增加。此处没有证明这样的候选存在、被选中，或解释了检索迁移失败；也没有重建实际移动的 ΔC/ΔS。','',
            '一致性复核通过：两组各 31 个固定分组齐全，支持/频次/标签变化分组的节点数、fit 次数及满足条件计数守恒；空加权分母为 null；直方图校验和、完整字节上限、总节点数、总度 2M、最大度、全库条件覆盖和固定经验分位点一致。子组分位点只复核秩、单调性、范围和汇总一致性，没有子组原始数据可独立重算。','',
            f"来源 SHA256：`{src['sha256']}`。P3 仍为 NOPASS；不新增置信区间、参数选择、模型或门控结论。",'']
    with Path(str(prefix)+'.md').open('x') as f: f.write('\n'.join(lines))
    print(json.dumps({'status':interpretation['status'],'groups_checked':62,'json':str(prefix)+'.json','markdown':str(prefix)+'.md'},indent=2))


if __name__=='__main__': main()
