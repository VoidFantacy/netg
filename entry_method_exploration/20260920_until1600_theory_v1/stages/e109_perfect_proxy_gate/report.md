# E109：真实目标代理仍未跨过搜索效用断点

2026-09-20，固定fit信息门完成，**STOP_PROXY_OBJECTIVES_BEFORE_TRAINING**。两种代理在Yandex均有正信号，但WebVid没有相应收益；按预锁跨两集门不训练这两个目标，不追加阈值或数据子集。原GT10默认与生产E99保持。

## 1. 这是学习目标的前置检查

从E24原fit20K固定取floor(i*20000/2048)，两集各2048行；原H、NSG、raw query和GT不变。TargetMean直接使用真实GT10单位目标向量的均值，最大化三个单位hub与该均值的平均内积。Coverage直接使用真实GT10目标的原hub归属质量，最大化三hub质量和；并列按原GT10精确分数及real ID。对照GT10Exact和UnitHubExact，同为全H精确选3入口。

两个代理知道部署时不可得的真实目标信息，但不是实际搜索效用最优动作，也不是Recall上界。fit参与过原画像构造；以下没有未曝光泛化证据。真实K1/K100均用L128，不新增Recall@10；输入覆盖10只是训练目标代理。

## 2. 全部真实检索对照

ΔR单位pp；16项主比较用固定20000次配对bootstrap、99.6875%区间（Bonferroni口径），仅作本fit投入门。

| 数据 | K | 代理 | 控制 | ΔR pp | 校正区间 | 零命中 控制→代理 |
|---|---:|---|---|---:|---|---|
| WebVid | 1 | TargetMean | GT10Exact | -1.3184 | [-2.7832, +0.1465] | 469→496 |
| WebVid | 1 | Coverage | GT10Exact | -0.6836 | [-2.0020, +0.6348] | 469→483 |
| WebVid | 1 | TargetMean | UnitHubExact | -0.2930 | [-1.7945, +1.1719] | 490→496 |
| WebVid | 1 | Coverage | UnitHubExact | +0.3418 | [-0.9277, +1.6113] | 490→483 |
| WebVid | 100 | TargetMean | GT10Exact | -0.0132 | [-0.5137, +0.4987] | 2→0 |
| WebVid | 100 | Coverage | GT10Exact | -0.0908 | [-0.5420, +0.3793] | 2→0 |
| WebVid | 100 | TargetMean | UnitHubExact | -0.0415 | [-0.5598, +0.5216] | 5→0 |
| WebVid | 100 | Coverage | UnitHubExact | -0.1191 | [-0.6147, +0.4136] | 5→0 |
| Yandex | 1 | TargetMean | GT10Exact | +1.0254 | [+0.0977, +2.0508] | 160→139 |
| Yandex | 1 | Coverage | GT10Exact | +0.9277 | [+0.1465, +1.8555] | 160→141 |
| Yandex | 1 | TargetMean | UnitHubExact | +1.1719 | [+0.1465, +2.1973] | 163→139 |
| Yandex | 1 | Coverage | UnitHubExact | +1.0742 | [+0.1465, +2.0996] | 163→141 |
| Yandex | 100 | TargetMean | GT10Exact | +0.5854 | [+0.1108, +1.1188] | 6→1 |
| Yandex | 100 | Coverage | GT10Exact | +0.4756 | [+0.0513, +0.9696] | 6→1 |
| Yandex | 100 | TargetMean | UnitHubExact | +1.0352 | [+0.4264, +1.7257] | 12→1 |
| Yandex | 100 | Coverage | UnitHubExact | +0.9253 | [+0.3555, +1.5800] | 12→1 |

Web目标均值相对GT10的R1/R100为−1.3184/−0.0132pp，覆盖代理为−0.6836/−0.0908pp；Web八项区间均跨0。Yandex两代理对两控制的八项区间均为正，其中目标均值相对GT10为+1.0254/+0.5854pp。保留这个数据集差异，但不据此改变冻结的跨数据训练门。

## 3. 代理更好不保证搜索更好

| 数据 | 方法 | 输入GT10区域覆盖 | 目标均值亲和 |
|---|---|---:|---:|
| WebVid | GT10Exact | 35.420% | 0.704730 |
| WebVid | UnitHubExact | 31.973% | 0.699103 |
| WebVid | TargetMean | 53.833% | 0.747545 |
| WebVid | Coverage | 68.931% | 0.732224 |
| Yandex | GT10Exact | 54.688% | 0.398126 |
| Yandex | UnitHubExact | 52.573% | 0.397256 |
| Yandex | TargetMean | 73.003% | 0.449456 |
| Yandex | Coverage | 81.504% | 0.429979 |

Web覆盖代理将平均输入区域覆盖从35.42%提高到68.93%，最终R1却低0.6836pp。Yandex则覆盖从54.69%提高到81.50%，R1/R100提高0.9277/0.4756pp。这是同一个代理到实际有限beam搜索的转化随数据而异的直接证据；不是模型表达力不足的证明，也不能归因于单一机制。

目标均值MSE与覆盖交叉熵均有各自的代理后悔界，但Recall界还需要代理到搜索效用的一致误差项δ。E109不估计全动作族δ，只显示当前两个代理最优动作未给出跨数据收益。停止投入不等于所有近似预测器必不可能改善：有限beam非单调，近似预测产生的不同动作仍可能更好。

预锁门要求每个代理在两集、两K、两控制均值均非负，且每集至少一个共同K对两个控制都≥1pp并且校正区间下端>0。TargetMean仅Yandex通过，Coverage两集门均未通过；Coverage在Yandex对GT10的K1均值0.9277pp低于1pp，不能事后下调门槛。

## 4. 验证、成本和下一步

真实NSG 66,304次，搜索编排77.86秒，分析3.59秒；0新GT/图/梯度训练/正式QPS。CPU15/实际线程1，方法及数据串行。两个smoke与链接E99同输出/距离bits/NDC，全量count/plain一致；全H代理排名、integer质量和10、输入方向/源行/real ID、独立评分、K1首返回与K100及NDC均通过。

新图表已实际查看，旧输入/模型/图及源码身份保持。后续应研究代理到搜索的断点，或在保留精确动作得分的条件下改善E108发现的小图可检索性；不能把本次停止解释成需要更大网络。16:00限时研究继续，当前无E109待运行搜索。

[协议](protocol.md) · [完整指标](results/metrics.csv) · [配对](results/paired.csv) · [代理量](results/proxy_values.csv) · [门](results/gate.json) · [图](figures/proxy_information_gate.png) · [验收](reviews/completion_audit.json)。
