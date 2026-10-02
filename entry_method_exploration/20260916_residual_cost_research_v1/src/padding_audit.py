"""Read-only audit of native NSG adjacency; no search or index mutation."""
import pathlib,json,struct,time
import numpy as np
D=pathlib.Path(__file__).resolve().parent.parent;c=json.loads((D/'config.json').read_text());t=time.time();p=pathlib.Path(c['index'])
with p.open('rb') as f:
 fmt='<iqii??cffffiiiiiq';values=struct.unpack(fmt,f.read(struct.calcsize(fmt)));version,n,d,metric=values[:4]
 assert version in [1,2] and n==2505000 and d==512 and metric==0,values
 for _ in range(2):
  size,=struct.unpack('<Q',f.read(8));assert size==n;f.seek(size*4,1)
 K,=struct.unpack('<i',f.read(4));count,=struct.unpack('<Q',f.read(8));assert K==64 and count==n*K
 offset=f.tell();hist=np.zeros(K+1,dtype=np.int64);holes=0;outofrange=0;notminusone=0;seen=0
 while seen<n:
  take=min(32768,n-seen);a=np.fromfile(f,dtype='<i4',count=take*K).reshape(take,K);valid=(a>=0)&(a<n);degree=valid.sum(axis=1);span=np.where(valid,np.arange(K,dtype=np.int16)+1,0).max(axis=1)
  holes+=int((span!=degree).sum());outofrange+=int((a>=n).sum());notminusone+=int(((~valid)&(a!=-1)).sum());hist+=np.bincount(degree,minlength=K+1);seen+=take
x={'status':'PASS','index':str(p),'n':n,'K':K,'adjacency_file_offset':offset,'adjacency_bytes_read':count*4,'rows_with_nontrailing_invalid_slots':holes,'out_of_range_positive_ids':outofrange,'invalid_slots_not_minus_one':notminusone,'degree_histogram':hist.tolist(),'mean_degree':float(np.dot(np.arange(K+1),hist)/n),'zero_degree_rows':int(hist[0]),'search_calls':0,'seconds':time.time()-t,'note':'This frozen graph has trailing padding iff rows_with_nontrailing_invalid_slots is zero. General graphs require validation or a last-valid-span fallback.'}
(D/'results/padding_audit.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({k:v for k,v in x.items() if k!='degree_histogram'},indent=2))
