#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

source_dir="${LAION_SOURCE_DIR:-benches/datasets/LAION10M_acsg_v1/source}"
mkdir -p "$source_dir"

laion_root="https://deploy.laion.ai/8f83b608504d46bb81708ec86e912220/embeddings"
zenodo_root="https://zenodo.org/records/11090378/files"
shard_bytes=1024458880

download_exact() {
  local url="$1"
  local output="$2"
  local expected_bytes="$3"
  local part="${output}.part"

  if [[ -f "$output" ]] && [[ "$(stat -c %s "$output")" == "$expected_bytes" ]]; then
    echo "reuse $output"
    return
  fi
  if [[ -f "$output" ]]; then
    echo "refusing unexpected existing file: $output" >&2
    exit 1
  fi

  curl --fail --location --retry 20 --retry-all-errors --continue-at - \
    --output "$part" "$url"
  local actual_bytes
  actual_bytes="$(stat -c %s "$part")"
  if [[ "$actual_bytes" != "$expected_bytes" ]]; then
    echo "size mismatch for $part: $actual_bytes != $expected_bytes" >&2
    exit 1
  fi
  mv "$part" "$output"
}

# RoarGraph's published LAION-10M contract deliberately skips shard 8 and
# concatenates shards 0..7,9,10.  Each source NPY contains 1,000,448 fp16 rows.
for shard in 0 1 2 3 4 5 6 7 9 10; do
  download_exact \
    "$laion_root/img_emb/img_emb_${shard}.npy" \
    "$source_dir/img_emb_${shard}.npy" \
    "$shard_bytes"
done

# ACSG needs 45K independent historical queries, not RoarGraph's full 10M
# training workload.  One official 1,000,448-row text shard is sufficient;
# the preparation stage samples, deduplicates, and physically separates it.
download_exact \
  "$laion_root/text_emb/text_emb_0.npy" \
  "$source_dir/text_emb_0.npy" \
  "$shard_bytes"

download_exact \
  "$zenodo_root/laion.query.10k.fbin?download=1" \
  "$source_dir/laion.query.10k.fbin" \
  20480008
download_exact \
  "$zenodo_root/laion.gt.10k.ibin?download=1" \
  "$source_dir/laion.gt.10k.ibin" \
  40000008

printf '%s  %s\n' af1343dc16554d87c43326cf4024493d \
  "$source_dir/laion.query.10k.fbin" | md5sum --check -
printf '%s  %s\n' d76a89a9e05ce4a18a5ebdaa3e159796 \
  "$source_dir/laion.gt.10k.ibin" | md5sum --check -

echo "LAION_ACSG_DOWNLOAD_COMPLETE"
