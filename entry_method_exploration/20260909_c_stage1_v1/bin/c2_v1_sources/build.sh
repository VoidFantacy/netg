#!/usr/bin/env bash
set -euo pipefail
repo_root=/data/netg/ACSG
task_root="$repo_root/entry_method_exploration/20260909_c_stage1_v1"
task_name=${1:?target source basename required}
task_output=${2:-"$task_root/bin/$task_name"}
test ! -e "$task_output"
c++ -std=c++17 -O3 -march=native -fopenmp -fPIC -Wall -Wextra \
  -I"$repo_root" -I"$repo_root/faiss" -I"$repo_root/benches" \
  -I"$repo_root/build/_deps/json-src/include" \
  "$task_root/src/$task_name.cpp" "$repo_root/ACSG/ACSG.cpp" \
  "$repo_root/build/faiss/faiss/libfaiss.a" "$repo_root/build/ACSG/libACSG.a" \
  "$repo_root/build/MRNN_Descent/libmrnndescent.a" "$repo_root/build/faiss/faiss/libfaiss.a" \
  /usr/lib/x86_64-linux-gnu/libopenblas.so -lm -ldl -lpthread -o "$task_output"
