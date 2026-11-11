import numpy as np
def view(d):
 dim=d['d'];a=np.memmap(d['path'],'<f4','r');start=d.get('row_start',0);n=d['n']
 if d['format']=='fvecs':a=a.reshape(-1,dim+1);assert np.all(a[np.linspace(0,len(a)-1,64,dtype=int),0].view('<i4')==dim);return a[start:start+n,1:]
 if d['format']=='fbin':a=a[2:]
 return a.reshape(-1,dim)[start:start+n]
def gt(d):
 dt='<i8' if d['format']=='raw_i64' else '<i4';a=np.memmap(d['path'],dt,'r').reshape(-1,101 if d['format']=='ivecs' else 100);return a[d.get('row_start',0):][:d['n'],1 if d['format']=='ivecs' else 0:]

def read_array(path,dtype):
 from pathlib import Path
 import gzip
 p=Path(path)
 if p.exists():return np.fromfile(p,dtype)
 return np.frombuffer(gzip.open(str(p)+'.gz','rb').read(),dtype=dtype).copy()
