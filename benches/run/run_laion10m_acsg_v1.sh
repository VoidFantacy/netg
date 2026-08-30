#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
source .venv_cpu/bin/activate

dataset="laion10m_acsg_v1"
log_dir="logs/${dataset}"
start_stage="${START_STAGE:-0}"
end_stage="${END_STAGE:-2}"
mkdir -p "$log_dir" "indices/${dataset}_index"
exec 9>"${log_dir}/pipeline.lock"
if ! flock -n 9; then
  echo "another LAION pipeline owns ${log_dir}/pipeline.lock" >&2
  exit 1
fi
printf '%s\n' "$$" > "${log_dir}/pipeline.pid"

run_stage() {
  local stage="$1"
  shift
  echo "[$(date --iso-8601=seconds)] START ${stage}"
  /usr/bin/time -v -o "${log_dir}/${stage}.time.txt" "$@" \
    >"${log_dir}/${stage}.log" 2>&1
  echo "[$(date --iso-8601=seconds)] DONE ${stage}"
}

if (( start_stage <= 0 && end_stage >= 0 )); then
  run_stage download benches/run/download_laion10m_acsg_v1.sh
fi
if (( start_stage <= 1 && end_stage >= 1 )); then
  run_stage prepare python benches/run/prepare_laion10m_acsg_v1.py
fi
if (( start_stage <= 2 && end_stage >= 2 )); then
  run_stage build_nsg build/benches/bench_ACO \
    --alpha 1.4 --beta 2.2 --rho 0.15 --lambda 0.012 --rejection 10 --iterations 20 \
    --R 64 --L_build 100 --C 512 --dataset "$dataset" \
    --index_file "indices/${dataset}_index/acosp_nsg.json"
fi

echo "LAION_ACSG_PIPELINE_COMPLETE"
