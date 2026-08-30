set -e

DATASET="sift100K"
M=32
efConstruction=500

export OMP_NUM_THREADS=16
FN_RESULT="benches/outputs/${DATASET}/hnsw.json"
./build/benches/bench_hnsw \
    --M ${M} \
    --efConstruction ${efConstruction} \
    --dataset ${DATASET} \
    --fn_result ${FN_RESULT}
