set -e

# 测试用参数，可根据需要调整
DATASET="test_dataset"
alpha=1.0
beta=1.0
rho=0.5
lambda=0.4
rejection=10
iterations=10

# 测试时可使用较少线程
export OMP_NUM_THREADS=16

# 测试结果输出到单独目录，避免覆盖正式结果
FN_RESULT="benches/outputs/${DATASET}/acosp_nsg_test.json"

# 执行测试版本的程序
./build/benches/bench_ACO_TEST \
    --alpha ${alpha} \
    --beta ${beta} \
    --rho ${rho} \
    --lambda ${lambda} \
    --rejection ${rejection} \
    --iterations ${iterations} \
    --dataset ${DATASET} \
    --fn_result ${FN_RESULT}