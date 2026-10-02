from common import *
import struct
def inspect_serialized(path,W,labels):
    data=Path(path).read_bytes();head=struct.unpack_from('<6QiI3QdQ',data);off,mx,n,size,label,coord,level,entry,M,M0,m,mult,ef=head
    start=struct.calcsize('<6QiI3QdQ');assert off==0 and mx==n==len(W) and M==m==16 and M0==32 and ef==200 and label-coord==W.shape[1]*4
    cursor=start+n*size;uppers=[];levels=[]
    for i in range(n):
        nb=struct.unpack_from('<I',data,cursor)[0];cursor+=4;assert nb%(M*4+4)==0;levels.append(nb//(M*4+4));uppers.append(data[cursor:cursor+nb]);cursor+=nb
    assert cursor==len(data) and max(levels)==level
    for i in range(n):
        row=start+i*size;assert struct.unpack_from('<Q',data,row+label)[0]==int(labels[i]) and data[row+coord:row+label]==W[i].tobytes()
        blocks=[data[row:row+M0*4+4]]+[uppers[i][j*(M*4+4):(j+1)*(M*4+4)] for j in range(levels[i])]
        for lev,b in enumerate(blocks):
            count=struct.unpack_from('<H',b)[0];assert count<=(M0 if lev==0 else M)
            adj=np.frombuffer(b,'<u4',count=count,offset=4);assert (adj<n).all() and len(np.unique(adj))==count and i not in adj
    return dict(path=str(path),physical_profiles=n,sha256=sha(path),unique_external_labels=len(set(map(int,labels))))
