import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parent
def main():
    original=(R/'run.py').read_text();before="hardcost=assign(abs(np.asarray([[.9,.1],[.1,.9]])[:,None,:]-.5).sum(2))";after="hardcost=assign(abs(np.asarray([[.9,.1],[.1,.9]])[:,None,:]-np.asarray([[.5,.5],[.5,.5]])[None,:,:]).sum(2))"
    assert original.count(before)==1 and not (R/'results.json').exists() and not (R/'all_comparisons.npz').exists()
    with (R/'run_v2.py').open('x') as f:f.write(original.replace(before,after,1))
    record={'unix':time.time(),'original_main_exit':1,'original_log':'../../logs/soft_mass_transport_v1.log','reason':'Fixed cancellation example accidentally made a 2x1 cost matrix using scalar 0.5; equal-K assignment requires 2x2. Explicit two-row comparison distribution restores the stated example.',
       'change':'One literal fixture expression only. Original theory, protocol, generator, numeric domains, counts, seeds, and tolerances unchanged. Full main rerun required; original failed run saved no numeric outputs.',
       'sources_sha256':{str(R/n):hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ['run_v2.py','execute_v2.py','prepare_correction_v2.py','config.locked.json']}}
    with (R/'correction_v2.locked.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
    print('FIXTURE_CORRECTION_V2_FROZEN')
if __name__=='__main__':main()
