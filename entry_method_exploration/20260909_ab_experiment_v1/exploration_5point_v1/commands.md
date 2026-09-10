# 实际执行与边界

工作区`/data/netg/ACSG`，所有原图、旧产物和冻结模型保留。

1. 编译独立`src/quick.cpp`到`bin/quick`，复用原CPU静态库，未修改原kernel。构建日志`logs/build.log`。
2. `src/prepare.py`核验原链接源码/库及1051个已冻结模型文件，复制各validation前2000行，固定seed20260828与同一个联合模型，生成两份配置。
3. 合成15点覆盖NSG/Fast/槽位路由及全部五L；240次原kernel比较、300组warm/timed query配对通过；多线程配置被拒绝。
4. 通过独立session启动`src/run.py`（PID16748），按两数据集顺序运行，每点一次warmup和一次独立wall。两个真实数据集内部各16query/点验原kernel，不做全量分项计时。
5. 结束后自动`src/analyze.py`独立核对GT、线程、五L模型和入口不变，输出三指标比较与图。

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv_cpu/bin/python entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/src/run.py
```

该命令已经运行，输出采用独立新目录，不能直接重复执行覆盖结果。实际阶段与wall见[state.json](state.json)。
