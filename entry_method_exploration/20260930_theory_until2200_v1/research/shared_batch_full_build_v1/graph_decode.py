from pathlib import Path
import struct
def decode_graph(p):
    raw=Path(p).read_bytes();off=0
    def read(fmt):
        nonlocal off
        fmt='<'+fmt;z=struct.unpack_from(fmt,raw,off);off+=struct.calcsize(fmt);return z
    offset0,maxel,n,size,labeloff,dataoff=read('QQQQQQ');maxlev,enter=read('iI');maxM,maxM0,M=read('QQQ');mult,efc=read('dQ');nodes=[]
    for i in range(n):
        s=off+i*size;count=struct.unpack_from('<H',raw,s+offset0)[0];edges=struct.unpack_from('<'+'I'*count,raw,s+offset0+4)
        label=struct.unpack_from('<Q',raw,s+labeloff)[0];nodes.append([label,raw[s+dataoff:s+labeloff],[edges]])
    off+=n*size
    for i in range(n):
        nb=read('I')[0];step=4+4*maxM;assert nb%step==0
        for j in range(nb//step):
            s=off+j*step;count=struct.unpack_from('<H',raw,s)[0];nodes[i][2].append(struct.unpack_from('<'+'I'*count,raw,s+4))
        off+=nb
    assert off==len(raw)
    return offset0,n,size,labeloff,dataoff,maxlev,enter,maxM,maxM0,M,mult,efc,nodes
