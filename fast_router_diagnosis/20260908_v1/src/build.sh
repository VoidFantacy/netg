#!/usr/bin/env bash
set -euo pipefail
task_root=/data/netg/ACSG/fast_router_diagnosis/20260908_v1
repo_root=/data/netg/ACSG
task_source=${1:-"$task_root/src/fast_router_diagnosis.cpp"}
task_binary=${2:-"$task_root/bin/fast_router_diagnosis"}
c++ -std=c++17 -O3 -march=native -fopenmp -fPIC -Wall -Wextra \
  -I"$repo_root" -I"$repo_root/faiss" -I"$repo_root/benches" \
  -I"$repo_root/build/_deps/json-src/include" \
  "$task_source" \
  "$repo_root/build/faiss/faiss/libfaiss.a" \
  "$repo_root/build/ACSG/libACSG.a" \
  "$repo_root/build/MRNN_Descent/libmrnndescent.a" \
  "$repo_root/build/faiss/faiss/libfaiss.a" \
  /usr/lib/x86_64-linux-gnu/libopenblas.so -lm -ldl -lpthread \
  -o "$task_binary"
