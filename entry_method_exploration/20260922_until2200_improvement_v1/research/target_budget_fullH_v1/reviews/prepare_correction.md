# 原生依赖列表更正

首版输入切片完成后，复制一个本继承版本不存在且也未引用的search_core.hpp失败，0编译/搜索。E118 ResearchKernel自包含于kernels.hpp，base_engine.hpp仅需要该文件与common目录。原准备源码、日志和inputs保留；v2按实际include闭包删除多余复制项，另写inputs_v2，样本/参数完全相同，已有两个复制文件逐字核对不覆盖。
