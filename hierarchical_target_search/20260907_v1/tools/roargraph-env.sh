# Source only for the isolated RoarGraph / DiskANN tools.
source /data/netg/ACSG/hierarchical_target_search/20260907_v1/tools/env.sh
export MKL_ROOT="$ACSG_HTS_ROOT/tools/mkl"
export OMP_PATH="$ACSG_HTS_ROOT/tools/mkl-sysroot/usr/lib/llvm-14/lib"
export LD_LIBRARY_PATH="$MKL_ROOT/lib/intel64:$OMP_PATH:$LD_LIBRARY_PATH"
