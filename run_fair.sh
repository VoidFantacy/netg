#!/bin/bash
# Fair A/B comparison: W-DPC vs HBKM hubs
# Interleaved runs, same time window, no Python subprocess issues
set -e
cd /mnt/lost+found/ACSG

EXE="./build/benches/test"
SEARCH_LS="100,300,600,1200,1500"
TOP_K=100
N_ROUNDS=5
COOLDOWN=5
TMPDIR="test_fair_tmp"
rm -rf "$TMPDIR"
mkdir -p "$TMPDIR"

DATASETS="deep10M sift10M sift10M_skewed yandex_t2i gist1M"

echo "[Fair Compare] START $(date)"
echo "[Fair Compare] N_ROUNDS=$N_ROUNDS, SEARCH_LS=$SEARCH_LS, TOP_K=$TOP_K"

for ds in $DATASETS; do
    echo ""
    echo "======================================================================"
    echo "  Dataset: $ds"
    echo "======================================================================"

    ACPG="acpg/${ds}_index/acpg_nsg.json"
    WDPC_HUBS="drl/${ds}_results/raw_hubs.bin"
    WDPC_IDS="drl/${ds}_results/transformed_hub_ids.bin"
    HBKM_HUBS="drl/${ds}_results/raw_hubs_hbkm.bin"
    HBKM_IDS="drl/${ds}_results/transformed_hub_ids_hbkm.bin"

    # Check files exist
    for f in "$ACPG" "$WDPC_HUBS" "$WDPC_IDS" "$HBKM_HUBS" "$HBKM_IDS"; do
        if [ ! -f "$f" ]; then
            echo "  [SKIP] missing $f"
            continue 2
        fi
    done

    for r in $(seq 0 $((N_ROUNDS-1))); do
        # Alternate order each round
        if [ $((r % 2)) -eq 0 ]; then
            ORDER="wdpc hbkm"
        else
            ORDER="hbkm wdpc"
        fi

        for method in $ORDER; do
            if [ "$method" = "wdpc" ]; then
                HUBS="$WDPC_HUBS"
                IDS="$WDPC_IDS"
            else
                HUBS="$HBKM_HUBS"
                IDS="$HBKM_IDS"
            fi

            REPORT="$TMPDIR/${ds}_${method}_r${r}.json"
            echo -n "  Round $((r+1))/$N_ROUNDS $method ... "

            $EXE \
                --dataset "$ds" \
                --acpg_file "$ACPG" \
                --fn_result "$REPORT" \
                --test_scope routing \
                --num_runs 1 \
                --R 32 \
                --raw_hubs "$HUBS" \
                --transformed_ids "$IDS" \
                --search_Ls "$SEARCH_LS" \
                --top_k $TOP_K \
                > /dev/null 2>&1

            if [ -f "$REPORT" ]; then
                echo "ok"
            else
                echo "FAILED"
            fi
            sleep $COOLDOWN
        done
    done
done

echo ""
echo "[Fair Compare] ALL DONE $(date)"
echo "[Fair Compare] Results in $TMPDIR/"
ls -la "$TMPDIR/"
