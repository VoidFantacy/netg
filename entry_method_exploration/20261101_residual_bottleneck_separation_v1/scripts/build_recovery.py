from common import *
started=time.perf_counter();receipt=read(R/'reviews/decision_source_identity.json')
assert sha(receipt['formal_source'])==receipt['formal_source_sha256']
assert sha(receipt['audit_base'])==receipt['audit_base_sha256']
argv=read(R/'reviews/build_formal.json')['argv']
source=R/'src/recover_packets.cpp';binary=R/'storage/recover_packets'
argv=[str(source) if a==str(R/'src/benchmark.cpp') else str(binary) if a==str(R/'storage/formal_benchmark') else a for a in argv]
p=subprocess.run(argv,cwd=REPO,capture_output=True,text=True)
(R/'reviews/build_recovery.log').write_text(p.stdout+p.stderr)
dump(R/'reviews/build_recovery.json',dict(argv=argv,returncode=p.returncode,seconds=time.perf_counter()-started,
    source_sha256=sha(source),inherited_exact_formal_source=receipt,
    binary_sha256=sha(binary) if p.returncode==0 else None))
assert p.returncode==0,p.stderr[-6000:]
print('RECOVERY_BINARY_BUILT',flush=True)
