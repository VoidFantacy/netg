cmake_minimum_required(VERSION 3.17 FATAL_ERROR)

project(ACSG)

set(CMAKE_CXX_STANDARD 17)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fno-builtin-malloc -fno-builtin-calloc -fno-builtin-realloc -fno-builtin-free")
add_definitions(-std=c++17 -O3 -lboost -march=native -Wall -DINFO)

add_subdirectory(faiss)
add_subdirectory(benches)
add_subdirectory(ACSG)
add_subdirectory(MRNN_Descent)