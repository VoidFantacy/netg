from common import *
import ctypes as ct
class Routes:
 def __init__(self,c):
  self.lib=ct.CDLL(str(O/'bin/routes.so'));l=self.lib;l.e86_error.restype=ct.c_char_p;l.e86_create.argtypes=[ct.c_char_p];l.e86_create.restype=ct.c_void_p;l.e86_destroy.argtypes=[ct.c_void_p];l.e86_run.argtypes=[ct.c_void_p,ct.c_int,ct.c_int];l.e86_data.argtypes=[ct.c_void_p,ct.c_int,ct.POINTER(ct.c_size_t)];l.e86_data.restype=ct.c_void_p;l.e86_calls.argtypes=[ct.c_void_p];l.e86_calls.restype=ct.c_uint64
  self.ptr=l.e86_create(json.dumps(c).encode());assert self.ptr,l.e86_error().decode();self.n=c['num_queries']
 def run(self,s=-1,t=-1):
  if self.lib.e86_run(self.ptr,s,t):raise RuntimeError(self.lib.e86_error().decode())
  out={}
  for j,(name,dt,w) in enumerate([('entries',np.int32,3),('slots',np.int32,7),('slot_distances',np.float32,7),('route_ndc',np.uint32,1)]):
   n=ct.c_size_t();p=self.lib.e86_data(self.ptr,j,ct.byref(n));a=np.ctypeslib.as_array(ct.cast(p,ct.POINTER(np.ctypeslib.as_ctypes_type(np.dtype(dt)))),shape=(n.value,)).copy();out[name]=a.reshape(self.n,w) if w>1 else a
  return out
 def calls(self):return int(self.lib.e86_calls(self.ptr))
 def close(self):
  if self.ptr:self.lib.e86_destroy(self.ptr);self.ptr=None
