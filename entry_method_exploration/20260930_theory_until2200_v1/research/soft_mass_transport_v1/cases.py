"""Frozen synthetic inputs shared by two arithmetic implementations; no real data paths."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
os.sched_setaffinity(0,{0})
import itertools
import numpy as np
SEED=20260930163
def units(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-12)
def transport_cases():
    i=0
    for h,d,k,ta,tb,r in itertools.product((2,3,7),(1,3,5),(1,2,3,4),(.25,1.,4.),(.25,1.,4.),range(8)):
        rng=np.random.default_rng(SEED+i);B=units(rng.normal(size=(h,d)));x=units(rng.normal(size=(k,d)));y=units(rng.normal(size=(k,d)));v=units(rng.normal(size=(1,d)))
        yield i,x@B.T/ta,y@B.T/tb,v@B.T,i%81==0
        i+=1
def aggregate_cases():
    for i in range(512):
        rng=np.random.default_rng(SEED+10000+i)
        yield i,units(rng.normal(size=(8,5))),units(rng.normal(size=(7,5))),rng.normal(size=(8,7)),rng.normal(size=(8,7))
def score_cases():
    for i in range(512):
        rng=np.random.default_rng(SEED+20000+i);s=rng.normal(size=7);e=rng.normal(size=7)*(0.,.001,.05,.5,2.)[i%5]
        yield i,s,e
def hard_cases():
    for k in range(1,5):
        labels=list(itertools.product(range(3),repeat=k))
        for x,y in itertools.product(labels,repeat=2):yield k,x,y
