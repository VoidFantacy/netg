"""Dependency installation verification only: no project data, fitting, or ANN evaluation."""
import importlib
import json
import os
import sys
from pathlib import Path

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['MPLBACKEND'] = 'Agg'
modules = ['numpy', 'scipy', 'torch', 'faiss', 'hnswlib', 'sklearn',
           'matplotlib', 'pandas', 'networkx', 'gensim', 'h5py',
           'transformers', 'prettytable']
versions = {}
for name in modules:
    module = importlib.import_module(name)
    versions[name] = {'version': getattr(module, '__version__', None), 'file': module.__file__}

import numpy as np
import torch
import faiss
from scipy.optimize import minimize
from transformers import HfArgumentParser
import h5py

torch.set_num_threads(1)
x = torch.tensor([2.0], requires_grad=True)
(x * x).sum().backward()
assert x.grad.item() == 4.0
result = minimize(lambda v: (v[0] - 3) ** 2, np.array([0.]), method='L-BFGS-B')
assert result.success and abs(result.x[0] - 3) < 1e-4
with h5py.File('dependency_memory_only.h5', 'w', driver='core', backing_store=False) as store:
    store['check'] = np.arange(4)
    assert list(store['check'][:]) == [0, 1, 2, 3]

# Import the published model definition and run one synthetic CPU forward pass.
baseline = Path(__file__).resolve().parents[1] / 'tools' / 'LIRA'
sys.path.insert(0, str(baseline))
from model_probing import MLP_2_Input
model = MLP_2_Input(input_dim1=4, input_dim2=8, output_dim=4).eval()
with torch.no_grad():
    output = model(torch.zeros((2, 4)), torch.zeros((2, 8)))
assert output.shape == (2, 4) and torch.isfinite(output).all()
print(json.dumps({'status': 'PASS', 'python': sys.executable, 'modules': versions,
                  'checks': ['imports', 'torch_cpu_autograd', 'scipy_lbfgs', 'hdf5_in_memory', 'lira_cpu_forward'],
                  'project_queries_loaded': False, 'research_experiments_run': False}, indent=2))
