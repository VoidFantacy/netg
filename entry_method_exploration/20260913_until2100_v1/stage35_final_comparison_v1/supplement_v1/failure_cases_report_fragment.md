
按L128每种方向取源行最小的两条，保留全五L命中（顺序64/128/256/400/800），只是事后失败解释：

| 数据 | 方向/源行 | P命中 | 新方法命中 |
|---|---|---|---|
| Web | rescued / 162 | 0 0 0 0 0 | 5 5 5 7 7 |
| Web | rescued / 195 | 0 0 3 3 5 | 2 3 4 5 6 |
| Web | new_failure / 99 | 7 7 7 8 8 | 0 0 1 1 8 |
| Web | new_failure / 121 | 1 5 6 6 8 | 0 0 1 6 7 |
| Y | rescued / 4 | 0 0 0 3 8 | 1 1 1 1 7 |
| Y | rescued / 18 | 0 0 0 0 10 | 9 9 10 10 10 |
| Y | new_failure / 154 | 4 4 4 5 8 | 0 0 4 5 8 |
| Y | new_failure / 850 | 0 1 1 9 10 | 0 0 1 9 10 |

![双向失败案例全五L](figures/failure_cases_both_directions.png)

[八例GT10/入口全表](failure_cases_both_directions.csv)。原全401条完整表保持，不以个例替代整体判断。
