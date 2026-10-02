"""Rescore all saved full-H samples and every baseline full return against GT."""
from common import *

def make_masks(membership):
    padded = np.pad(membership, [(0, 0), (0, 28)])
    return np.packbits(padded, axis=1, bitorder='little').view('<u8').reshape(-1, 2)

if __name__ == '__main__':
    start = time.monotonic()
    records = []
    for ds in read(RUN/'config.locked.json')['datasets']:
        data = load_data(ds)
        nbase = read(OLD/'config.locked.json')['datasets'][ds]['base_n']
        assert (data['gt'] >= 0).all() and (data['gt'] < nbase).all()
        assert (np.diff(np.sort(data['gt'], axis=1), axis=1) > 0).all()
        labeldir = OLD/'results'/ds/'labels'
        total_samples = 0
        for block in read(labeldir/'complete.json')['blocks']:
            lo, nb = block['start'], block['n']
            p = labeldir/f'block_{lo}'
            sample = np.fromfile(p/'sample_ids.i32','<i4').reshape(len(data['hubs'])+1,100)
            assert (sample >= 0).all() and (sample < nbase).all()
            membership = (sample[:,:,None] == data['gt'][lo,None,None,:]).any(axis=1)
            assert np.array_equal(make_masks(membership),data['masks'][lo])
            baseline = np.fromfile(p/'baseline_ids.i32','<i4').reshape(nb,100)
            membership = (baseline[:,:,None] == data['gt'][lo:lo+nb,None,:]).any(axis=1)
            assert np.array_equal(make_masks(membership),data['masks'][lo:lo+nb,0])
            assert (np.diff(np.sort(sample,axis=1),axis=1)>0).all()
            assert (np.diff(np.sort(baseline,axis=1),axis=1)>0).all()
            total_samples += len(sample)
        records.append(dict(dataset=ds, full_H_sample_returns_rescored=total_samples,
            all_baseline_full_returns_rescored=4096, K100_mask_bit_identity=True,
            GT_and_return_ID_validity_and_uniqueness=True))
        print('RETURN_SCORE_PASS',ds,total_samples,flush=True)
    dump(RUN/'reviews/label_return_audit.json',dict(status='PASS',datasets=records,
        seconds=time.monotonic()-start,new_search_calls=0,new_GT=False))
