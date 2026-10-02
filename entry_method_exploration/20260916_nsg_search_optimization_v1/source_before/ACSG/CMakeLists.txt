add_library(ACSG IndexACSG.cpp ACSG.cpp)

# 关键：为 ACSG 静态库添加 -fPIC 选项（解决共享库链接错误）
target_compile_options(ACSG PRIVATE -fPIC)

target_include_directories(ACSG PUBLIC
    $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}>
)

target_compile_definitions(ACSG PRIVATE FINTEGER=int)

find_package(OpenMP REQUIRED)
target_link_libraries(ACSG PUBLIC OpenMP::OpenMP_CXX)

target_link_libraries(ACSG PUBLIC
    faiss
    mrnndescent
    nlohmann_json::nlohmann_json
)