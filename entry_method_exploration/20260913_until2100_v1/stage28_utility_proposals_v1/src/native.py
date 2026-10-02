from common import *
import ctypes as ct
class Native:
 def __init__(self,c):
  self.lib=ct.CDLL(str(C/'stage10_exact_triple_utility_v1/bin/inject.so'));l=self.lib
  l.e37_error.restype=ct.c_char_p;l.e37_create.argtypes=[ct.c_char_p];l.e37_create.restype=ct.c_void_p;l.e37_destroy.argtypes=[ct.c_void_p]
  l.e46_search.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_void_p,ct.c_size_t]
  l.e69_search.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_void_p,ct.c_size_t,ct.c_int]
  l.e37_data.argtypes=[ct.c_void_p,ct.c_int,ct.POINTER(ct.c_size_t)];l.e37_data.restype=ct.c_void_p
  l.e37_stat.argtypes=[ct.c_void_p,ct.c_int];l.e37_stat.restype=ct.c_uint64
  self.ptr=l.e37_create(json.dumps(c).encode());assert self.ptr,l.e37_error().decode()
 def close(self):
  if self.ptr:self.lib.e37_destroy(self.ptr);self.ptr=None
 def stats(self):return dict(zip(['NSG','HNSW','builds','actual_threads'],[int(self.lib.e37_stat(self.ptr,k)) for k in range(4)]))
 def data(self,field,dt):
  n=ct.c_size_t();ptr=self.lib.e37_data(self.ptr,field,ct.byref(n))
  if not n.value:return np.empty(0,dt)
  return np.ctypeslib.as_array(ct.cast(ptr,ct.POINTER(np.ctypeslib.as_ctypes_type(np.dtype(dt)))),shape=(n.value,)).copy()
 def search(self,rows,entries,mode):
  rows=np.ascontiguousarray(rows,np.int32);entries=np.ascontiguousarray(entries,np.int32);assert entries.shape==(len(rows),3)
  if mode=='count':status=self.lib.e46_search(self.ptr,rows.ctypes.data,entries.ctypes.data,len(rows))
  else:status=self.lib.e69_search(self.ptr,rows.ctypes.data,entries.ctypes.data,len(rows),int(mode=='reference'))
  if status:raise RuntimeError(self.lib.e37_error().decode())
  return dict(ids=self.data(0,np.int32).reshape(-1,10),distances=self.data(1,np.float32).reshape(-1,10),graph_ndc=self.data(4,np.uint32))
