from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

if __name__ == '__main__':
    result = read(RUN/'analysis/results.json')
    audit = read(RUN/'reviews/independent_audit.json')
    assert audit['status'] == 'PASS'
    assert read(RUN/'reviews/asset_audit.json')['status'] == 'PASS'
    assert read(RUN/'reviews/label_return_audit.json')['status'] == 'PASS'
    cost = read(RUN/'reviews/training_complete.json')
    lock = read(RUN/'config.locked.json')
    inherited_labels = [read(OLD/'results'/ds/'labels/complete.json') for ds in lock['datasets']]
    names = lock['primary'] + lock['strong']
    lines = ['# E119: Response-Defined Entry Capability', '',
        f"Status: **{result['status']}**. Default unchanged. No new search, GT, graph, or QPS.", '',
        '## Main Results', '',
        'Historical-development, whole-query four-fold OOF. All values compare with the original GT10 policy.',
        'Recall is in percentage points. Cached time is main-search-only relative change, not full online cost.',
        'U = delta Recall - 0.1 * normalized search-time delta, averaged equally over K1/K100.', '',
        '| Dataset | Method | R1 pp | R100 pp | Cached time K1 / K100 % | U x100 [descriptive 95% CI] |',
        '|---|---|---:|---:|---:|---:|']
    for ds, methods in result['results'].items():
        for name in ['BestFixed','ClusterMean','E118Additive'] + names:
            r = methods[name]; a,b=r['K']['1'],r['K']['100']; ci=r['utility_CI95']
            lines.append(f"| {ds.split('_')[0]} | {name} | {a['recall_delta_pp']:+.4f} | {b['recall_delta_pp']:+.4f} | {a['cached_time_delta_pct']:+.3f} / {b['cached_time_delta_pct']:+.3f} | {100*r['mean_utility']:+.4f} [{100*ci[0]:+.4f}, {100*ci[1]:+.4f}] |")
    lines += ['', '## Decision and Interpretation', '',
        f"Frozen primary candidate: `{result['selected']}`. Strong-control passes: `{result['strong_only']}`.",
        f"H1 capability contrast: `{result['H1']}`. H2 mean contrast versus additive reference: `{result['H2_mean_contrast']}`.",
        'A representation contrast is separate from absolute net gain and from paid deployment performance.',
        'No model, threshold, lambda, seed, cluster count, depth, or candidate set was selected from outer failures.', '']
    if result['selected'] is None and not result['strong_only']:
        lines += ['The version stops at its query-out gate. The conditional native/fresh-query/performance stage is not triggered.',
            'This bounds the fixed support representation and fixed scorer runs, not all response-based routing or all neural models.', '']
    elif result['selected'] is None:
        lines += ['Only strong controls passed. This is evidence for a compression question, not a ready deployable method.', '']
    else:
        lines += ['Only the locked primary candidate proceeds. Current cached evidence is not yet an end-to-end improvement.', '']
    lines += ['## Fit Versus Transfer', '', '| Dataset | Method | Mean fit U x100 | Mean monitor U x100 | OOF U x100 |',
              '|---|---|---:|---:|---:|']
    fit_values = {}
    for ds in lock['datasets']:
        fit_values[ds] = {}
        for name in names:
            fitting, monitoring = [], []
            for fold in range(4):
                t=read(RUN/'models'/ds/f'fold_{fold}'/name/'training.json')
                if name in lock['primary']:
                    selected_epoch=max(t['history'],key=lambda z:z['monitor_utility'])
                    fitting.append(selected_epoch['fit_utility']);monitoring.append(selected_epoch['monitor_utility'])
                else:
                    fitting.append(t['fit_utility']);monitoring.append(t.get('monitor_utility', t.get('best_monitor_utility')))
            fit_values[ds][name]=dict(fit=float(np.mean(fitting)),monitor=float(np.mean(monitoring)))
            lines.append(f"| {ds.split('_')[0]} | {name} | {100*np.mean(fitting):+.4f} | {100*np.mean(monitoring):+.4f} | {100*result['results'][ds][name]['mean_utility']:+.4f} |")
    lines += ['', '## Rescue and Harm', '',
        '| Dataset | Method | K1 rescue / harm | K100 improved / worsened queries | K1 / K100 switches |',
        '|---|---|---:|---:|---:|']
    for ds in lock['datasets']:
        for name in names:
            r=result['results'][ds][name];a,b=r['K']['1'],r['K']['100']
            lines.append(f"| {ds.split('_')[0]} | {name} | {a['rescue_queries']} / {a['harmed_queries']} | {b['rescue_queries']} / {b['harmed_queries']} | {a['switches']} / {b['switches']} |")
    lines += ['', '## Theory and Literature', '',
        'The systematic chain is: oracle opportunity -> observable service descriptor -> query-out selection -> paid online cost.',
        '[Research and prior-work differences](research.md) links UniRoute, decision-focused ranking, DCNv2, TabM and RouteLLM.',
        '[Algorithm-selection prior work](prior_work_addendum.md) records ALORS and bilinear ranking, including their overlap with the proposed framing.',
        '[Theoretical conditions and counterexamples](theory_bounds.md) separates representation error, finite support, estimation and deployment overhead.',
        'The gated shared scorer is our bounded diagnostic parameterization, not a DCNv2 or UniRoute reproduction.',
        'No general OOD guarantee or paper novelty is claimed.', '',
        '## Validation and Limits', '',
        f"Independent numerical audit PASS; {audit['source_files_verified']} inherited source files remain unchanged.",
        'All original top1 labels and K100 masks, four query roles, representation isolation, objective gradient, scalar forward,',
        'model reloads, selected monitor checkpoints, every saved action and realized payoff were checked.',
        'Independent here means a separate numerical implementation, not a separate human or agent reviewer.',
        'The old GT10 profile bank and historical queries were previously exposed. OOF intervals are descriptive;',
        'training folds overlap and the 4 configurations were compared. They are not a substitute for a new blind test.',
        'Equal allocated parameters do not equalize the effective capacity of zeroed versus nonzero capability inputs.',
        'The additive reference uses inherited direction features; its comparison does not isolate the interaction layer causally.',
        'All strong controls share the fixed information set; they do not bound every possible cheap geometry or graph feature.',
        'Support+fit/monitor per fold are 1024/1792/256 queries; H paired labels do not multiply the independent sample count.',
        'Strong controls are fixed-budget configurations, not optimally tuned upper bounds on their model families.',
        'The negative-result interpretation must retain these limits and the full fit/monitor learning curves.', '',
        '## Cost and Data Boundary', '',
        f"Training controller: {cost['seconds']/60:.2f} minutes; peak RSS {cost['maxrss_gib']:.3f} GiB; offline numerical threads <=8.",
        'New search/GT/graph/K10/full-wall calls: zero. E118 response acquisition is inherited, not free from-scratch supervision.',
        f"Inherited label-only loops: {sum(v['seconds'] for v in inherited_labels)/3600:.3f} hours, {sum(v['search_calls'] for v in inherited_labels):,} search calls; graph/GT/profile acquisition has additional inherited cost.",
        'No fresh test query payload was materialized. [Source audit](reviews/source_audit.json) identifies candidate source windows',
        'but requires complete byte deduplication, identity checks, model freeze and power-based sample size before any final test.',
        'Original data, labels, graphs, code, models and production E99 remain unchanged.', '',
        '## Artifacts', '',
        '- [Frozen protocol](protocol.md), [lock](config.locked.json), [preflight](reviews/preflight.json).',
        '- [All metrics](analysis/metrics.csv), [full gate and contrasts](analysis/results.json), query-aligned NPZ in analysis/.',
        '- [Independent audit](reviews/independent_audit.json), [training cost](reviews/training_complete.json).',
        '- [Numerical determinism correction](reviews/preflight_correction.md), [metadata schema correction](reviews/source_schema_correction.md).',
        '- [Cost scope](reviews/cost_scope.md), [source audit](reviews/source_audit.json), [training log](training.log).']
    (RUN/'report.md').write_text('\n'.join(lines)+'\n')
    (RUN/'figures').mkdir(exist_ok=True)
    fig, axes = plt.subplots(1,2,figsize=(13,5),layout='constrained')
    colors = ['#2c7fb8','#31a354','#756bb1','#d95f0e','#c51b7d','#636363']
    for ax,ds in zip(axes,lock['datasets']):
        for i,name in enumerate(names):
            r=result['results'][ds][name];value=100*r['mean_utility'];ci=np.array(r['utility_CI95'])*100
            ax.errorbar(value,i,xerr=[[value-ci[0]],[ci[1]-value]],fmt='o',color=colors[i],capsize=3)
        ax.axvline(0,color='black',linewidth=.8);ax.set_yticks(range(len(names)),names)
        ax.set_title(ds.split('_')[0]);ax.set_xlabel('OOF utility delta x100 (not QPS)')
        ax.grid(axis='x',alpha=.2);ax.invert_yaxis()
    fig.suptitle('Cached query-out decisions; descriptive query-bootstrap intervals')
    fig.savefig(RUN/'figures/oof_utility.png',dpi=150);fig.savefig(RUN/'figures/oof_utility.pdf');plt.close(fig)
    dump(RUN/'analysis/fit_transfer.json',fit_values)
    dump(RUN/'reviews/report_identity.json',dict(files=[identity(RUN/'report.md'),identity(RUN/'figures/oof_utility.png')]))
    print('REPORT WRITTEN',flush=True)
