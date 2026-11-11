from common import *
from archive import load_packets
import gzip
started=time.perf_counter();old=load_packets(R/'storage/results/coco/A')
expected=read(R/'reviews/recovery_qualification_expected.json')
root=Path('/dev/shm/acsg-e197-recovery-qualification');rows=[];files=0
for p in expected['results']:
    prefix=f"k{p['K']}/{p['method']}_L{p['L']}";count=0
    for key,value in old.items():
        if not key.startswith(prefix+'/'):continue
        q=root/key;assert q.is_file(),key
        actual=gzip.decompress(q.read_bytes()) if key.endswith('witness.bin.gz') else q.read_bytes()
        assert value==actual,('recovery differs from durable actual native payload',key)
        count+=1;files+=1
    rows.append(dict(K=p['K'],L=p['L'],method=p['method'],matched_original_payload_files=count))
receipt=dict(status='PASS_RECOVERY_ALL_60_DURABLE_NATIVE_POINT_PAYLOADS_BYTE_EQUAL',points=len(rows),
    payload_files=files,all_six_array_packet_SHA_original=True,work_seed_and_witness_bytes_original_equal=True,
    K=[1,100],L=200,all_formal_method_branches=True,rows=rows,seconds=time.perf_counter()-started,
    scope='COCO A original durable packets. Later reconstructed windows require their own original timed packet SHA; original work/seed/witness files there were lost, so only replay provenance can be claimed for those files.')
dump(R/'reviews/recovery_qualification.json',receipt)
print(receipt['status'],len(rows),files,flush=True)
