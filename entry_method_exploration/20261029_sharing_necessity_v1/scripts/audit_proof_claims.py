"""Check integer oracle certificates and concrete counterexamples separately."""
import array,csv,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R.parent/'20261028_seven_dataset_scoring_v1'
sys.path.insert(0,str(OLD/'scripts'))
from packet_archive import read_bytes
def rows(p):return list(csv.DictReader(Path(p).open()))
def a(p,k='i'):
 x=array.array(k);p=Path(p);x.frombytes(p.read_bytes() if p.exists() else read_bytes(p));return x
def read(p):return json.loads(Path(p).read_text())
def main():
 t=time.perf_counter();points=rows(R/'analysis/all_native_points.csv');covers=rows(R/'analysis/all_native_coverage.csv');certs=rows(R/'analysis/oracle_cost_certificates.csv')
 for c in certs:
  ds,m=c['dataset'],c['method'];p=[x for x in points if x['dataset']==ds];b=next(x for x in p if x['method']=='GT10' and x['L']=='200');method=next(x for x in p if x['method']==m and x['L']=='200');cover=next(x for x in covers if x['dataset']==ds and x['method']==m);upper=int(b['hits'])+int(cover['pool_covered']);scan=int(b['hits'])+int(cover['scan_covered']);assert int(c['optimistic_pool_hit_ceiling'])==upper and int(c['optimistic_scan_hit_ceiling'])==scan
  dom=[x['L'] for x in p if x['method']=='GT10' and int(x['hits'])>=upper and float(x['qps'])>=float(method['qps'])];assert c['GT_dominating_even_pool_oracle_L']==','.join(dom)
 witnesses=read(R/'analysis/actual_counterexamples.json');checked=0
 for ds in dict.fromkeys(x['dataset'] for x in witnesses):
  config=read(OLD/f'configs/{ds}.json');source=set(a(Path(config['source_dir'])/'global_ids.i32'));d=config['test_gt'];g=a(d['path'],'q' if d['format']=='raw_i64' else 'i');stride=101 if d['format']=='ivecs' else 100;start=d.get('row_start',0)
  for w in [x for x in witnesses if x['dataset']==ds]:
   K,i,m=w['K'],w['query'],w['method'];root=OLD/f'storage/results/{ds}/k{K}';main=a(root/'GT10_L200/raw/ids.i32');final=a(root/f'{m}_L200/raw/ids.i32');truth=set(g[(i+start)*stride+(stride==101):(i+start)*stride+(stride==101)+K]);original=set(main[i*K:(i+1)*K]);new=(truth&set(final[i*K:(i+1)*K]))-original
   assert new and new==set(w['rescued_ids']);assert not ((truth-original)&source);assert set(w['main_return'])==original and set(w['test_GT'])==truth;checked+=1
 toy=read(R/'analysis/mathematical_counterexample.json');x=toy['base'];train=toy['train_query'];test=toy['test_query'];gttrain=min(range(len(x)),key=lambda i:(x[i]-train)**2);gttest=min(range(len(x)),key=lambda i:(x[i]-test)**2);final=min(set(toy['assumed_test_main_return'])|set(toy['proposed_block']),key=lambda i:(x[i]-test)**2);assert gttrain!=gttest and gttest not in toy['training_missing_IDs'] and final==gttest
 v=dict(status='PASS_E192_INTEGER_CERTIFICATES_AND_CONCRETE_COUNTEREXAMPLES',oracle_certificates=len(certs),actual_witnesses_checked=checked,executable_toy_checked=True,seconds=time.perf_counter()-t,scope='The fixed-source theorem is mathematical; tests validate reported finite data/counterexamples, not a universal impossibility assertion.')
 (R/'reviews/proof_claims_audit.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
if __name__=='__main__':main()
