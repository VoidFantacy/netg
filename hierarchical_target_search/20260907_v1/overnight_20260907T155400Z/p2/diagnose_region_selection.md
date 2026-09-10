# P2 区域选择诊断入口与字段

该脚本须在主分析完成、两数据集 L64/128 共四项 `oracle_protection` 的 ordinary paired95% 区间下界都大于 0 后，由 root 串行控制器启动。此条件只允许一次有界诊断，不意味着 P2 GO 或正式性能改善。

```bash
.venv_cpu/bin/python hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/diagnose_region_selection.py \
  --analysis hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/analysis_v1/analysis.json \
  --audit hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p0/full_audit/audit.json \
  --input webvid2_5m_light_v1 hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/webvid_eval/count.json hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/webvid_model/model.json \
  --input yandex_t2i_official10M_ip_v1 hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/yandex_eval/count.json hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/yandex_model/model.json \
  --output NEW_DIAGNOSIS_DIRECTORY
```

只打开 analysis、P0 audit、count、model、labels，以及 router_train GT 文件前 10K 条记录；不打开 base、图、query vectors、validation、held-out，不读 GT 后 20K 拟合部分，不运行搜索或重新拟合。pilot GT 全 top100 值用于匹配已有 P0 fingerprint，实际诊断只用前十个 ID。query 对齐通过 P0 split 契约和 count 的 `[0,10000)`/逐行 query IDs 核验，不声称重新计算 query-vector hash。

count/model 文件 SHA256 必须匹配已完成主分析；model 必须绑定所给 P0 audit，fit-range 和 fit query/GT fingerprint、labels SHA256 均须一致；同路由队列对照及跨 L 路由须相同。输出目录必须不存在。截止保护为 UTC 2026-09-07 22:59；截止后不能为报告运行本诊断。

| 字段 | 含义 |
| --- | --- |
| `geometry_absolute_gt10_mass` | `GT10` 落入 count 实际 geometric top4 区域的数量 / 10 |
| `oracle_absolute_gt10_mass` | 根据真实 pilot GT 计算的最多四区域质量；同时严格校验已保存 oracle 区域顺序与 ID tie 规则 |
| `absolute_mass_gap` | oracle 绝对质量减 geometric 绝对质量 |
| `gt10_distinct_regions` | 十个 GT ID 分布到的不同区域数 |
| `top4_overlap_count` | 几何/oracle 所选区域集合交集大小，0–4 |
| `intersection_absolute_gt10_mass` | GT10 落入两个所选集合交集的数量 / 10 |
| `intersection_fraction_of_oracle_top4_mass` | 上项除 oracle 绝对质量；这是条件比例，不能替代绝对覆盖 |

主表固定按 **geometric 绝对质量** 分 `[0,.25),[.25,.5),[.5,.75),[.75,1]` 四箱，每箱报告 query 数、几何/oracle 质量、区域 distinct，以及 geometry uniform/probability 和 oracle probability 各自减 unified 的 Recall pp。另保存 `oracle_unified−geom_unified` 作为路由组合差距。空箱为 `null`；不增设分箱、CI 或通过阈值。

产物为 `diagnosis.json`、每数据集 JSON、按 query ID/L 对齐的 CSV 和完成/失败标记。分箱只是历史 development pilot 上的相关性，不能据此宣称因果、泛化或 QPS 收益。oracle 与 geometric 同时改变选区、门户、入口顺序和可能的去重后入口数，差距不能直接归因于门户或连接问题。搜索允许跨区访问，top4 GT 质量也不是 Recall 上界。

最终合成检查见 `selection_diagnosis_synthetic_tests_v2/result.json`：六种无效主分析 gate 被拒绝；相同 normalized oracle weights 对应不同绝对质量的案例通过；固定分箱边界、交集质量、ID tie 顺序及 GT **物理读取范围不越过 pilot 前缀** 均通过。错误 P0 audit hash 绑定在读取 GT 前被拒绝。结果记录了最终生产脚本 SHA256；没有使用真实数据运行诊断。
