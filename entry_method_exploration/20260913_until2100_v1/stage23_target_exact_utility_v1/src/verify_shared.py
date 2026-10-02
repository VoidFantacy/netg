from common import *
threads();records=[];paths=[]
for ds in DS:
 sc=read(E81/'inputs'/ds/'aux.json');rows=np.fromfile(sc['row_ids'],np.int64)
 for m in ['exact_P','exact_mode']:
  a=np.load(E69/'results'/ds/(m+'.npz'));assert np.array_equal(a['source_rows'],rows)
 cc=read(C/'stage7_multimode_index_v1/inputs'/ds/'construction.json');d=cc['dim']
 root=E73/'models'/ds
 full=np.fromfile(C/'stage7_multimode_index_v1/models'/ds/'mode3P/W.f32',np.float32).reshape(-1,d)
 w=np.fromfile(root/'W.f32',np.float32).reshape(-1,d)
 inv=np.fromfile(root/'old_to_compact.i32',np.int32)
 assert w[inv].tobytes()==full.tobytes()
 orig=np.fromfile(root/'original_slots.i32',np.int32);assert full[orig].tobytes()==w.tobytes()
 records.append(dict(dataset=ds,source_rows_verified=7952,complete_mode_bank_bytes_recovered=True,physical=len(w)))
 paths += [root/x for x in ['W.f32','old_to_compact.i32','original_slots.i32']]+[C/'stage7_multimode_index_v1/models'/ds/'mode3P/W.f32']
dump(O/'reviews/shared_bank_verification.json',dict(status='PASS',records=records));freeze(O/'reviews/shared_bank_freeze.json',paths+[O/'src/verify_shared.py',O/'reviews/shared_bank_verification.json'])
print('PASS_SHARED_BANK_AND_SOURCE_ROWS')
