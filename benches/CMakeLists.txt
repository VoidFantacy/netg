cmake_minimum_required(VERSION 3.15)

# ==============================================================================
# 1. 终极拦截：跳过CUDA启用
# ==============================================================================
function(enable_language)
    set(lang ${ARGV0})
    if(lang STREQUAL "CUDA")
        message(STATUS "⚠️  拦截faiss的CUDA启用请求，强制使用CPU模式")
        return()
    endif()
    _enable_language(${ARGV})
endfunction()

# 强制PIC设置
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
if(UNIX)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC -Wall -Wextra")
endif()

project(ACSG_Benchmarks)

# 设置C++标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ==============================================================================
# 2. 基础依赖配置
# ==============================================================================
set(FAISS_ENABLE_GPU OFF CACHE BOOL "Force disable FAISS GPU" FORCE)
set(FAISS_NO_CUDA ON CACHE BOOL "Force FAISS no CUDA" FORCE)
set(BUILD_WITH_GPU OFF CACHE BOOL "Force disable GPU build" FORCE)
set(CUDA_FOUND FALSE CACHE BOOL "CUDA not available" FORCE)

message(STATUS "✅ 已拦截CUDA启用，强制FAISS使用CPU模式")

set(FAISS_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../faiss")
message(STATUS "Using FAISS from: ${FAISS_ROOT}")

include_directories(
    ${FAISS_ROOT}
    ${FAISS_ROOT}/faiss
    ${FAISS_ROOT}/faiss/impl
    ${FAISS_ROOT}/faiss/cpu
)
link_directories(
    ${FAISS_ROOT}/faiss/impl
    ${FAISS_ROOT}/faiss/cpu
)

find_package(OpenMP REQUIRED)

# ==============================================================================
# 3. 第三方库
# ==============================================================================
include(FetchContent)

FetchContent_Declare(
    argparse
    GIT_REPOSITORY https://github.com/p-ranav/argparse.git
    GIT_TAG v2.9
)
FetchContent_MakeAvailable(argparse)

FetchContent_Declare(
    json
    URL https://github.com/nlohmann/json/releases/download/v3.11.2/json.tar.xz
)
FetchContent_MakeAvailable(json)

FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG v2.11.1
)
FetchContent_MakeAvailable(pybind11)



# ==============================================================================
# 5. 定义构建目标
# ==============================================================================

macro(setup_target target_name)
    target_include_directories(${target_name} PUBLIC
        $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}>
        ${FAISS_ROOT}
    )
    target_link_libraries(${target_name}
        faiss
        ACSG
        OpenMP::OpenMP_CXX
        argparse
        nlohmann_json::nlohmann_json
    )
    target_compile_features(${target_name} PRIVATE cxx_std_17)
    target_compile_options(${target_name} PRIVATE -Wall -Wextra -O3 -march=native)
endmacro()

# --- 基础目标 ---
add_executable(bench_ACO bench_ACO.cpp)
setup_target(bench_ACO)

add_executable(bench_ACO_NDC bench_ACO_NDC.cpp)
setup_target(bench_ACO_NDC)

add_executable(bench_ACO_TEST bench_ACO_TEST.cpp)
setup_target(bench_ACO_TEST)

add_executable(kph_dpc_clustering kph_dpc_clustering.cpp)
setup_target(kph_dpc_clustering)

add_executable(bench_generate_labels bench_generate_labels.cpp)
setup_target(bench_generate_labels)

# --- [新增] 神经建图数据生成器 ---
add_executable(bench_generate_graph_train_data bench_generate_graph_train_data.cpp)
setup_target(bench_generate_graph_train_data)
target_include_directories(bench_generate_graph_train_data PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/benches>)

# --- [修改] 图处理器 (合并了ONNX支持) ---
add_executable(graph_processor graph_processor.cpp)
setup_target(graph_processor)
if(ONNXRUNTIME_FOUND)
    target_compile_definitions(graph_processor PRIVATE USE_ONNXRUNTIME)
    target_include_directories(graph_processor PRIVATE ${ONNXRUNTIME_INCLUDE_DIR})
    target_link_libraries(graph_processor ${ONNXRUNTIME_LIBRARY})
endif()

# --- 测试程序 ---
add_executable(test test.cpp)
setup_target(test)
target_include_directories(test PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/benches>)
if(ONNXRUNTIME_FOUND)
    target_compile_definitions(test PRIVATE USE_ONNXRUNTIME)
    target_include_directories(test PRIVATE ${ONNXRUNTIME_INCLUDE_DIR})
    target_link_libraries(test ${ONNXRUNTIME_LIBRARY})
endif()

# --- Hop 统计测试（Recall / Memory / Hops，不统计 QPS）---
add_executable(test_hop test_hop.cpp)
setup_target(test_hop)
target_include_directories(test_hop PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/benches>)

# --- NETG on SSG：验证框架图索引通用性 ---
set(SSG_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../SSG")
set(SSG_LIB  "${SSG_ROOT}/build/src/libssg.a")
find_package(Boost REQUIRED)

add_executable(bench_ssg bench_ssg.cpp)
setup_target(bench_ssg)
target_include_directories(bench_ssg PUBLIC
    ${SSG_ROOT}/include
    ${Boost_INCLUDE_DIRS}
)
target_link_libraries(bench_ssg
    ${SSG_LIB}
    ${Boost_LIBRARIES}
    OpenMP::OpenMP_CXX
)
target_compile_options(bench_ssg PRIVATE -march=native -O3)

# --- Python 模块 ---
pybind11_add_module(graph_eval graph_eval.cpp)
target_include_directories(graph_eval PUBLIC
    ${FAISS_ROOT}
    ${PROJECT_SOURCE_DIR}
    ${PROJECT_SOURCE_DIR}/utils
    ${PROJECT_SOURCE_DIR}/benches
)
target_link_libraries(graph_eval PRIVATE
    pybind11::module
    faiss
    ACSG
    OpenMP::OpenMP_CXX
    nlohmann_json::nlohmann_json
)
target_compile_features(graph_eval PRIVATE cxx_std_17)
target_compile_options(graph_eval PRIVATE -O3 -fopenmp -march=native)
target_link_options(graph_eval PRIVATE -fopenmp)
set_target_properties(graph_eval PROPERTIES PREFIX "")


# --- Per-Query Recall Distribution Benchmark ---
add_executable(bench_per_query_recall bench_per_query_recall.cpp)
setup_target(bench_per_query_recall)
target_include_directories(bench_per_query_recall PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/benches>)

# Read-only validation oracle for frozen-graph entry headroom.
add_executable(bench_entry_oracle bench_entry_oracle.cpp)
setup_target(bench_entry_oracle)
target_include_directories(bench_entry_oracle PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/benches>)

# Deployment-faithful target-basin router with separate count/timing modes.
add_executable(bench_target_basin_eval bench_target_basin_eval.cpp)
setup_target(bench_target_basin_eval)
target_include_directories(bench_target_basin_eval PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/benches>)

# Read-only finite-beam expansion diagnostics for the frozen-graph entry layer.
add_executable(bench_finite_beam_trace bench_finite_beam_trace.cpp)
setup_target(bench_finite_beam_trace)
target_include_directories(bench_finite_beam_trace PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/benches>)

# Lossless frozen-graph adapter for GATE's standard variable-degree NSG format.
add_executable(export_gate_nsg export_gate_nsg.cpp)
setup_target(export_gate_nsg)

# Read-only coarse transition graph over QGT hub basins on a frozen NSG.
add_executable(build_basin_transition_graph build_basin_transition_graph.cpp)
setup_target(build_basin_transition_graph)

# --- HNSW 基准测试 ---
add_executable(bench_hnsw bench_hnsw.cpp)
setup_target(bench_hnsw)

# Isolated frozen-graph regional search: legacy code paths are unchanged.
add_executable(test_regional_search test_regional_search.cpp)
setup_target(test_regional_search)

# Isolated pure-wall evaluator for the hierarchical target search protocol.
add_executable(bench_hierarchical_eval bench_hierarchical_eval.cpp)
setup_target(bench_hierarchical_eval)
target_include_directories(bench_hierarchical_eval PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/benches>)

# Versioned P3 structure/portal diagnostic evaluator; P2 target stays unchanged.
add_executable(bench_hierarchical_eval_p3 bench_hierarchical_eval_p3.cpp)
setup_target(bench_hierarchical_eval_p3)
target_include_directories(bench_hierarchical_eval_p3 PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/benches>)

# Fit-only P3 portal probes; no default routing or changes to legacy methods.
add_executable(bench_hierarchical_portals bench_hierarchical_portals.cpp)
setup_target(bench_hierarchical_portals)
target_include_directories(bench_hierarchical_portals PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/benches>)
