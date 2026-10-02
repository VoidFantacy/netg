from common import *
import ctypes as ct
class Routes:
 def __init__(self,c):
  self.lib=ct.CDLL(str(E89/'bin/routes.so'));l=self.lib;l.e89_error.restype=ct.c_char_p;l.e89_create.argtypes=[ct.c_char_p];l.e89_create.restype=ct.c_void_p;l.e89_destroy.argtypes=[ct.c_void_p];l.e89_run.argtypes=[ct.c_void_p,ct.c_int,ct.c_size_t];l.e89_data.argtypes=[ct.c_void_p,ct.c_int,ct.POINTER(ct.c_size_t)];l.e89_data.restype=ct.c_void_p;l.e89_calls.argtypes=[ct.c_void_p];l.e89_calls.restype=ct.c_uint64
  self.ptr=l.e89_create(json.dumps(c).encode());assert self.ptr,l.e89_error().decode();self.n=c['num_queries']
 def run(self,hub=-1,n=None):
  n=self.n if n is None else n
  if self.lib.e89_run(self.ptr,hub,n):raise RuntimeError(self.lib.e89_error().decode())
  out={}
  for j,(name,dt,w) in enumerate([('entries',np.int32,3),('slots',np.int32,7),('slot_distances',np.float32,7),('route_ndc',np.uint32,1)]):
   count=ct.c_size_t();p=self.lib.e89_data(self.ptr,j,ct.byref(count));a=np.ctypeslib.as_array(ct.cast(p,ct.POINTER(np.ctypeslib.as_ctypes_type(np.dtype(dt)))),shape=(count.value,)).copy();out[name]=a[:n*w].reshape(n,w) if w>1 else a[:n]
  return out
 def calls(self):return int(self.lib.e89_calls(self.ptr))
 def close(self):
  if self.ptr:self.lib.e89_destroy(self.ptr);self.ptr=None
