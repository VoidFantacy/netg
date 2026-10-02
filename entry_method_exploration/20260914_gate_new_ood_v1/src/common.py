from pathlib import Path
import hashlib, json, os, struct, time
import numpy as np

ROOT = Path('/data/netg/ACSG')
RUN = Path(__file__).resolve().parents[1]
DATASETS = json.loads((RUN/'config.locked.json').read_text())['datasets']
GATE_MODEL = 'gate_release10_v2'
GATE_FEATURE_READY = 'gate_release10_features.json'
GATE_GRAPH_FILE = 'gate.release10.graph2vec.f32'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(16*1024**2),b''): h.update(b)
    return h.hexdigest()
def dump(p,x):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');t.replace(p)
def vecs(p,dtype='f4'):
    d=int(np.fromfile(p,dtype='<i4',count=1)[0]);a=np.memmap(p,dtype=dtype,mode='r').reshape(-1,d+1)
    assert np.all(a[:,0].view('i4')==d)
    return a[:,1:]
def unit(x):
    x=np.asarray(x,dtype=np.float32);return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
def settings(ds):
    c=json.loads((ROOT/'benches/datasets/settings.json').read_text())['datasets'][ds]
    folder=ROOT/'benches/datasets'/c['dataset_dir']
    return {k:str(folder/v) for k,v in c.items() if k.endswith('_path')} | {'manifest':str(folder/'manifest.json'),'index':str(ROOT/'indices'/(ds+'_index')/'acosp_nsg.json')}
def nsg_map(path):
    with open(path,'rb') as f:
        def read(fmt):return struct.unpack('<'+fmt,f.read(struct.calcsize('<'+fmt)))
        version,n,d,metric,trained,built,build=read('iqii??c'); assert version in (1,2) and metric==0 and trained and built
        alpha,beta,rho,lam,it,th,L,R,ep,ants=read('ffffiiiiiq')
        for _ in range(2):
            count,=read('Q'); assert count==n;f.seek(count*4,1)
        k,count=read('iQ');assert count==n*k
        offset=f.tell();f.seek(count*4,1);vc,=read('Q');assert vc==n*d
        voff=f.tell()
    return np.memmap(path,mode='r',dtype='<i4',offset=offset,shape=(n,k)),np.memmap(path,mode='r',dtype='<f4',offset=voff,shape=(n,d)),dict(n=n,d=d,k=k,ep=ep,graph_offset=offset,vector_offset=voff,version=version)
def resource_check():
    import shutil
    assert shutil.disk_usage(RUN).free>=1610612736,'disk below frozen 1.5 GiB floor'
