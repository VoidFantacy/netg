from shared import *
import ctypes as ct

class Native:
 def __init__(self,c):
  self.lib=ct.CDLL(str(O/'bin/environment.so'));l=self.lib
  l.e37_error.restype=ct.c_char_p;l.e37_create.argtypes=[ct.c_char_p];l.e37_create.restype=ct.c_void_p
  l.e37_destroy.argtypes=[ct.c_void_p]
  l.e37_build.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_size_t]
  l.e37_run.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_size_t,ct.c_int]
  l.e37_save.argtypes=[ct.c_void_p,ct.c_char_p]
  l.e37_verify.argtypes=[ct.c_void_p,ct.c_char_p,ct.c_void_p,ct.c_size_t]
  l.e37_data.argtypes=[ct.c_void_p,ct.c_int,ct.POINTER(ct.c_size_t)];l.e37_data.restype=ct.c_void_p
  l.e37_stat.argtypes=[ct.c_void_p,ct.c_int];l.e37_stat.restype=ct.c_uint64
  l.e37_build_seconds.argtypes=[ct.c_void_p];l.e37_build_seconds.restype=ct.c_double
  l.e46_route.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_size_t]
  l.e46_search.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_void_p,ct.c_size_t]
  l.e48_install.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_size_t]
  l.e48_verify_vectors.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_size_t]
  l.e48_installations.restype=ct.c_uint64
  self.ptr=l.e37_create(json.dumps(c).encode())
  if not self.ptr:raise RuntimeError(l.e37_error().decode())
 def close(self):
  if self.ptr:self.lib.e37_destroy(self.ptr);self.ptr=None
 def ok(self,status):
  if status:raise RuntimeError(self.lib.e37_error().decode())
 def data(self,field,dtype):
  n=ct.c_size_t();ptr=self.lib.e37_data(self.ptr,field,ct.byref(n))
  if n.value==0:return np.empty(0,dtype=dtype)
  return np.ctypeslib.as_array(ct.cast(ptr,ct.POINTER(np.ctypeslib.as_ctypes_type(np.dtype(dtype)))),shape=(n.value,)).copy()
 def build(self,w):
  w=np.ascontiguousarray(w,np.float32);self.ok(self.lib.e37_build(self.ptr,w.ctypes.data,w.size))
  return digest(self.data(5,np.int32))
 def run(self,rows,L=128):
  rows=np.ascontiguousarray(rows,np.int32);self.ok(self.lib.e37_run(self.ptr,rows.ctypes.data,len(rows),L))
  return dict(ids=self.data(0,np.int32).reshape(-1,10),distances=self.data(1,np.float32).reshape(-1,10),entries=self.data(2,np.int32).reshape(-1,3),route_ndc=self.data(3,np.uint32),graph_ndc=self.data(4,np.uint32))
 def save(self,path):self.ok(self.lib.e37_save(self.ptr,str(path).encode()))
 def verify(self,path,rows):
  rows=np.ascontiguousarray(rows,np.int32);self.ok(self.lib.e37_verify(self.ptr,str(path).encode(),rows.ctypes.data,len(rows)))
 def stats(self):
  return dict(NSG_calls=int(self.lib.e37_stat(self.ptr,0)),HNSW_calls=int(self.lib.e37_stat(self.ptr,1)),builds=int(self.lib.e37_stat(self.ptr,2)),actual_threads=int(self.lib.e37_stat(self.ptr,3)),build_seconds=float(self.lib.e37_build_seconds(self.ptr)))

 def route(self,rows):
  rows=np.ascontiguousarray(rows,np.int32);self.ok(self.lib.e46_route(self.ptr,rows.ctypes.data,len(rows)))
  return dict(entries=self.data(2,np.int32).reshape(-1,3),route_ndc=self.data(3,np.uint32))
 def search_entries(self,rows,entries):
  rows=np.ascontiguousarray(rows,np.int32);entries=np.ascontiguousarray(entries,np.int32);assert entries.shape==(len(rows),3)
  self.ok(self.lib.e46_search(self.ptr,rows.ctypes.data,entries.ctypes.data,len(rows)))
  return dict(ids=self.data(0,np.int32).reshape(-1,10),distances=self.data(1,np.float32).reshape(-1,10),graph_ndc=self.data(4,np.uint32))

 def install_topology(self,topology):
  topology=np.ascontiguousarray(topology,np.int32);self.ok(self.lib.e48_install(self.ptr,topology.ctypes.data,topology.size))
  return digest(self.data(5,np.int32))
 def installation_count(self):return int(self.lib.e48_installations())
 def verify_vectors(self,w):
  w=np.ascontiguousarray(w,np.float32);self.ok(self.lib.e48_verify_vectors(self.ptr,w.ctypes.data,w.size))
