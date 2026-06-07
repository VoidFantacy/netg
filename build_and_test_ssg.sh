#!/bin/bash
# SSG 全流程 NETG Pipeline: 建图 → 蚁群(ACO) → DPC → 标签 → Router → 测试
# 用法: nohup bash build_and_test_ssg.sh > ssg_full_pipeline.log 2>&1 &
#       tail -f ssg_full_pipeline.log

cd /mnt/new/New/ACSG

SSG_BUILD="/mnt/new/New/ACSG/SSG/build/tests/test_ssg_index"
BENCH_ACO_TEST="./build/benches/bench_ACO_TEST"
BENCH_SSG="./build/benches/bench_ssg"
KPH_DPC="./build/benches/kph_dpc_clustering"
GEN_LABELS="./build/benches/bench_generate_labels"
TRAIN_ROUTER="python3 benches/run/train_router.py"
SSG_DIR="ssg_index"
mkdir -p "$SSG_DIR"

declare -a BUILD_TASKS=(
    "gist1M|benches/datasets/GIST1M/gist_base.fvecs|GATE/output_gist1M/knng.graph|${SSG_DIR}/gist1M.ssg|100|50|60"
    "sift10M|benches/datasets/SIFT10M/sift10m_base.fvecs|GATE/output_sift10M/knng.graph|${SSG_DIR}/sift10M.ssg|100|50|60"
    "deep10M|benches/datasets/DEEP10M/base.10M.fvecs|GATE/output_deep10M/knng.graph|${SSG_DIR}/deep10M.ssg|100|50|60"
    "yandex_t2i|benches/datasets/YandexT2I/base.10M.fvecs|GATE/output_yandex_t2i/knng.graph|${SSG_DIR}/yandex_t2i.ssg|100|50|60"
)

declare -A SSG_FILE_MAP
SSG_FILE_MAP["gist1M"]="${SSG_DIR}/gist1M.ssg"
SSG_FILE_MAP["sift10M"]="${SSG_DIR}/sift10M.ssg"
SSG_FILE_MAP["sift10M_skewed"]="${SSG_DIR}/sift10M.ssg"
SSG_FILE_MAP["deep10M"]="${SSG_DIR}/deep10M.ssg"
SSG_FILE_MAP["yandex_t2i"]="${SSG_DIR}/yandex_t2i.ssg"

declare -a TEST_DATASETS=("gist1M" "sift10M" "sift10M_skewed" "deep10M" "yandex_t2i")

# ===== ACO 参数配置（与 train.py 中对齐） =====
SIFT_ACO_PARAMS="--alpha 0.2 --beta 4.5 --rho 0.1 --lambda 0.5 --rejection 20 --iterations 25 --L 400"
DEEP_ACO_PARAMS="--alpha 0.01 --beta 10.0 --rho 0.15 --lambda 0.4 --rejection 20 --iterations 50 --L 400"

get_aco_params() {
    local ds="$1"
    case "$ds" in
        sift*) echo "$SIFT_ACO_PARAMS" ;;
        *)     echo "$DEEP_ACO_PARAMS" ;;
    esac
}

get_label_L() {
    local ds="$1"
    case "$ds" in
        sift*)     echo "100" ;;
        deep*)     echo "100" ;;
        yandex*)   echo "300" ;;
        gist*)     echo "500" ;;
        *)         echo "100" ;;
    esac
}

timer_start() { START_TIME=$(date +%s); }
timer_end() {
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    echo "⏱️  耗时: ${ELAPSED}s ($(( ELAPSED/60 ))m $(( ELAPSED%60 ))s)"
}

echo "===================================================="
echo " SSG 全流程 NETG Pipeline: $(date)"
echo "===================================================="
echo ""

# ══════════════════════════════════════════
# Phase 1: SSG 建图（多线程）
# ══════════════════════════════════════════
echo "═══ Phase 1: SSG 建图 ═══"
export OMP_NUM_THREADS=$(nproc)

for task in "${BUILD_TASKS[@]}"; do
    IFS='|' read -r ds base knng output L R A <<< "$task"
    if [ -f "$output" ]; then echo "✅ [$ds] SSG 图已存在，跳过"; continue; fi
    if [ ! -f "$base" ]; then echo "❌ [$ds] Base 不存在: $base"; continue; fi
    if [ ! -f "$knng" ]; then echo "❌ [$ds] KNNG 不存在: $knng"; continue; fi

    echo ""
    echo "🔨 [$ds] 建图开始 (L=$L R=$R Angle=$A)"
    timer_start
    $SSG_BUILD "$base" "$knng" "$L" "$R" "$A" "$output"
    timer_end
    if [ -f "$output" ]; then
        echo "✅ [$ds] 建图完成: $(ls -lh $output | awk '{print $5}')"
    else
        echo "❌ [$ds] 建图失败!"
    fi
done

# ══════════════════════════════════════════
# Phase 2: 蚁群训练 ACO on SSG（多线程）
# ══════════════════════════════════════════
echo ""
echo "═══ Phase 2: 蚁群训练 ACO on SSG (多线程) ═══"
export OMP_NUM_THREADS=$(nproc)
export MKL_NUM_THREADS=$(nproc)
export OPENBLAS_NUM_THREADS=$(nproc)

for ds in "${TEST_DATASETS[@]}"; do
    ssg_file="${SSG_FILE_MAP[$ds]}"
    if [ ! -f "$ssg_file" ]; then echo "⚠️ [$ds] SSG 索引不存在，跳过蚁群训练"; continue; fi

    acpg_dir="acpg/${ds}_ssg_index"
    acpg_file="${acpg_dir}/acpg_ssg.json"
    fn_result="${acpg_dir}/aco_result.json"
    mkdir -p "$acpg_dir"

    if [ -f "$acpg_file" ]; then echo "✅ [$ds] ACPG 已存在，跳过蚁群训练"; continue; fi

    aco_params=$(get_aco_params "$ds")

    echo ""
    echo "🐜 [$ds] 蚁群训练开始 (SSG 直通模式)"
    echo "   SSG: $ssg_file"
    echo "   输出: $acpg_file"
    echo "   参数: $aco_params"
    timer_start
    $BENCH_ACO_TEST \
        --index_file dummy \
        --ssg_file "$ssg_file" \
        --dataset "$ds" \
        --acpg_file "$acpg_file" \
        --fn_result "$fn_result" \
        --R 50 \
        $aco_params
    ret=$?
    timer_end
    if [ $ret -eq 0 ] && [ -f "$acpg_file" ]; then
        echo "✅ [$ds] 蚁群训练完成: $(ls -lh $acpg_file | awk '{print $5}')"
    else
        echo "❌ [$ds] 蚁群训练失败! (exit code: $ret)"
    fi
done

# ══════════════════════════════════════════
# Phase 3: DPC 聚类（多线程）
# ══════════════════════════════════════════
echo ""
echo "═══ Phase 3: DPC 聚类 ═══"
export OMP_NUM_THREADS=8

for ds in "${TEST_DATASETS[@]}"; do
    acpg_file="acpg/${ds}_ssg_index/acpg_ssg.json"
    dpc_dir="dpc/${ds}_ssg_results"
    dpc_file="${dpc_dir}/dpc_hierarchical_results.json"
    mkdir -p "$dpc_dir"

    if [ ! -f "$acpg_file" ]; then echo "⚠️ [$ds] ACPG 不存在，跳过 DPC"; continue; fi
    if [ -f "$dpc_file" ]; then echo "✅ [$ds] DPC 已存在，跳过"; continue; fi

    echo ""
    echo "📊 [$ds] DPC 聚类开始"
    timer_start
    $KPH_DPC \
        --acpg_file "$acpg_file" \
        --output_file "$dpc_file" \
        --num_threads 8
    ret=$?
    timer_end
    if [ $ret -eq 0 ] && [ -f "$dpc_file" ]; then
        echo "✅ [$ds] DPC 完成: $(ls -lh $dpc_file | awk '{print $5}')"
    else
        echo "❌ [$ds] DPC 失败! (exit code: $ret)"
    fi
done

# ══════════════════════════════════════════
# Phase 4: 生成训练标签（多线程）
# ══════════════════════════════════════════
echo ""
echo "═══ Phase 4: 生成训练标签 ═══"
export OMP_NUM_THREADS=16

for ds in "${TEST_DATASETS[@]}"; do
    acpg_file="acpg/${ds}_ssg_index/acpg_ssg.json"
    dpc_file="dpc/${ds}_ssg_results/dpc_hierarchical_results.json"
    label_dir="drl/${ds}_ssg_results"
    label_file="${label_dir}/topo_aware_labels.ivecs"
    mkdir -p "$label_dir"

    if [ ! -f "$acpg_file" ]; then echo "⚠️ [$ds] ACPG 不存在，跳过标签生成"; continue; fi
    if [ ! -f "$dpc_file" ]; then echo "⚠️ [$ds] DPC 不存在，跳过标签生成"; continue; fi
    if [ -f "$label_file" ]; then echo "✅ [$ds] 标签已存在，跳过"; continue; fi

    label_L=$(get_label_L "$ds")

    echo ""
    echo "🏷️ [$ds] 生成训练标签 (L=$label_L)"
    timer_start
    $GEN_LABELS \
        --dataset "$ds" \
        --index_file "$acpg_file" \
        --cluster_file "$dpc_file" \
        --output_file "$label_file" \
        --limit 30000 \
        --query_type acpg \
        --L "$label_L"
    ret=$?
    timer_end
    if [ $ret -eq 0 ] && [ -f "$label_file" ]; then
        size_mb=$(du -m "$label_file" | cut -f1)
        echo "✅ [$ds] 标签生成完成: ${size_mb}MB"
    else
        echo "❌ [$ds] 标签生成失败! (exit code: $ret)"
    fi
done

# ══════════════════════════════════════════
# Phase 5: 训练 Router（GPU）
# ══════════════════════════════════════════
echo ""
echo "═══ Phase 5: 训练 Router ═══"

# train_router.py 内部读 drl/{ds}_results/ 和 dpc/{ds}_results/
# SSG 版用的是 _ssg_results/，需要做软链接
for ds in "${TEST_DATASETS[@]}"; do
    # 处理 drl 目录
    ssg_label_dir="drl/${ds}_ssg_results"
    orig_label_dir="drl/${ds}_results"

    if [ ! -f "${ssg_label_dir}/topo_aware_labels.ivecs" ]; then
        echo "⚠️ [$ds] SSG 标签不存在，跳过 Router 准备"
        continue
    fi

    if [ -d "$orig_label_dir" ] && [ ! -L "$orig_label_dir" ]; then
        backup_dir="${orig_label_dir}_nsg_backup"
        if [ ! -d "$backup_dir" ]; then
            echo "📦 [$ds] 备份 NSG 版 drl 目录 → ${backup_dir}"
            mv "$orig_label_dir" "$backup_dir"
        fi
    fi
    if [ ! -e "$orig_label_dir" ]; then
        ln -sf "$(realpath $ssg_label_dir)" "$orig_label_dir"
        echo "🔗 [$ds] 软链接: $orig_label_dir → $ssg_label_dir"
    fi

    # 处理 dpc 目录
    ssg_dpc_dir="dpc/${ds}_ssg_results"
    orig_dpc_dir="dpc/${ds}_results"

    if [ ! -f "${ssg_dpc_dir}/dpc_hierarchical_results.json" ]; then continue; fi

    if [ -d "$orig_dpc_dir" ] && [ ! -L "$orig_dpc_dir" ]; then
        backup_dir="${orig_dpc_dir}_nsg_backup"
        if [ ! -d "$backup_dir" ]; then
            echo "📦 [$ds] 备份 NSG 版 dpc 目录 → ${backup_dir}"
            mv "$orig_dpc_dir" "$backup_dir"
        fi
    fi
    if [ ! -e "$orig_dpc_dir" ]; then
        ln -sf "$(realpath $ssg_dpc_dir)" "$orig_dpc_dir"
        echo "🔗 [$ds] 软链接: $orig_dpc_dir → $ssg_dpc_dir"
    fi

    # 【关键】把 SSG DPC 文件覆盖到 train_router.py 优先读取的 entry_points.json
    # 确保 bench_generate_labels 和 train_router.py 用同一份 hub 列表
    gp_dir="graph_processing/${ds}_results"
    ep_file="${gp_dir}/entry_points.json"
    mkdir -p "$gp_dir"
    if [ -f "$ep_file" ] && [ ! -f "${ep_file}.nsg_backup" ]; then
        cp "$ep_file" "${ep_file}.nsg_backup"
        echo "📦 [$ds] 备份 NSG 版 entry_points.json"
    fi
    cp "${ssg_dpc_dir}/dpc_hierarchical_results.json" "$ep_file"
    echo "📋 [$ds] 覆盖 entry_points.json ← SSG DPC (hub 列表对齐)"
done

echo ""
echo "🧠 训练 Router..."
$TRAIN_ROUTER

# ══════════════════════════════════════════
# Phase 6: SSG 搜索测试（单线程）
# ══════════════════════════════════════════
echo ""
echo "═══ Phase 6: SSG 搜索测试 (单线程) ═══"
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

for ds in "${TEST_DATASETS[@]}"; do
    ssg_file="${SSG_FILE_MAP[$ds]}"
    if [ ! -f "$ssg_file" ]; then echo "⚠️ [$ds] SSG 索引不存在，跳过"; continue; fi

    echo ""
    echo "########################################"
    echo "📦 [$ds] 测试开始"
    echo "########################################"

    outdir="test/${ds}_ssg_results"
    mkdir -p "$outdir"
    result_json="${outdir}/${ds}_ssg_report.json"

    cmd="$BENCH_SSG --dataset $ds --ssg_file $ssg_file --fn_result $result_json --num_runs 3"

    # 优先用 SSG 版 Router，回退到原有 Router
    trans_hubs=""
    trans_ids=""
    for try_dir in "drl/${ds}_ssg_results" "drl/${ds}_results"; do
        if [ -f "${try_dir}/transformed_hubs.bin" ] && [ -f "${try_dir}/transformed_hub_ids.bin" ]; then
            trans_hubs="${try_dir}/transformed_hubs.bin"
            trans_ids="${try_dir}/transformed_hub_ids.bin"
            break
        fi
    done

    if [ -n "$trans_hubs" ]; then
        cmd="$cmd --transformed_hubs $trans_hubs --transformed_ids $trans_ids"
        echo "🔗 [$ds] 已挂载 NETG Router (from: $(dirname $trans_hubs))"
    else
        echo "⚠️ [$ds] 无 Router，仅跑 SSG Baseline"
    fi

    timer_start
    eval "$cmd"
    timer_end
    echo "✅ [$ds] 结果: $result_json"
done

echo ""
echo "🎉 SSG 全流程 NETG Pipeline 完成! $(date)"
