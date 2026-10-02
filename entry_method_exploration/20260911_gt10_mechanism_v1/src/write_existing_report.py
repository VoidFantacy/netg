from common import *

def loadcsv(name):return list(csv.DictReader((RUN/'results'/name).open()))
def table(head,rows):return ['| '+' | '.join(head)+' |','|'+'|'.join(['---']*len(head))+'|']+['| '+' | '.join(map(str,row))+' |' for row in rows]
def f(x,d=3):return f'{float(x):.{d}f}'
def main():
    evidence=read(RUN/'results/existing_evidence.json');metrics=loadcsv('all_metrics.csv');pairs=loadcsv('all_pairs.csv');rep=loadcsv('repetition.csv')
    out=['# GT10机制分析 A–C：已有证据阶段','',
        '2026-09-11。此报告在补测前形成，新增NSG/ANN搜索调用为0。原E24/E25/E26资产只读；所有分段有历史使用，validation不是新盲测。主对照固定两数据集GT10 hard与matched GT1 hard，辅助软画像维持原cal选择。','',
        '## 1. 主对照与Fast原有贡献','',
        '表内QPS均为E24当轮一次独立单线程plain wall；不是稳定加速幅度。两层增益分列，不能把Fast对NSG的收益全部算给GT10。','']
    vals=[]
    for ds in DATASETS:
        for L in LS:
            mm={m['model']:m for m in metrics if m['dataset']==ds and m['stage']=='validation' and int(m['L'])==L}
            n,a,b=mm['nsg_medoid'],mm['gt1_hard'],mm['gt10_hard']
            vals.append([ds.split('_')[0],L,f(n['recall_percent']),f(a['recall_percent']),f(b['recall_percent']),
              f(float(a['recall_percent'])-float(n['recall_percent'])),f(float(b['recall_percent'])-float(a['recall_percent'])),
              f(a['qps'],2),f(b['qps'],2),f(100*(float(b['qps'])/float(a['qps'])-1),2)])
    out+=table(['数据','L','NSG R%','GT1 R%','GT10 R%','Fast−NSG pp','GT10−Fast pp','GT1 QPS','GT10 QPS','ΔQPS%'],vals)
    out+=['','全部同L正/负点及未校正描述性配对query区间：[all_pairs.csv](results/all_pairs.csv)；不插值的实测非支配点：[hard_frontier.csv](results/hard_frontier.csv)。','',
          '## 2. 已有重复性','',
          '每个历史批次独立比较；表为该批次各方法QPS中位数的比值。逐轮原值另存，不跨批次拼接。WebVid重复的是GT10 soft，不能用它补GT10 hard的空缺。','']
    vals=[]
    for ds in DATASETS:
        for L in LS:
            r=[x for x in rep if x['dataset']==ds and int(x['L'])==L and x['repeat']=='0']
            vals.append([ds.split('_')[0],r[0]['model'],L]+[f(x['batch_median_delta_qps_percent'],3) for x in sorted(r,key=lambda x:int(x['version']))])
    out+=table(['数据','实际画像','L','E24 ΔQPS%','E25 ΔQPS%','E26 ΔQPS%'],vals)
    out+=['','Yandex L128的+0.335pp命中提升跨历史结果逐位复现，但E24的+2.563%速度在E25/E26为−0.184%/+0.038%。不能给它编造一个已经证实的2.56%加速机制。Yandex其它L速度也有正负波动；三轮重复不增加Recall样本数。','',
          '来源及七字段逐位回归见[repetition.csv](results/repetition.csv)与[existing_evidence.json](results/existing_evidence.json)。','',
          '## 3. GT目标、支持和画像方向','',
          'a10(q,h)=Σj=1..10 1[b(q,j)=h]/10；每query总质量1。画像加的是unit(query)，GT向量只决定权重。对应于把query的服务对象从GT1所属hub扩展到随机一个top10目标所属hub；它是目标相关的分数分配，既含多目标信息，也改变支持和平滑程度。','']
    vals=[]
    for ds in DATASETS:
        fit=evidence['datasets'][ds]['fit'];mm={x['model']:x for x in fit['reconstructed_profiles']};a,b=mm['gt1_hard'],mm['gt10_hard']
        vals.append([ds.split('_')[0],f(fit['distinct_GT_hubs']['mean']),f(100*fit['off_GT1_mass']['mean'],2),fit['all_ten_same_hub_queries'],
           f(a['mass']['median'])+' → '+f(b['mass']['median']),f(a['ESS']['median'])+' → '+f(b['ESS']['median']),
           f(a['direction_concentration']['median'])+' → '+f(b['direction_concentration']['median']),
           f(b['angle_degrees']['median'],2),str(a['zero_support_hubs'])+' → '+str(b['zero_support_hubs'])])
    out+=table(['数据','平均不同hub','离开GT1质量%','十目标同hub/20K','mass中位','ESS中位','方向集中度中位','画像角度中位°','零支持hub'],vals)
    out+=['','两数据集四份已选画像的归属digest、支持统计和W数值恢复均通过；GT1沿原dense assignments身份，其它沿原float64 digest。ESS不等于新增独立query数，所有画像的全局总质量仍20K。每hub原值、rank归属和质量转移矩阵完整保留。','',
          '## 4. 三入口与真正产生效果的query','']
    vals=[]
    for ds in DATASETS:
        for L in LS:
            x=next(x for x in pairs if x['dataset']==ds and x['stage']=='validation' and x['model']=='gt10_hard' and int(x['L'])==L)
            vals.append([ds.split('_')[0],L,x['changed_entries'],x['positive'],x['neutral'],x['negative'],x['gain_hits'],x['lost_hits'],x['net_hits'],x['rescued']+'/'+x['new_zero']])
    out+=table(['数据','L','换入口/2000','正query','平query','负query','正命中','负命中','净命中','零命中救回/新增'],vals)
    out+=['','同query实际三入口相同的返回ID、距离bits、命中/mask和graph NDC全部相同；质量变化只能通过改变入口及其后的原NSG执行产生。换入口是必要条件，远非充分条件。五L入口完全不变，但有限beam执行不同，query可以跨L正负切换。全部aligned配对保存在results/*_paired.npz，不因分层删除任何query。','',
          '## 5. 精确画像排序与HNSW','']
    vals=[]
    for ds in DATASETS:
        for stage in ['cal','audit']:
            r=[x for x in pairs if x['dataset']==ds and x['stage']==stage and x['model']=='gt10_hard']
            a=next(x for x in r if x['exact']=='False');b=next(x for x in r if x['exact']=='True')
            vals.append([ds.split('_')[0],stage,f(a['delta_recall_pp']),f(b['delta_recall_pp']),f(float(a['delta_recall_pp'])-float(b['delta_recall_pp']))])
    out+=table(['数据','历史段L128','HNSW下GT10−GT1 pp','exact下GT10−GT1 pp','后端交互pp'],vals)
    out+=['','GT10的局部质量收益并非只能由HNSW近似误差制造：WebVid两个开发段在精确画像top3下仍有正净命中。后端可以放大或缩小这个差，精确画像top3也不是NSG效用oracle。validation原来没有hard exact3整批搜索，不能把开发段的结论直接当作其逐query因果分解。','',
          '## 6. 成本证据与缺口','',
          'WebVid GT10 hard五L的graph NDC均小幅减少，路由NDC减少约10.232/query；可支持工作量减少这个分项事实。Yandex L128 graph NDC略增，约1%量级的路由wall也解释不了E24约2.56%的总速度差。已有NDC、分项wall和总wall均分列，未测扩展路径长度或硬件cache事件。','',
          '新增诊断前的明确缺口：','',
          '- WebVid GT10 hard缺独立重复wall；只补固定两硬画像、历史validation2K五L，各三次warm/plain即可。Yandex已有重复，当前无需再补整轮。',
          '- 真实多目标对应关系与一般支持/平滑同时改变。GT1 soft等辅助表说明ESS大不保证更好，但没有严格因果隔离。可用一个保留0.1 GT1贡献、共同打乱第2–10名目标所属hub与query对应关系的控制，保留每rank全局hub频次和每hub总质量；它不保持ESS/方向/逐query重合分布，不能称完全匹配。只对原cal/audit L128做exact/HNSW机制诊断，不作为部署或validation候选。',
          '- 没有逐扩展路径/cache证据，最终应保留未知；当前不需要为解释未复现的速度幅度追加trace实验。','',
          '以上缺口将在任何新搜索前另存独立小协议与硬预算。此已有证据阶段不启动2A/微型图拉伸/聚类/rank等方法分支。']
    (RUN/'existing_report.md').write_text('\n'.join(out)+'\n')
    print('EXISTING_REPORT_WRITTEN')

if __name__=='__main__':main()
