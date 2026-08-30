set -e

DATASET="glove"
alpha=2.4
beta=1.2
rho=0.15
lambda=0.4
rejection=10
iterations=10

export OMP_NUM_THREADS=16
FN_RESULT="benches/outputs/${DATASET}/acosp_nsg_NDC.json"
./build/benches/bench_ACO_NDC \
    --alpha ${alpha} \
    --beta ${beta} \
    --rho ${rho} \
    --lambda ${lambda} \
    --rejection ${rejection}\
    --iterations ${iterations} \
    --dataset ${DATASET} \
    --fn_result ${FN_RESULT}