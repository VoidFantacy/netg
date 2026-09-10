# Source this file; it only changes the current shell environment.
export ACSG_HTS_ROOT=/data/netg/ACSG/hierarchical_target_search/20260907_v1
export ACSG_HTS_PYTHON=/data/netg/ACSG/.venv_cpu/bin/python
export ACSG_HTS_BASELINE_PYTHON="$ACSG_HTS_ROOT/tools/python/bin/python"
export METIS_ROOT="$ACSG_HTS_ROOT/tools/local"
export PATH="$METIS_ROOT/bin:/data/netg/ACSG/.venv_cpu/bin:$PATH"
export LD_LIBRARY_PATH="$METIS_ROOT/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
# MKL is intentionally enabled only in the RoarGraph-specific environment.
export HF_HUB_OFFLINE=1
export HF_HUB_DISABLE_TELEMETRY=1
export DO_NOT_TRACK=1
