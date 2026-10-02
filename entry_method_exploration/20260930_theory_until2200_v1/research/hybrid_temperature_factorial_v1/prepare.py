import hashlib
import json
import shutil
import time
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parent
ROOT=R.parents[3]
OLD=ROOT/'entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_approximate_target_profiles_v1'
PART=R.parent/'partial_replacement_v1'

def ident(p):
    p=Path(p)
    return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def dump(p,x):
    with Path(p).open('x') as f:
        json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

assert json.loads((PART/'reviews/independent_audit.json').read_text())['status']=='PASS'
assert not (R/'config.locked.json').exists()
assert shutil.disk_usage(R).free>=6*2**30
for name in ['inputs','models','results','reviews','logs','bin','src']:(R/name).mkdir(exist_ok=True)
shutil.copytree(OLD/'src/common',R/'src/common')
shutil.copy2(OLD/'src/kernels.hpp',R/'src/kernels.hpp')
shutil.copy2(OLD/'src/build_router.cpp',R/'src/build_router.cpp')
source=(OLD/'src/evaluate.cpp').read_text()
edits={
 'require(names.size()==2&&names[1]=="ApproxTarget10","two frozen methods");':'const int M=names.size();require((M==3||M==5)&&names[1]=="ApproxTarget10","frozen factorial methods");',
 'std::array<std::unique_ptr<Batch>,2> reference;':'std::vector<std::unique_ptr<Batch>> reference(M);',
 'std::array<std::vector<double>,2> wall;':'std::vector<std::vector<double>> wall(M);',
 '(ordinal+rep+c.value("dataset_order",0))%2;for(int z=0;z<2;++z){int m=(first+z)%2;':'(ordinal+rep+c.value("dataset_order",0))%M;for(int z=0;z<M;++z){int m=(first+z)%M;',
 'for(int m=0;m<2;++m){Batch':'for(int m=0;m<M;++m){Batch',
 'if(m==0){auto old=fs::path(c["baseline_reference"]':'if(m<2){auto old=fs::path(c["baseline_reference"]',
 'calls==(n*2*(reps+2)+32)*c["points"].size()':'calls==(n*M*(reps+2)+16*M)*c["points"].size()',
 '{"router_calls",calls}':'{"router_calls",n*M*(reps+2)*c["points"].size()}',
 '{"points",ordinal*2}':'{"points",ordinal*M}'
}
for old,new in edits.items():
    assert source.count(old)==1,old
    source=source.replace(old,new)
(R/'src/evaluate.cpp').write_text(source)
old_config=json.loads((OLD/'config.locked.json').read_text())
datasets={};protected={};large={}
for index,(ds,dc) in enumerate(old_config['datasets'].items()):
    c=dc['original'];d=c['dimension'];ip=R/'inputs'/ds;ip.mkdir()
    rows=np.random.default_rng(2026093002+index).permutation(20000)[:2048].astype('<i4')
    np.testing.assert_array_equal(rows,np.load(PART/'results'/(ds+'.npz'))['selected_rows'][0])
    gt=np.fromfile(c['fit_source']['gt_file'],'<i8').reshape(20000,100)
    rows.tofile(ip/'selected_rows.i32');gt[rows].astype('<i8').tofile(ip/'selected_gt.i64')
    ec=json.loads((OLD/'inputs'/ds/'evaluate.json').read_text())
    ec['points']=[{'K':1,'L':1000 if index==0 else 128},{'K':100,'L':1250 if index==0 else 256}]
    new_names=['HybridFixedTemperature','ApproxPilotTemperature','HybridPilotTemperature'] if index==0 else ['HybridFixedTemperature']
    for name in new_names:
        mp=R/'models'/ds/name;mp.mkdir(parents=True)
        method={'name':name,'ids':c['anchor']['ids'],'W':str(mp/'W.f32'),'graph':str(mp/'router.hnsw')}
        ec['methods'].append(method)
        dump(ip/(name+'.build.json'),{'dimension':d,'methods':[ec['methods'][0],method]})
    ec['baseline_reference']=str(OLD/'results'/ds/'evaluation')
    ec['max_search_calls']=210000 if index==0 else 130000
    ec['seconds_cap']=1800
    dump(ip/'evaluate.json',ec)
    # Candidate construction sees no full exact target file.
    profile={'dataset':ds,'dimension':d,'base_n':c['base_n'],'base':c['base'],'hub_ids':c['anchor']['ids'],
             'queries':c['fit_source']['queries_file'],'approx_ids':str(OLD/'results'/ds/'labels/ids.i32'),
             'selected_rows':str(ip/'selected_rows.i32'),'selected_gt':str(ip/'selected_gt.i64'),
             'old_temperature':json.loads((OLD/'models'/ds/'profiles.json').read_text())['temperature'],
             'methods':ec['methods'],'n':20000,'pilot_n':2048}
    dump(ip/'profiles.json',profile)
    fit=np.fromfile(profile['queries'],'<f4').reshape(20000,d)
    eq=np.fromfile(ec['queries'],'<f4').reshape(4096,d)
    fit_hashes={hashlib.sha256(x.tobytes()).digest() for x in fit}
    assert not any(hashlib.sha256(x.tobytes()).digest() in fit_hashes for x in eq)
    for p in [profile['queries'],profile['hub_ids'],profile['approx_ids'],c['fit_source']['gt_file'],ec['queries'],ec['gt']]+[m[k] for m in ec['methods'][:2] for k in ['W','graph','ids']]:
        protected[str(p)]=ident(p)
    for p in [c['base'],c['index']]:
        st=Path(p).stat();large[p]={'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
    datasets[ds]={'profiles':profile,'evaluate':ec,'new_methods':new_names,'training_eval_overlap':0}
config={'datasets':datasets,'bootstrap_reps':20000,'bootstrap_seed':2026093004,'max_NSG':330000,'max_ANN':327680,
        'deadline_unix':1790775000,'seconds_cap':1800,'default_changed':False}
dump(R/'config.locked.json',config)
dump(R/'reviews/prepare_inputs.json',{'files':protected,'large_stat_only':large,'unix':time.time(),
     'prepare_source':ident(Path(__file__)),'source_edits':list(edits),'full_exact_GT_read_only_to_extract_fixed_rows':True})
print('PREPARED',flush=True)
