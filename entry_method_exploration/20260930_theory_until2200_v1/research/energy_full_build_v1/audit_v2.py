import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
os.sched_setaffinity(0,range(8))
import hashlib,importlib.util,json,time
from pathlib import Path
import numpy as np
from graph_decode import decode_graph
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text());REF=json.loads((R/'reviews/validation_references.json').read_text())
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    start=time.perf_counter();run=json.loads((R/'reviews/run_complete.json').read_text());assert run['status']=='BUILT_PENDING_IDENTITY_AUDIT'
    # Sealed pre-build simulation code is an independent artifact reference, never imported by the actual builder.
    source=R.parent/'energy_temperature_clean_v1/common.py';spec=importlib.util.spec_from_file_location('sealed_simulation',source);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    frozen={str(source):ident(source),str(Path(__file__)):ident(__file__)};records={};totalgt=teacher_calls=ann_calls=manual_predictions=0;max_correction_error=0.
    tail=json.loads((R/'reviews/GT_tail_float64_audit.json').read_text());assert tail['status']=='PASS_REPORTED_SHORT_TAIL_SCORE_ROUNDING_ONLY' and tail['independent_fullbase_float64_GT_checks']==4
    diagnostic=json.loads((R/'reviews/GT_distance_shape_diagnostic_v1.json').read_text())
    frozen[str(R/'reviews/GT_tail_float64_audit.json')]=ident(R/'reviews/GT_tail_float64_audit.json')
    def distance_check(ds,name,rows,actual,truth):
        different=actual!=truth;changed=rows[np.any(different,axis=1)]
        expected=diagnostic['datasets'][ds][name]
        assert changed.tolist()==expected['rows_differing'] and int(different.sum())==expected['different_distance_bits']
        assert np.array_equal(actual[rows<19968],truth[rows<19968]) and set(changed)<=set(tail['datasets'][ds]['affected_rows'])
        return int(different.sum())
    for ds,c in C['datasets'].items():
        p=Path(c['output']);r=REF[ds];d=c['dimension'];prior=Path(r['demand_build']);full=Path(r['full_default']);n=c['fit_n']
        for key in ['fit_gt','approx_ids','approx_distances','simulation_npz','simulation_json','default_cost_summary']:frozen[r[key]]=ident(r[key])
        for name in ['ids.i32','qgt_demand.rows.i32','qgt_demand.ids.i64','qgt_demand.dist.f32','qgt_trace.json','qgt_generation.json']:
            assert (p/name).read_bytes()==(prior/name).read_bytes(),(ds,name)
        a=np.load(p/'cluster_plan.npz');b=np.load(prior/'cluster_plan.npz')
        for key in ['assignment','centroids','first_representatives']:assert np.array_equal(a[key],b[key])
        for name,key in [('ids.i32','approx_ids'),('distances.f32','approx_distances')]:assert (p/'labels'/name).read_bytes()==Path(r[key]).read_bytes(),(ds,key)
        gt=np.fromfile(r['fit_gt'],'<i8').reshape(n,100);assert np.array_equal(gt,np.fromfile(full/'fit20000.ids.i64','<i8').reshape(n,100))
        gdist=np.fromfile(full/'fit20000.dist.f32','<u4').reshape(n,100);pilot=np.fromfile(p/'pilot_rows.i32','<i4')
        assert np.array_equal(pilot,np.random.default_rng(c['pilot_seed']).permutation(n)[:1024])
        assert np.array_equal(np.fromfile(p/'pilot1024.ids.i64','<i8').reshape(1024,100),gt[pilot])
        pilot_distance=np.fromfile(p/'pilot1024.dist.f32','<u4').reshape(1024,100)
        pilot_differences=distance_check(ds,'pilot',pilot,pilot_distance,gdist[pilot])
        assert np.array_equal(pilot_distance,np.fromfile(prior/'selected2048.dist.f32','<u4').reshape(2048,100)[:1024]),'same-shape old pilot distance bytes'
        simulation=np.load(r['simulation_npz']);meta=json.loads(Path(r['simulation_json']).read_text());x=old.cheap_inputs(ds)
        assert np.array_equal(pilot,simulation['pilot_rows'][0]);fit=np.fromfile(c['fit_queries'],'<f4').reshape(n,d)
        exact=json.loads((p/'exact_complete.json').read_text());teacher=json.loads((p/'labels/complete.json').read_text())
        assert exact['new_GT']==c['H']+1024 and exact['faiss_threads']==8 and exact['affinity']==list(range(8))
        assert teacher['n']==20000 and teacher['new_NSG_calls']==20032 and teacher['threads']==1 and teacher['GT10_files_read']==teacher['GT10_route_calls']==0
        assert run['jobs'][ds+'_teacher']['single_thread_samples']>0 and run['jobs'][ds+'_teacher']['max_threads']==1
        totalgt+=exact['new_GT'];teacher_calls+=teacher['new_NSG_calls'];models={}
        for mi,method in enumerate([C['primary'],C['control']]):
            out=p/method;selected=np.fromfile(out/'selected_rows.i32','<i4');added=np.fromfile(out/'added_rows.i32','<i4')
            assert np.array_equal(selected,simulation['selected'][0,mi+1]) and np.array_equal(selected,np.r_[pilot,added]) and len(np.unique(selected))==2048
            assert np.array_equal(np.fromfile(out/'additional1024.ids.i64','<i8').reshape(1024,100),gt[added])
            additional_differences=distance_check(ds,method,added,np.fromfile(out/'additional1024.dist.f32','<u4').reshape(1024,100),gdist[added])
            selection=json.loads((out/'selection.json').read_text());data=np.load(out/'selection.npz');tree=selection['tree']
            assert selection['temperature']==meta['temperature']==x['temp'] and tree==meta['trees'][0][mi]
            for key,refarray in [('features',simulation['features']),('pilot_energy',simulation['pilot_energy'][0]),('predictions',simulation['predictions'][0,mi]),('shuffle',simulation['shuffles'][0]),('proxy_gaps',simulation['proxy_gaps'])]:
                assert np.array_equal(data[key],refarray),(ds,method,key)
            xf=data['features'].astype('f4');manual=[]
            for row in xf:
                node=0
                while tree['children_left'][node]>=0:node=tree['children_left'][node] if row[tree['feature'][node]]<=tree['threshold'][node] else tree['children_right'][node]
                manual.append(tree['values'][node])
            np.testing.assert_array_equal(manual,data['predictions']);manual_predictions+=n
            v=old.mixed_resultant(x,gt,selected);w=old.unit(v).astype('f4')
            assert v.tobytes()==(out/'v.f64').read_bytes() and w.tobytes()==(out/'W.f32').read_bytes(),(ds,method,'W/V bits')
            # Independent additive correction identity at 16 fixed hubs; uses explicit selected-query sums, no 20K aggregation.
            actual_exact=old.assignment(x['base'],gt[selected],x['h'],x['temp']);delta=actual_exact-x['b'][selected]
            for h in np.linspace(0,len(x['h'])-1,16,dtype=int):
                calc=x['vp'][h]+np.sum(delta[:,h,None]*x['q'][selected],axis=0)
                err=float(np.max(np.abs(calc-v[h])));max_correction_error=max(max_correction_error,err);np.testing.assert_allclose(calc,v[h],rtol=1e-12,atol=1e-12)
            decoded=decode_graph(out/'router.hnsw');offset,num,size,labeloff,dataoff,maxlev,enter,maxM,maxM0,M,mult,efc,nodes=decoded
            ids=np.fromfile(p/'ids.i32','<i4');assert num==len(ids)==c['H'] and 0<=enter<num and M==16 and efc==200
            assert maxlev==max(len(z[2])-1 for z in nodes) and len(nodes[enter][2])==maxlev+1
            edges=0
            for i,(label,vec,levels) in enumerate(nodes):
                assert label==int(ids[i]) and vec==w[i].tobytes()
                for lev,neighbors in enumerate(levels):
                    assert len(neighbors)<= (maxM0 if lev==0 else maxM) and len(set(neighbors))==len(neighbors)
                    assert all(0<=j<num and j!=i and len(nodes[j][2])>lev for j in neighbors);edges+=len(neighbors)
            ra=json.loads((out/'router_audit.json').read_text());assert ra['status']=='PASS' and ra['threads']==1 and ra['query_pairs']==256 and ra['new_ANN_calls']==512
            slots={int(z):i for i,z in enumerate(ids)};maxscore=0.
            for qi,row in enumerate(ra['returns']):
                for item in row:
                    score=1.-float(np.dot(fit[qi].astype('f8'),w[slots[item['id']]].astype('f8')));err=abs(score-item['distance'])
                    assert err<=item['round_bound'];maxscore=max(maxscore,err)
            profile=json.loads((out/'profile_complete.json').read_text());add=json.loads((out/'additional_complete.json').read_text());router=json.loads((out/'router_complete.json').read_text())
            assert profile['exact_labels_consumed']==2048 and profile['approx_labels_retained_after_override']==17952 and router['graph_builds']==1
            assert add['new_GT']==1024 and add['faiss_threads']==8 and add['affinity']==list(range(8));totalgt+=1024;ann_calls+=512
            for path,vv in json.loads((out/'selection_frozen.json').read_text())['files'].items():assert ident(path)==vv
            models[method]={'selection_features_tree_predictions_bits_match_record155_r0':True,'fit_GT_ID_bits_match':True,'fit_GT_distance_bits_match':pilot_differences+additional_differences==0,
                'fit_GT_distance_bit_differences_old_short_tail_only':pilot_differences+additional_differences,
                'profile_W_V_bits_match_sealed_simulation_rebuild':True,'independent_graph_nodes':num,'independent_graph_edges':edges,
                'native_query_pairs':256,'returned_score_max_error':maxscore,'temperature':selection['temperature'],
                'selection_seconds':selection['seconds'],'additional_base_load_seconds':add['base_load_flat_build_seconds'],
                'additional_GT_search_seconds':add['search_seconds'],'W_identity':ident(out/'W.f32'),'graph_identity':ident(out/'router.hnsw')}
        cost=run['datasets'][ds];default=json.loads(Path(r['default_cost_summary']).read_text())['datasets'][ds]['complete_build_wall_seconds']
        assert cost['complete_build_wall_seconds']>=cost['job_seconds_sum'] and abs(cost['job_seconds_sum']-sum(run['jobs'][j]['seconds'] for j in cost['jobs']))<1e-8
        records[ds]={'models':models,**cost,'default_complete_build_wall_seconds':default,'ratio_to_default_complete_wall':cost['complete_build_wall_seconds']/default,
            'primary_cost_lower_than_default':cost['complete_build_wall_seconds']<default,'first_base_load_seconds':exact['base_load_flat_build_seconds'],
            'qgt_search_seconds':exact['GT']['qgt_demand']['search_seconds'],'pilot_search_seconds':exact['GT']['pilot1024']['search_seconds'],
            'primary_job_seconds':{j:run['jobs'][j]['seconds'] for j in cost['jobs']}}
    identities=0
    for name in ['preparation.json','run_frozen.json']:
        for path,v in json.loads((R/'reviews'/name).read_text())['inputs'].items():assert ident(path)==v;identities+=1
    for path,v in frozen.items():assert ident(path)==v
    for path,v in json.loads((R/'reviews/preparation.json').read_text())['large_stat_only'].items():
        s=Path(path).stat();assert {'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}==v
    ledger=json.loads((R/'reviews/gt_ledger.json').read_text());assert totalgt==ledger['completed']==ledger['reserved']==7780 and teacher_calls==40064 and ann_calls==2048
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<C['max_new_bytes']
    dump(R/'results/cost_summary.json',{'status':'FIXED_ENERGY_FULL_BUILD_REPRODUCED','datasets':records,'new_exact_GT':totalgt,'new_NSG':teacher_calls,
        'new_audit_ANN':ann_calls,'new_profiles':4,'new_graphs':4,'new_trees':4,'new_qgt_kmeans_fits':2,'independent_fullbase_float64_GT_checks':4,'GT_tail_rounding_record':str(R/'reviews/GT_tail_float64_audit.json'),
        'gate_pass':all(v['primary_cost_lower_than_default'] for v in records.values()),'default_changed':False,'new_online_performance':False,
        'cost_scope':'single primary full wall from no target label input; current OS cache; all loads/processes/selection/output; controls incremental sharing H,teacher,pilot; post-audit separate'})
    dump(R/'reviews/independent_audit.json',{'status':'PASS','seconds':time.perf_counter()-start,'identities':identities,'references':frozen,
        'manual_tree_predictions':manual_predictions,'independent_hub_correction_checks':64,'max_correction_error':max_correction_error,
        'native_ANN_calls':ann_calls,'record155_r0_selections_restored':4,'independent_fullbase_float64_GT_checks':4,'short_tail_distance_bit_difference_disclosed':True,'new_graph_internal_validity_checked':4,
        'does_not_claim_historical_Energy_graph_identity_or_exact_route_top3':True,'default_changed':False})
    print('AUDIT PASS',[(ds,r['ratio_to_default_complete_wall']) for ds,r in records.items()],flush=True)
if __name__=='__main__':main()
