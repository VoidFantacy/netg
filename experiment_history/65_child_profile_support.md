# E76 子模态支持与既有收益损伤

低支持子模态并没有一致地集中损伤，当前证据不支持直接提高mass/ESS门槛。原完整三入口的损伤与子画像方向有关，但训练/辅助迁移方向并不稳定，以下仅为事后关联。

| 数据 / 比较 | 全部净命中 | ESS<16组净命中 | fraction<.25组 | parent cosine<.9组 | lift>.05组 |
|---|---:|---:|---:|---:|---:|
| WebVid / fit_approx | -496 | +57 | +26 | +28 | +147 |
| WebVid / aux_compact | -59 | +18 | -49 | -57 | -19 |
| WebVid / aux_exact | -109 | +17 | -31 | -51 | +4 |
| Yandex / fit_approx | 164 | +35 | +31 | +50 | +228 |
| Yandex / aux_compact | 120 | -24 | +4 | +25 | +79 |
| Yandex / aux_exact | 132 | -22 | -11 | +24 | +65 |

WebVid ESS<16组在fit/compact辅助/exact辅助分别+57/+18/+17命中；小fraction组fit +26却辅助−49/−31，远离父画像组fit +28却辅助−57/−51。Yandex低ESS辅助反而−24/−22。因此不能把低ESS当共同损伤规则，也不能从这一组的净值模拟删除子画像后的效用。组间有重叠，表内不同列不可累加。

下一可检验候选是固定一档子画像向原父P收缩，保留P/物理槽/映射，并把评分变化与普通重构图做四格控制。它不按低ESS删画像，不把本组query或单hub的组合损益作为因果信用；收缩可能丢失已有收益、产生新损伤，需真实NSG检验，不保证单调保护。新版本尚未构图/查询，不能提前称成功。

三个比较分别是E66 fit20K mode−P、E73 aux7952 compact−P、E69 aux7952 exact-mode−exact-P。仅在已经选择的新增hub内部计算3画像分数，完整三入口返回全部来自旧物；不是重新运行ANN、全H路由或效用oracle。原approx实际slot与完整hub内winning slot各自保存，不能混同。

独立复算143616个旧返回集合/mask，6组比较、72个cohort行、3272个子画像支持行，耗时3.085秒；新ANN/NSG/构图/训练/GT/QPS全部0。每条query源行、三入口、actual/winning slot、支持和六个cohort标记保存为aligned NPZ。原E75及更早门保持，E73/E74 Yandex局部信号保留。

全部输入历史暴露，aux设计反馈计训练，fit含旧train/monitor；E34最终与held-out未打开。单线程CPU15分析，旧source与产物保持，整日目标未完成。

[协议](../entry_method_exploration/20260913_until2100_v1/stage17_child_support_diagnosis_v1/protocol.md) · [分组全表](../entry_method_exploration/20260913_until2100_v1/stage17_child_support_diagnosis_v1/results/cohorts.csv) · [子画像支持](../entry_method_exploration/20260913_until2100_v1/stage17_child_support_diagnosis_v1/results/child_support.csv) · [图](../entry_method_exploration/20260913_until2100_v1/stage17_child_support_diagnosis_v1/figures/child_support.png) · [核验和成本](../entry_method_exploration/20260913_until2100_v1/stage17_child_support_diagnosis_v1/reviews/verification.json)。
