from common import *
from prepare_supplement import SUP
from write_existing_report import table,f

def rows(path):return list(csv.DictReader(Path(path).open()))
def main():
    out=['# GT10机制分析：完整补测与辅助表','',
        '所有数据均为历史开发/validation，非盲测。真实shuffle每数据集一份、一个固定排列；没有按结果重选。QPS仅出自WebVid两硬画像的独立三次plain wall；其它补测为机制诊断，无QPS。','',
        '## WebVid三次硬画像计时','']
    r=rows(SUP/'results/repeat_wall.csv')
    out+=table(['L','repeat','GT1 Recall%','GT10 Recall%','GT1 QPS','GT10 QPS','同轮ΔQPS%'],
        [[x['L'],x['repeat'],f(x['GT1_recall_percent']),f(x['GT10_recall_percent']),f(x['GT1_qps'],2),f(x['GT10_qps'],2),f(x['delta_qps_percent'],3)] for x in r])
    out+=['','## 局部正点exact3与HNSW','',
          '两点为原WebVid L64和Yandex L128。backend_difference行是同画像exact−HNSW，不能当GT10相对GT1。','']
    r=rows(SUP/'results/local_exact_comparisons.csv')
    out+=table(['数据','L','比较','baseline','ΔRecall pp','正query','负query','正/负命中','描述性95% pp'],
       [[x['dataset'],x['L'],x['model'],x['baseline'],f(x['delta_recall_pp']),x['positive'],x['negative'],x['gain_hits']+'/'+x['lost_hits'],
         '['+f(x['CI95_low'])+', '+f(x['CI95_high'])+']'] for x in r])
    out+=['','## 打乱第2–10名目标对应关系','',
          '下表差值为shuffle−baseline。负数代表原画像更好。每hub总质量固定；ESS、query的GT1/tail重合和画像方向没有匹配。','']
    r=rows(SUP/'results/shuffle_comparisons.csv')
    out+=table(['数据','段','后端','baseline','ΔRecall pp','正query','负query','净命中','描述性95% pp'],
       [[x['dataset'],x['stage'],x['backend'],x['baseline'],f(x['delta_recall_pp']),x['positive'],x['negative'],x['net_hits'],
         '['+f(x['CI95_low'])+', '+f(x['CI95_high'])+']'] for x in r])
    out+=['','## shuffle支持与画像','']
    mm=read(SUP/'models/construction.json')
    out+=table(['数据','固定点/20K','mass最大误差','真实GT10 ESS中位','shuffle ESS中位','shuffle方向集中度中位','相对GT1角度中位°'],
        [[x['dataset'],x['fixed_points'],f'{x["mass_max_abs_difference"]:.3g}',f(x['real_GT10_ESS']['median']),f(x['ESS']['median']),
           f(x['concentration']['median']),f(x['angle_from_GT1_degrees']['median'],2)] for x in mm])
    out+=['','## 分项成本（仅WebVid新重复）','',
          'NDC为全部query均值；wall微秒/query。route/graph分别独立预热和计时，不相加代替独立端到端wall。非L128分项未排测，留空。','']
    r=rows(SUP/'results/repeat_components.csv')
    out+=table(['L','画像','route NDC','graph NDC','总wall μs','route-only μs','graph-only μs'],
      [[x['L'],x['model'],f(x['route_ndc']),f(x['graph_ndc']),f(x['median_end_to_end_us']),
        f(x['route_only_us']) if x['route_only_us'] else '未测',f(x['graph_only_us']) if x['graph_only_us'] else '未测'] for x in r])
    out+=['','## E24所有温度的原cal消融','',
          '原始选择已冻结。保留同温度GT1/GT10对照，不按本分析结果替换主画像。','']
    r=[x for x in rows(RUN/'results/all_metrics.csv') if x['stage']=='cal']
    out+=table(['数据','画像','exact','Recall%','route NDC','graph NDC'],
        [[x['dataset'],x['model'],x['exact'],f(x['recall_percent'],4),f(x['route_ndc']),f(x['graph_ndc'])] for x in r])
    out+=['','## 全量证据入口','',
          '- [已有A–C表](../existing_report.md)、[所有既有点](all_metrics.csv)、[所有配对](all_pairs.csv)、[按query分层](query_groups.csv)。',
          '- [GT名次命中变化](GT_rank_hit_changes.csv)、[目标hub与入口的几何联系](target_region_links.csv)、[每hub入口频次](entry_frequencies.csv)、[舍入控制](numeric_control.csv)。',
          '- [所有旧重复](repetition.csv)、[后来开发段](later_development.csv)、[旧实测前沿](hard_frontier.csv)、[新逐轮前沿](../supplement/results/repeat_frontier.csv)。',
          '- [规则选取的正负案例](cases.json)、`*_paired.npz`保存全部query与row IDs，不按结果筛掉query。',
          '- [新逐queryexact/HNSW](../supplement/results/analysis.json)、[补测执行与成本](../supplement/reviews/execution_complete.json)。']
    (RUN/'results/tables.md').write_text('\n'.join(out)+'\n')
    print('TABLES_COMPLETE')

if __name__=='__main__':main()
