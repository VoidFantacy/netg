from common import *
import ctypes as C
class Environment:
 def __init__(self,c,folder,load_nsg=True):
  self.lib=C.CDLL(str(O/'bin/environment_v2.so'));v=C.c_void_p;z=C.c_size_t;i=C.c_int;u=C.c_uint64;p=C.c_char_p
  defs={'e33_create':([p,p,i],v),'e33_destroy':([v],None),'e33_error':([],p),'e33_run':([v,v,z,v,v,u,i,i],i),'e33_static':([v,v,z,p],i),'e33_export':([v,v,p],i),'e33_parity':([v,v,z,v,i],i),'e33_data':([v,i,C.POINTER(z)],v),'e33_calls':([v],u),'e33_routes':([v],u)}
  for name,(a,r) in defs.items():getattr(self.lib,name).argtypes=a;getattr(self.lib,name).restype=r
  self.ptr=self.lib.e33_create(json.dumps(c).encode(),str(folder).encode(),load_nsg);assert self.ptr,self.lib.e33_error().decode()
  self.topology=read(Path(folder)/'topology.json');self.edges=self.topology['edges']
 def close(self):
  if self.ptr:self.lib.e33_destroy(self.ptr);self.ptr=None
 def __enter__(self):return self
 def __exit__(self,*args):self.close()
 def check(self,status):assert status==0,self.lib.e33_error().decode()
 def data(self,field,dtype):
  length=C.c_size_t();ptr=self.lib.e33_data(self.ptr,field,C.byref(length))
  if not length.value:return np.empty(0,dtype)
  a=np.ctypeslib.as_array((np.ctypeslib.as_ctypes_type(np.dtype(dtype))*length.value).from_address(ptr));return a.copy()
 def run(self,rows,p=None,mask=None,seed=0,search=True,trace=False):
  rows=np.ascontiguousarray(rows,np.int32);p=None if p is None else np.ascontiguousarray(p,np.float64);mask=None if mask is None else np.ascontiguousarray(mask,np.uint8)
  assert (p is None)!=(mask is None)
  a=lambda x:None if x is None else x.ctypes.data
  self.check(self.lib.e33_run(self.ptr,a(rows),len(rows),a(p),a(mask),int(seed),search,trace))
  return self.output(rows)
 def static(self,rows,path):
  rows=np.ascontiguousarray(rows,np.int32);self.check(self.lib.e33_static(self.ptr,rows.ctypes.data,len(rows),str(path).encode()));return self.output(rows)
 def output(self,rows):
  names=['ids','entries','route_ndc','graph_ndc','actions','offsets','distances'];types=[np.int32,np.int32,np.uint32,np.uint32,np.int32,np.int32,np.float32]
  out={k:self.data(j,t) for j,(k,t) in enumerate(zip(names,types))}
  out['ids']=out['ids'].reshape(len(rows),10);out['distances']=out['distances'].reshape(len(rows),10);out['entries']=out['entries'].reshape(len(rows),3);out['rows']=rows.copy();return out
 def export(self,mask,path):
  mask=np.ascontiguousarray(mask,np.uint8);self.check(self.lib.e33_export(self.ptr,mask.ctypes.data,str(path).encode()))
 def parity(self,rows,mask,native=False):
  rows=np.ascontiguousarray(rows,np.int32);mask=np.ascontiguousarray(mask,np.uint8);self.check(self.lib.e33_parity(self.ptr,rows.ctypes.data,len(rows),mask.ctypes.data,native))
 @property
 def calls(self):return int(self.lib.e33_calls(self.ptr))
 @property
 def route_calls(self):return int(self.lib.e33_routes(self.ptr))
