from common import *
threads();resources();check(O/'reviews/precompile_freeze.json');paths=[Path(x['path']) for x in read(O/'reviews/precompile_freeze.json')['files']]
for ds in DS:
 src=read(R/'entry_method_exploration/20260911_hnsw_edge_rl_v1/inputs'/ds/'config.json');rc=read(O/'inputs'/ds/'routes.json');nc=read(O/'inputs'/ds/'native.json');old=read(E66/'inputs'/ds/'fit.json')
 for key,dt,w in [('queries_file',np.float32,rc['dim']),('gt_file',np.int64,100),('row_ids',np.int64,1)]:
  assert Path(src[key]).read_bytes()==np.fromfile(old[key],dt,count=20000*w).tobytes();paths += [Path(src[key])]
 nc.update(queries_file=src['queries_file'],gt_file=src['gt_file'],row_ids=src['row_ids']);dump(O/'inputs'/ds/'native_training.json',nc);paths.append(O/'inputs'/ds/'native_training.json')
dump(O/'reviews/input_container_clarification.json',dict(scope='Before first training/native call. Frozen native.json is an unused preparation template with 22048-row container; effective native_training.json references existing exact 20000-row E24 files, all query/GT/row bytes verified against E66 first20K. No source/binary/label or protocol change; original template preserved.'))
paths+=list((O/'src').glob('*'))+[O/'bin/routes.so',O/'bin/provenance.json',O/'config.locked.json',O/'reviews/input_container_clarification.json'];freeze(O/'reviews/pretraining_freeze.json',paths)
dump(O/'state.json',dict(status='READY_TRAINING_FROZEN',NSG=0,HNSW=0,day_goal_complete=False));print('E86_READY_TRAINING')
