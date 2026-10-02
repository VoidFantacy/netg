from common import *
assert read(LOCK['wait_for_E108'])['status']=='PASS','E108 all timing and independent analysis must finish first'
assert not (RUN/'reviews/inputs_prepared.json').exists()
deadline();protected_check();start=time.time();n=LOCK['n'];all_records=[]
freeze=[identity(p) for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[identity(RUN/nm) for nm in ['protocol.md','config.locked.json']]+[identity(p) for p in (RUN/'theory_snapshot').glob('*.md')]
dump(RUN/'reviews/pre_fit_lock.json',dict(created_unix=time.time(),files=freeze,fit_numeric_payload_decoded=False,heldout_access=False))
selection=(np.arange(n,dtype='int64')*20000//n);assert len(np.unique(selection))==n and selection.min()==0 and selection.max()<20000
for ds,c in LOCK['datasets'].items():
 t=time.time();d=c['dimension'];h=c['H'];inp=Path(c['fit_input']);meta=read(inp/'prepared.json');base_path=Path(meta['base_file']);assert sha(base_path)==meta['source_train']['base']['sha256']
 qfull=np.fromfile(inp/'fit/queries.f32','<f4').reshape(20000,d);gfull=np.fromfile(inp/'fit/gt.i64','<i8').reshape(20000,100);rows=np.fromfile(inp/'fit/row_ids.i64','<i8');hids=np.fromfile(inp/'hub_ids.i32','<i4');assert np.array_equal(rows,np.arange(10000,30000)) and len(hids)==h and np.all(np.diff(hids)>0)
 raw=np.fromfile(inp/'raw_hubs.f32','<f4').reshape(h,d);unit=np.fromfile(c['unit_W'],'<f4').reshape(h,d);assert np.array_equal((raw/np.linalg.norm(raw,axis=1,keepdims=True)).view('<u4'),unit.view('<u4'))
 stored=np.load(c['assignments']);assert np.array_equal(stored['row_ids'],rows) and np.array_equal(stored['hub_ids'],hids)
 real=stored['rank_hubs'];assert real.shape==(20000,10);cols=np.searchsorted(hids,real[selection]);assert np.array_equal(hids[cols],real[selection])
 counts=np.zeros((n,h),dtype='<i4');np.add.at(counts,(np.repeat(np.arange(n),10),cols.ravel()),1);assert np.all(counts.sum(1)==10) and np.all(counts>=0)
 q=qfull[selection].copy();gt=gfull[selection].copy();assert np.isfinite(q).all() and np.all((gt>=0)&(gt<c['base_n'])) and np.all(np.diff(np.sort(gt,axis=1),axis=1)>0)
 base=np.memmap(base_path,dtype='<f4',mode='r').reshape(c['base_n'],d+1);assert np.array_equal(base[hids,1:],raw)
 mean=np.zeros((n,d),dtype='float64');norms=[]
 for rank in range(10):
  target=np.asarray(base[gt[:,rank],1:],dtype='float32');norm=np.linalg.norm(target,axis=1,keepdims=True);assert np.isfinite(target).all() and np.all(norm>1e-12);norms.extend(norm[:,0].tolist());mean+=(target/norm).astype('float64')/10
 mean=mean.astype('<f4');assert np.all(np.linalg.norm(mean,axis=1)<=1+2e-6)
 max_error=0.;max_rank_gap=0.
 for i in range(0,n,64):
  reference=np.zeros(d,dtype='float64')
  for rank in range(10):
   v=base[gt[i,rank],1:].astype('float64');v/=np.linalg.norm(v);reference+=v/10;scores=unit.astype('float64')@v;gap=float(scores.max()-scores[cols[i,rank]]);max_rank_gap=max(max_rank_gap,gap);assert gap<2e-6,'cached hard attribution independent float64 check'
  error=float(np.max(np.abs(reference-mean[i])));max_error=max(max_error,error);assert error<2e-6
 out=RUN/'inputs'/ds;out.mkdir();q.tofile(out/'queries.f32');gt.astype('<i4').tofile(out/'gt.i32');rows[selection].astype('<i8').tofile(out/'source_rows.i64');selection.tofile(out/'fit_indices.i64');counts.tofile(out/'coverage_counts.i32');mean.tofile(out/'target_mean.f32')
 cfg=dict(dataset=ds,n=n,dimension=d,H=h,base_n=c['base_n'],index=c['index'],base=str(base_path),queries=str(out/'queries.f32'),GT=str(out/'gt.i32'),source_rows=str(out/'source_rows.i64'),fit_indices=str(out/'fit_indices.i64'),coverage_counts=str(out/'coverage_counts.i32'),target_mean=str(out/'target_mean.f32'),unit_W=c['unit_W'],GT10_W=c['default']['W'],hub_ids=str(inp/'hub_ids.i32'),threads=1,methods=LOCK['methods'],deadline_unix=LOCK['deadline_unix'],seconds_cap=LOCK['job_seconds_cap'],max_search_calls=LOCK['max_NSG_calls'])
 dump(out/'config.json',cfg);record=dict(dataset=ds,config=cfg,files=[identity(p) for p in out.iterdir() if p.is_file()],mean_independent_max_abs=max_error,stored_hub_independent_max_score_gap=max_rank_gap,independent_checks=32*10,coverage_row_sum=10,source_rows='prelocked systematic fit indices +10000',seconds=time.time()-t,privileged_fit_diagnostic=True)
 dump(out/'manifest.json',record);all_records.append(record);print(ds,'fit proxy inputs prepared',round(record['seconds'],2),flush=True)
 assert time.time()-start<300
protected_check();dump(RUN/'reviews/inputs_prepared.json',dict(status='PASS',datasets=all_records,seconds=time.time()-start,new_GT=0,new_training=0,heldout_access=False))
print('PROXY_INPUTS_PREPARED',flush=True)
