# P2 预选查询 trace 分析

已独立重放 460 条搜索 trace、完成 276 个同入口配对。实际 query IDs：[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 157, 631, 2003, 4093, 6007, 8009, 9967]。
选择覆盖：FULL_REGISTERED_LIST；未观察的预选 IDs：[]。这份小样本描述不判定 P2 gate，也不证明总体性能收益。

完整预注册矩阵另行检查：12 / 12 个数据集×L×比较单元有完整查询对；全矩阵及全部预选 IDs 齐全：True。

| 数据集 | L | 对照 | 查询数 | 获得/损失 GT 结果数 | 非 GT 保留路径证据的查询数 |
| --- | --- | --- | --- | --- | --- |
| webvid2_5m_light_v1 | 64 | geom_unified → geom_uniform | 23 | 20 / 18 | 8 |
| webvid2_5m_light_v1 | 64 | geom_unified → geom_probability | 23 | 20 / 18 | 8 |
| webvid2_5m_light_v1 | 64 | oracle_unified → oracle_probability | 23 | 27 / 9 | 10 |
| webvid2_5m_light_v1 | 128 | geom_unified → geom_uniform | 23 | 10 / 25 | 5 |
| webvid2_5m_light_v1 | 128 | geom_unified → geom_probability | 23 | 10 / 25 | 5 |
| webvid2_5m_light_v1 | 128 | oracle_unified → oracle_probability | 23 | 16 / 15 | 6 |
| yandex_t2i_official10M_ip_v1 | 64 | geom_unified → geom_uniform | 23 | 15 / 19 | 6 |
| yandex_t2i_official10M_ip_v1 | 64 | geom_unified → geom_probability | 23 | 14 / 19 | 6 |
| yandex_t2i_official10M_ip_v1 | 64 | oracle_unified → oracle_probability | 23 | 18 / 9 | 7 |
| yandex_t2i_official10M_ip_v1 | 128 | geom_unified → geom_uniform | 23 | 2 / 13 | 1 |
| yandex_t2i_official10M_ip_v1 | 128 | geom_unified → geom_probability | 23 | 2 / 13 | 1 |
| yandex_t2i_official10M_ip_v1 | 128 | oracle_unified → oracle_probability | 23 | 3 / 1 | 2 |

路径证据要求中间节点在当前方法被扩展、在配对方法被拒绝或在扩展前淘汰，且实际成为新增 GT 的首次发现祖先；中间节点可以不是 GT。它不能证明该节点是必要或唯一的桥，其他未观察路径仍可能存在。

所有候选事件、GT 阶段、同 route 校验、扩展/未扩展淘汰、获益与受损的对称路径证据、阈值统计及证据 checksum 见 [report.json](report.json)。跨区域统计仅覆盖首次发现边，未把已 visited 的邻接访问算作已观察边。
