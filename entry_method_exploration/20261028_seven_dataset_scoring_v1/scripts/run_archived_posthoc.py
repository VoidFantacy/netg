"""Storage-only adapter; run the unchanged, bound scientific diagnostic."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
import runpy
from pathlib import Path
import numpy as np
import io_data
from packet_archive import read_bytes
original=io_data.read_array
def archived_array(path,dtype):
    p=Path(path)
    if p.exists() or Path(str(p)+'.gz').exists():return original(p,dtype)
    return np.frombuffer(read_bytes(p),dtype=dtype).copy()
io_data.read_array=archived_array
runpy.run_path(str(Path(__file__).with_name('posthoc_scoring.py')),run_name='__main__')
