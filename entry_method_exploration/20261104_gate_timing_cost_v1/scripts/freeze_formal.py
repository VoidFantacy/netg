from common import *
assert read(R/'reviews/qualification_complete.json')['status']=='PASS_FOUR_DATASET_BRANCH_PROFILE_OLD_ACTION_AND_PLACEMENT_QUALIFICATION'
old=read(OLD/'formal_freeze.json');files=[];large=[]
for ref in old['files']:
    assert sha(ref['path'])==ref['sha256'],ref['path'];files.append(ref)
for ref in old['large_inherited_inputs']:
    if ref.get('dataset') not in DS:continue
    st=Path(ref['path']).stat();assert st.st_size==ref['bytes'] and st.st_mtime_ns==ref['mtime_ns'];large.append(ref)
for ds in DS:
  for w in ['A','B']:
    c=read(R/'configs'/f'{ds}.{w}.formal.json')
    for p in [c['queries']['path'],c['test_gt']['path']]:files.append(dict(path=p,sha256=sha(p),bytes=Path(p).stat().st_size))
dump(R/'inherited_identity.json',dict(status='PASS_INHERITED_SCIENTIFIC_FILES_AND_LARGE_STATS',files=files,large=large))
sources=list((R/'src').glob('*'))+list((R/'scripts').glob('*.py'))+[R/'protocol.md',R/'role_freeze.json',R/'assets_freeze.json',R/'gate_training_freeze.json',R/'inherited_identity.json',R/'storage/benchmark']
sources+=list((R/'storage/gates').rglob('*.json'))
for ds in DS:
    for ref in read(R/'configs'/f'{ds}.gate_labels.json')['model_files']:
        p=Path(ref['path']);j=read(p);sources += [p,Path(j['node_ids']),Path(j['node_embeddings'])]
frozen=[dict(path=str(p),sha256=sha(p),points=len(read(p)['points'])) for p in sorted((R/'configs').glob('*.formal.json'))]
dump(R/'formal_freeze.json',dict(status='FROZEN_BEFORE_FORMAL_TEST_RESPONSES',configs=frozen,sources=[dict(path=str(p),sha256=sha(p)) for p in sorted(set(sources)) if p.is_file()],points=sum(x['points'] for x in frozen),protocol='four multimodal, K1/K100 L200 gate study; no threshold retuning',created_unix=time.time()))
print('FORMAL_FROZEN',sum(x['points'] for x in frozen),flush=True)
