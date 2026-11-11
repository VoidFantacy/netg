"""Read-only capacity estimate for the already-frozen dense configurations."""
import hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def main():
    assert (R/'primary_complete.json').exists() and (R/'dense_freeze.json').exists()
    t=time.perf_counter();cases=[];cumulative=0;peak=0;hashes=[]
    for d in json.loads((R/'dense_freeze.json').read_text())['decisions']:
        if not d['positive_points']:continue
        p=R/f"configs/{d['dataset']}.dense.json";c=json.loads(p.read_text());n=c['queries']['n'];raw=traces=access=uncompressed=points=0
        for k,ls in c['K_L'].items():
            K=int(k);completion=set(c['completion_L'][k])
            for L in ls:
                count=5 if L in completion else 1;points+=count;raw+=count*(8*n*K+24*n)
                if L in completion:
                    for method in ['REUSE-PQ','REUSE-SQ','MAIN-SQ']:
                        old=R/f"storage/results/{c['dataset']}/k{K}/{method}_L{L}/trace.i32.gz"
                        traces+=old.stat().st_size;uncompressed+=n*160*4;access+=n*5*8
        metadata=points*16384+2**20
        final=raw+traces+access+metadata
        peak=max(peak,cumulative+raw+uncompressed+access+metadata+min(uncompressed,16<<20))
        cumulative+=final
        cases.append(dict(dataset=c['dataset'],points=points,batches=3*points,actual_raw_packet_bytes=raw,
                          trace_gzip_bytes_predicted=traces,trace_uncompressed_bytes=uncompressed,
                          access_bytes=access,metadata_allowance_bytes=metadata,final_bytes_predicted=final))
        hashes.append(dict(path=str(p.resolve()),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    free=shutil.disk_usage('/').free;reserve=int(.7*2**30)
    v=dict(status='PASS_CAPACITY' if free-peak>=reserve else 'NEEDS_OWN_NEW_PACKET_LOSSLESS_ARCHIVE',
           free_bytes=free,reserve_bytes=reserve,predicted_final_bytes=cumulative,predicted_peak_extra_bytes=peak,
           predicted_free_at_peak=free-peak,datasets=cases,files=hashes,
           assumptions='Dense completion points repeat original K/L/models, so trace compressed sizes use original actual traces; metadata and transient gzip buffers are conservative. No models, configs, points or old evidence changed.',seconds=time.perf_counter()-t)
    (R/'reviews/storage_preflight.json').write_text(json.dumps(v,indent=2)+'\n')
    print(json.dumps({k:v[k] for k in ['status','free_bytes','predicted_final_bytes','predicted_peak_extra_bytes','predicted_free_at_peak']}),flush=True)
if __name__=='__main__':main()
