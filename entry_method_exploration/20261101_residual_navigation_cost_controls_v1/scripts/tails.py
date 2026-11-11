from common import *
t=time.perf_counter();h=np.load(OLD/'analysis/query_hits.npz');rows=[]
methods=['B32','ONEHOP96','DIST96','DIST384','NOVEL96','NOVEL384','REP384','REUSE-SQ']
for ds in DS:
 for w in ['A','B']:
  for L in [100,200,400]:
   g=h[f'{ds}|{w}|100|{L}|GT10'];b=h[f'{ds}|{w}|100|{L}|B32']
   for m in methods:
    f=h[f'{ds}|{w}|100|{L}|{m}'];gbad=g<10;bbad=b<10
    rows.append(dict(dataset=ds,window=w,K=100,L=L,method=m,n=len(f),GT_failed=int(gbad.sum()),B32_failed=int(bbad.sum()),method_failed=int((f<10).sum()),GT_failed_improved=int((gbad&(f>g)).sum()),GT_failed_escaped=int((gbad&(f>=10)).sum()),B32_failed_improved=int((bbad&(f>b)).sum()),B32_failed_escaped=int((bbad&(f>=10)).sum()),new_failure_vs_B32=int(((~bbad)&(f<10)).sum()),scope='E195 actual timed query hits; same packets for E196 remeasured methods; zero failure denominator gives no repair-rate evidence'))
csvwrite(R/'analysis/severe_tail_transitions.csv',rows);dump(R/'analysis/tail_receipt.json',dict(status='PASS_EXACT_PAIRED_LT10_TRANSITIONS',rows=len(rows),seconds=time.perf_counter()-t,source_sha=sha(OLD/'analysis/query_hits.npz'),threshold='0-9 hits out of100; exactly10 excluded'))
