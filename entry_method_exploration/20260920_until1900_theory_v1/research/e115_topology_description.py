from pathlib import Path
import json,struct,hashlib,time
import numpy as np
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1];R=TB/'stages/e115_score_topology_factorial';OLD=ROOT/'entry_method_exploration/20260920_until1600_theory_v1/stages/e108_unit_hub_online'
def read(p):return json.loads(Path(p).read_text())
def ident(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def parse(p,d,h):
 raw=Path(p).read_bytes();header=struct.unpack_from('<6QiI3QdQ',raw,0);start=struct.calcsize('<6QiI3QdQ');offset0,maxel,n,row,labeloff,dataoff,maxlevel,ep,maxM,maxM0,M,mult,efc=header
 assert n==h and dataoff+d*4==labeloff and M==16 and efc==200
 layers=[[] for _ in range(maxlevel+1)];labels=[];vectors=[];levels=[]
 for i in range(n):
  pos=start+i*row;count=struct.unpack_from('<H',raw,pos+offset0)[0];assert count<=maxM0
  neighbors=struct.unpack_from('<'+'I'*count,raw,pos+offset0+4);assert all(j<n and j!=i for j in neighbors) and len(set(neighbors))==count
  layers[0].append([i,list(neighbors)]);labels.append(struct.unpack_from('<Q',raw,pos+labeloff)[0]);vectors.append(raw[pos+dataoff:pos+dataoff+d*4])
 pos=start+n*row;upper_row=maxM*4+4
 for i in range(n):
  size=struct.unpack_from('<I',raw,pos)[0];pos+=4;assert size%upper_row==0;level=size//upper_row;levels.append(level)
  for l in range(1,level+1):
   count=struct.unpack_from('<H',raw,pos+(l-1)*upper_row)[0];assert count<=maxM
   neighbors=struct.unpack_from('<'+'I'*count,raw,pos+(l-1)*upper_row+4);assert all(j<n and j!=i for j in neighbors) and len(set(neighbors))==count
   layers[l].append([i,list(neighbors)])
  pos+=size
 assert pos==len(raw) and max(levels)==maxlevel and labels==sorted(labels)
 stats=[]
 for l,items in enumerate(layers):
  deg=np.array([len(v) for _,v in items]);stats.append(dict(layer=l,nodes=len(items),edges=int(deg.sum()),mean_outdegree=float(deg.mean()),median_outdegree=float(np.median(deg)),minimum=int(deg.min()),maximum=int(deg.max())))
 active=dict(labels=labels,levels=levels,entrypoint=int(ep),maxlevel=int(maxlevel),ordered_active_adjacency=layers)
 return dict(source=ident(p),header=list(header),layers=stats,active_topology_sha256=hashlib.sha256(json.dumps(active,sort_keys=True).encode()).hexdigest(),vector_sha256=hashlib.sha256(b''.join(vectors)).hexdigest()),active
out=R/'results/topology_description.json';assert not out.exists();started=time.time();results=[]
for ds in read(R/'config.locked.json')['datasets']:
 old=read(OLD/'reviews'/('formal_'+ds['dataset']+'.json'));graphs={};states={}
 for name,m in zip(['GP_original','GP_rebuilt','GU'],old['methods']):
  graphs[name],states[name]=parse(m['graph'],ds['dimension'],ds['H']);assert graphs[name]['vector_sha256']==ident(m['W'])['sha256']
 comparisons=[]
 for a,b in [('GP_original','GP_rebuilt'),('GP_original','GU'),('GP_rebuilt','GU')]:
  x,y=states[a],states[b];comparisons.append(dict(a=a,b=b,same_levels=x['levels']==y['levels'],same_entrypoint=x['entrypoint']==y['entrypoint'],same_active_topology=graphs[a]['active_topology_sha256']==graphs[b]['active_topology_sha256'],same_level0_rows=sum(v==w for v,w in zip(x['ordered_active_adjacency'][0],y['ordered_active_adjacency'][0]))))
 results.append(dict(dataset=ds['dataset'],graphs=graphs,comparisons=comparisons))
record=dict(status='PASS',created_unix=time.time(),seconds=time.time()-started,source=ident(__file__),posthoc_static_description=True,gate_unchanged=True,new_NSG=0,new_ANN=0,new_GT=0,new_training=0,datasets=results)
out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
