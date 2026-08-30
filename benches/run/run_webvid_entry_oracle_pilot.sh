#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

out_dir="oracle_entry_diagnostics/webvid_validation_1k_current_hubs_v1"
mkdir -p "$out_dir"

exec build/benches/bench_entry_oracle \
  --dataset webvid2_5m_light_v1 \
  --index_file indices/webvid2_5m_light_v1_index/acosp_nsg.json \
  --candidate_ids fast_entry_variants/webvid2_5m_light_v1_seed20260828/qgt_cover_hub_ids.bin \
  --prototype_hubs fast_entry_variants/webvid2_5m_light_v1_seed20260828/qgt_gt_basin_prototype_hubs.bin \
  --prototype_ids fast_entry_variants/webvid2_5m_light_v1_seed20260828/qgt_cover_hub_ids.bin \
  --output_file "$out_dir/results.json" \
  --query_type validation \
  --max_queries 1000 \
  --search_Ls 64,128,200,400 \
  --top_ks 1,10,100 \
  --num_runs 3 \
  --threads 16
