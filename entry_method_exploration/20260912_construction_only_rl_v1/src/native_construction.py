from native_factorial import Native as FactorialNative
from shared import *

class Native(FactorialNative):
 def __init__(self,c):
  super().__init__(c)
  self.score_P=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim'])
  self.construction_calls=0;self.score_vector_verifications=0
 def build(self,construction_W):
  topology_sha=super().build(construction_W)
  topology=self.data(5,np.int32)
  super().build(self.score_P)
  assert self.install_topology(topology)==topology_sha
  self.verify_vectors(self.score_P)
  self.construction_calls+=1;self.score_vector_verifications+=1
  return topology_sha
 def stats(self):
  return dict(super().stats(),construction_calls=self.construction_calls,topology_installations=self.installation_count(),score_vector_verifications=self.score_vector_verifications)
