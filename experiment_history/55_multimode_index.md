# E66 GT10多画像单小索引

2026-09-13，完整训练/历史辅助开发已执行，非最终wall。固定原真实H和GT10归属，每hub保留P加两模态；physical3H、search7slot去重为3真实hub。WebVid soft归属全部保留；固定20轮和父mass8/ESS16、子mass2/ESS8，不合格重复P。两个新增slot按子质量分raw prior1，总query质量保持，原P额外保存。旧E10是GT1硬盆、原top32内64点积重排；此处直接同一小图检索，不宣称新颖性。

webvid2_5m_light_v1：478/815个hub有合格双模态；相对baseline fit净-496、aux净-106 GT10命中，两半[-38, -68]，aux失败净+13；aux相对同容量duplicate控制净+130。预锁开发门失败，不把局部正值或NDC当完整性能。

yandex_t2i_official10M_ip_v1：623/821个hub有合格双模态；相对baseline fit净+164、aux净+49 GT10命中，两半[-14, 63]，aux失败净-4；aux相对同容量duplicate控制净+182。预锁开发门失败，不把局部正值或NDC当完整性能。

画像全部冻结后测完整fit20K和aux7952；aux来自历史router_train[2048:10000]，两半均为选型训练反馈，不称盲集。fit含旧train/monitor，Fast30K/E10已有使用；E34最终validation与held-out未进入本轮。

实际337248 NSG、336960 HNSW、4新图构建；合成另1小图/15 HNSW。单线程CPU15，所有job实际退出后评分；167712开发返回及768预检独立集合评分，55904旧baseline恢复，288原kernelparity、7slot映射/去重、图bytes和模型质量/ESS/先验守恒通过。训练30.286秒，操作wall不当QPS。

[协议](../entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/protocol.md) · [完整结果/控制](../entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/report.md) · [冻结门](../entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/results/selection.json) · [逐query失败](../entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/results/failure_cases.csv) · [验收](../entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/reviews/verification.json)。
