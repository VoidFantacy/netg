from shared import *
import struct

def inspect_serialized(path,P,mapping):
 data=Path(path).read_bytes();fmt='<6QiI3QdQ';head=struct.unpack_from(fmt,data);start=struct.calcsize(fmt)
 off,mx,n,size,label,coord,level,entry,M,M0,m,mult,ef=head
 assert off==0 and mx==n==len(P) and M==m==16 and M0==32 and ef==200 and label-coord==P.shape[1]*4
 cursor=start+n*size;upper=[];levels=[]
 for i in range(n):
  count=struct.unpack_from('<I',data,cursor)[0];cursor+=4;assert count%(M*4+4)==0
  levels.append(count//(M*4+4));upper.append(data[cursor:cursor+count]);cursor+=count
 assert cursor==len(data) and max(levels)==level
 topology=[n,P.shape[1],entry,level]
 for i in range(n):
  row=start+i*size;lab=struct.unpack_from('<Q',data,row+label)[0]
  assert lab==int(mapping[i]) and data[row+coord:row+label]==np.ascontiguousarray(P[i]).tobytes()
  topology.extend([lab,levels[i]])
  blocks=[data[row:row+M0*4+4]]+[upper[i][j*(M*4+4):(j+1)*(M*4+4)] for j in range(levels[i])]
  for lev,block in enumerate(blocks):
   count=struct.unpack_from('<H',block)[0];assert count<=(M0 if lev==0 else M)
   adj=np.frombuffer(block,dtype='<u4',count=count,offset=4);assert (adj<n).all() and len(np.unique(adj))==count and i not in adj
   topology.append(count);topology.extend(map(int,adj))
 return dict(topology_sha=digest(np.array(topology,np.int32)),profile_rows=n,levels=levels,header=list(head))
