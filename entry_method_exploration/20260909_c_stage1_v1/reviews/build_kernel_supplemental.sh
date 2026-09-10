#!/usr/bin/env bash
set -euo pipefail
repo_root=/data/netg/ACSG
review_root="$repo_root/entry_method_exploration/20260909_c_stage1_v1/reviews"
test ! -e "$review_root/kernel_supplemental_v1"
c++ -std=c++17 -O3 -march=native -fopenmp -fPIC \
  -I"$repo_root" -I"$repo_root/faiss" -I"$repo_root/benches" \
  -I"$repo_root/build/_deps/json-src/include" \
  "$review_root/kernel_supplemental.cpp" \
  "$repo_root/build/faiss/faiss/libfaiss.a" \
  /usr/lib/x86_64-linux-gnu/libopenblas.so -lm -ldl -lpthread \
  -o "$review_root/kernel_supplemental_v1"
