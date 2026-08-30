set -e

DATASET="deep"
alpha=2.2
beta=1.4
rho=0.15
lambda=0.4
rejection=10
iterations=20

export OMP_NUM_THREADS=16
FN_RESULT="benches/outputs/${DATASET}/acosp_nsg_v1.json"
./build/benches/bench_ACO \
    --alpha ${alpha} \
    --beta ${beta} \
    --rho ${rho} \
    --lambda ${lambda} \
    --rejection ${rejection}\
    --iterations ${iterations} \
    --dataset ${DATASET} \
    --fn_result ${FN_RESULT}