"""Acquire pinned public inputs; never execute downloaded source or decode test rows."""
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.request

RUN = Path(__file__).resolve().parents[1]
REV = '07b387891a221b7b073b83d2f752b76462e5fa03'

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'ACSG-E96-research'}), timeout=60)

def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')

def main():
    api=f'https://huggingface.co/api/datasets/vector-index-bench/vibe/tree/{REV}?recursive=true&expand=true&limit=100'
    with get(api) as f: listing=json.load(f)
    save_json(RUN/'sources/huggingface_listing.json',listing)
    for name in ['yi-128-ip.hdf5','llama-128-ip.hdf5']:
        item=next(x for x in listing if x['path']==name)
        dest=RUN/'sources'/name
        if dest.exists():
            info=json.loads(dest.with_suffix('.download.json').read_text())
            assert info['bytes']==dest.stat().st_size
            print('ALREADY_ACQUIRED',name,flush=True)
            continue
        assert shutil.disk_usage(RUN).free > item['size']+2*1024**3
        assert not dest.with_suffix('.partial').exists(),'preserve partial and inspect before retry'
        url=f'https://huggingface.co/datasets/vector-index-bench/vibe/resolve/{REV}/{name}?download=true'
        digest=hashlib.sha256();count=0;start=time.monotonic();last=start
        with get(url) as response, dest.with_suffix('.partial').open('xb') as output:
            for chunk in iter(lambda:response.read(4*1024**2),b''):
                output.write(chunk);digest.update(chunk);count+=len(chunk)
                if time.monotonic()-last>15:
                    print(name,count,'/',item['size'],flush=True);last=time.monotonic()
        assert count==item['size']
        expected=item.get('lfs',{}).get('oid')
        if expected: assert digest.hexdigest()==expected,(name,digest.hexdigest(),expected)
        dest.with_suffix('.partial').rename(dest)
        save_json(dest.with_suffix('.download.json'),{'url':url,'revision':REV,'bytes':count,'sha256':digest.hexdigest(),'expected_lfs_sha256':expected,'seconds':time.monotonic()-start})
        print('ACQUIRED',name,count,digest.hexdigest(),flush=True)
    for name,url in {
        'vibe_README.md':f'https://huggingface.co/datasets/vector-index-bench/vibe/raw/{REV}/README.md',
        'vibe_datasets.py':'https://raw.githubusercontent.com/vector-index-bench/vibe/main/vibe/datasets.py',
        'gate_upstream_model.py':'https://raw.githubusercontent.com/jacksondca/gate/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/model.py',
        'gate_upstream_train.py':'https://raw.githubusercontent.com/jacksondca/gate/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/__main__.py',
        'gate_upstream_fusion.py':'https://raw.githubusercontent.com/jacksondca/gate/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/fusion.py',
        'gate_upstream_search.cpp':'https://raw.githubusercontent.com/jacksondca/gate/229f18dadb791ddede22597e44d5ceb028b104ba/tests/test_gate_search.cpp',
    }.items():
        dest=RUN/'sources'/name
        if not dest.exists():
            with get(url) as response: data=response.read()
            dest.write_bytes(data)
            save_json(dest.with_suffix(dest.suffix+'.source.json'),{'url':url,'sha256':hashlib.sha256(data).hexdigest(),'download_unix':time.time()})

if __name__=='__main__':main()
