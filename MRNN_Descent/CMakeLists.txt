# 全局强制开启位置无关代码（双重保险，确保所有源文件都生效）
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

add_library(mrnndescent IndexMRNNDescent.cpp MRNNDescent.cpp)

# 显式添加 -fPIC 选项（直接关联到 mrnndescent 目标，优先级最高）
target_compile_options(mrnndescent PRIVATE -fPIC)

target_include_directories(mrnndescent PUBLIC
    $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}>
)

target_compile_definitions(mrnndescent PRIVATE FINTEGER=int)

find_package(OpenMP REQUIRED)
target_link_libraries(mrnndescent PUBLIC OpenMP::OpenMP_CXX)

target_link_libraries(mrnndescent PUBLIC faiss)