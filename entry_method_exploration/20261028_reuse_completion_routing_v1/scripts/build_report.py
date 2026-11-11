import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import csv,json,time,textwrap
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import font_manager
R=Path(__file__).resolve().parents[1]
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':10,'axes.unicode_minus':False,'pdf.fonttype':3})
DS=['coco','deep10m_l2_v1'];LABEL={'coco':'COCO raw-IP','deep10m_l2_v1':'Deep10M squared-L2'};METHODS=['GT10','B32','BLOCK-R2048','REUSE-REG','REUSE-BLOCK','MAIN-BLOCK'];NEW=METHODS[3:]
def rows(p):return list(csv.DictReader(p.open()))
def num(r,k):return float(r[k]) if r[k] else float('nan')
def tablemd(header,rs):return '\n'.join(['| '+' | '.join(header)+' |','| '+' | '.join(['---']*len(header))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rs])
def main():
 t=time.perf_counter();ps=rows(R/'analysis/points.csv');pa=rows(R/'analysis/paired.csv');cc=rows(R/'analysis/discrete_comparisons.csv');get=lambda ds,m,L:next(p for p in ps if p['dataset']==ds and p['method']==m and int(p['L'])==L);pair=lambda ds,m,L:next(p for p in pa if p['dataset']==ds and p['method']==m and int(p['L'])==L)
 selected=[p for p in cc if p['method'] in NEW];dom=sum(bool(p['dominated_by_GT_L']) for p in selected);speed=sum(num(p,'target_speed_delta_pct')>=2 and p['target_speed_three_rounds_positive']=='True' for p in selected);budget=sum(num(p,'budget_recall_delta_pp')>=.05 for p in selected)
 cov=json.loads((R/'reviews/formal_trace_audit.json').read_text())['coverage'];prep=json.loads((R/'preparation.json').read_text());audit=json.loads((R/'reviews/results_audit.json').read_text());fit=prep['models'];cost=[]
 for role in ['calibration','formal']:
  for ds in DS:
   rec=json.loads((R/f'reviews/{role}_{ds}.receipt.json').read_text());cost.append([role,LABEL[ds],f"{rec['seconds']:.2f}",f"{rec['peak_sampled_rss_bytes']/2**30:.2f}",rec['max_observed_threads']])
 key=[]
 for ds in DS:
  for m in METHODS:
   p=get(ds,m,200);b=get(ds,'GT10',200);gain=num(p,'recall_pct')-num(b,'recall_pct');extra=1e6/num(p,'qps')-1e6/num(b,'qps');key.append([LABEL[ds],m,f"{num(p,'recall_pct'):.4f}%",f"{num(p,'qps'):.2f}",f'{gain:+.4f}',f'{extra:+.2f}'])
 lines=['# E189：复用 GT10 信息的补全路由实验','2026-10-28。默认 E99 GT10 保持；本轮固定矩阵已完成，无待恢复队列。',f'正式两集真实 K100，共70点/210完整单线程轮；校准64点/192轮。18个新复用点中，{dom}个被实测GT10同时覆盖Recall与QPS；离散速度筛选通过{speed}点，预算召回筛选通过{budget}点。筛选是有限网格的探索结果，不自动构成默认替换。','## 固定 L200 的完整表现',tablemd(['数据','方法','Recall@100','QPS','ΔRecall pp','额外 μs/query'],key),'QPS为本轮同一二进制三轮中位数，包含分配、GT10路由/主搜、补全、六数组复制及销毁。绝对速度不拼接E188；B32的原生计数0是占位，实际精算由独立表重建。','## 机制及与旧方法的区别','REUSE-REG：三个已产生入口的每hub8区域表，加主返回计数最高8区域，最多32个粗代表评分；取最多8个，沿旧REG-R模型选最多2区，后续每区1024码/48候选。模型迁移到稀疏排名存在失配风险，不是返回等价优化。','REUSE-BLOCK：入口每hub8块加主返回最高8块，最多32个块代表，直接按原metric排序并扫码；总预算2048码，全局96个PQ候选。MAIN-BLOCK只用主返回8块，实际最多1024码。块包含训练未见目标，能越过固定ID表，但候选表仍可能缺少有用块。','这与E174的posting种子加NSG一跳不同：本轮不读主图邻接作补全，不改变visited或搜索状态。块/PQ/主核不重建。区域法每区48与直接块法全局96不同，不能将全部差额归为纯路由因果。','## 固定 L200：路由、访问与实际救回']
 detail=[]
 for ds in DS:
  for m in METHODS[2:]:
   p=get(ds,m,200);a=pair(ds,m,200);detail.append([LABEL[ds],m,f"{num(p,'coarse_centres_per_query'):.1f}",f"{num(p,'block_centres_per_query'):.1f}",f"{num(p,'scanned_codes_per_query'):.1f}",a['members_rescued'],a['members_damaged'],a['rescued_source_out']])
 lines += [tablemd(['数据','方法','粗代表/query','块代表/query','扫码/query','救回成员','损伤成员','旧来源外救回'],detail),'成员计数为10K查询中的发生次数；旧来源是原16K完整遗漏并集，不是截断B32或本轮12K源。扫码包括已在主返回内的码，不能据此推断耗时。','## 补全损失发生在哪一层',tablemd(['数据','方法','原遗漏','候选块覆盖','实际扫描覆盖','PQ96覆盖','最终救回'],[[LABEL[x['dataset']],x['method'],x['missing_members'],x['pool_covered'],x['scanned_covered'],x['shortlist_covered'],x['rescued']] for x in cov]),'L200全query覆盖链从同一实际主返回重建的全排序oracle trace计算。候选块覆盖尚未支付该块所有向量原metric精算，不能作可获得的Recall承诺。trace是wall外重建，不称另外保存的timed内部trace。','## 全部预定点及实际预算比较',tablemd(['数据','方法','L','同Recall阈值GT L','相对其QPS%','同预算GT L','预算Recall差pp','GT同时覆盖L'],[[LABEL[x['dataset']],x['method'],x['L'],x['target_GT_L'],f"{num(x,'target_speed_delta_pct'):+.2f}",x['budget_GT_L'],f"{num(x,'budget_recall_delta_pp'):+.4f}",x['dominated_by_GT_L'] or '无已测点'] for x in selected]),'阈值参照是达到候选Recall的最快已测GT10；其Recall可能更高，不等于精确等Recall。预算参照是QPS不低于候选的最高Recall已测GT10。全部真实L和三轮范围见points.csv；不插值外推，未测点不判胜。','## 严重失败与统计边界']
 fails=[]
 for x in pa:
  if x['method'] in NEW:fails.append([LABEL[x['dataset']],x['method'],x['L'],x['original_lt10'],x['final_lt10'],x['lt10_improved'],x['lt10_escaped'],x['new_lt10']])
 lines += [tablemd(['数据','方法','L','原失败','现失败','原失败改善','脱离失败','新增失败'],fails),'失败严格定义为单query Recall@100<10%，即0–9命中；恰好10不算。少量尾部个例不能推广。完整恢复、查询改善、成员救损、来源外救回分别统计。配对5000次bootstrap只作描述，不作多重比较或语义IID保证；三轮计时不是三份质量样本。','## 训练角色、费用和证据限制','新稀疏表只用合法前12K的L200教师实际遗漏和入口；末4K仅诊断，未按其结果改参数或选择配置。旧B32含末4K标签，所以完全排除于校准矩阵，正式仍作为16K历史参考。GT10历史训练可能使用合法fit query；正式公共10K历史曝光，均非新的全系统盲确认。模型固定迁移L100/200/400，无逐query跳过开关。',tablemd(['阶段','数据','子进程秒','采样RSS GiB','最大观察线程'],cost),tablemd(['数据','新表/映射构建秒','新持久数组 MiB'],[[LABEL[x['dataset']],f"{x['seconds']:.3f}",f"{x['bytes']/2**20:.3f}"] for x in fit]),'新表构建费用包含ID→block映射与教师遗漏计数。旧GT/PQ/块/图/画像/教师构建沿原收据继承，不是零成本。benchmark同时加载旧布局及新映射，RSS是进程共同装载的0.25秒采样峰值，不是单独生产增量；数组字节不等于RSS。suite已包含正式wall，不能重复相加。','新方法额外ID→block映射为N×4字节；原块布局直接复用。默认GT10不依赖这些补全数组，旧后端本身的常驻成本仍须支付。','## 核验与收口',f"真实timed包/3轮SHA、全量实际主包补全oracle、预算上限、第二份stdlib整数审计及原metric抽样评分通过；{audit['historical_packets_equal']}个旧控制完整包一致；E188的{audit['old_E188_seal_files_unchanged']}个封存文件未变。候选池、块选择及PQ阈值另用第二实现抽检。第二实现由同一执行者完成，不称独立人员复现。",'本轮只测COCO/Deep真实K100，一套图/画像与一个曝光窗口；不能替代K1或其余五集。固定版本收口，不按测试结果扩池/扩预算/重训直到通过。可靠Recall–QPS目标仍需覆盖范围与独立确认。','[协议](protocol.md) · [冻结身份](freeze.json) · [全部70点](analysis/points.csv) · [救损](analysis/paired.csv) · [离散比较](analysis/discrete_comparisons.csv) · [覆盖链核验](reviews/formal_trace_audit.json) · [整数核验](reviews/results_audit.json)']
 note=json.loads((R/'interpretation.json').read_text());lines[3:3]=[note['conclusion'],note['cost_finding'],note['coverage_finding']]
 cp=rows(R/'calibration_analysis/paired.csv');calrows=[]
 for ds in DS:
  for m in METHODS[2:]:
   a=next(x for x in cp if x['dataset']==ds and x['method']==m and x['L']=='200');b=pair(ds,m,200);calrows.append([LABEL[ds],m,f"{num(a,'recall_delta_pp'):+.4f}",f"{num(a,'extra_time_pct'):+.2f}",f"{num(b,'recall_delta_pp'):+.4f}",f"{num(b,'extra_time_pct'):+.2f}"])
 lines += ['## 校准诊断与正式表现（不用于配置选择）',tablemd(['数据','方法 L200','校准增益pp','校准耗时增加%','正式增益pp','正式耗时增加%'],calrows),'校准4K与正式10K的绝对QPS不拼接；此表只对照各自同L GT10的相对量。旧B32不参与校准。[全部校准64点](calibration_analysis/points.csv)及[第二实现核验](reviews/calibration_results_audit.json)单独保留。']
 roles=json.loads((R/'reviews/role_model_audit.json').read_text())['checks'];lines += ['## 训练表与查询角色复核',tablemd(['数据','复算hub表行数','fit/cal同向量SHA','fit/test同向量SHA','cal/test同向量SHA'],[[LABEL[x['dataset']],x['recomputed_hub_rows'],x['fit_cal_identical_vector_hashes'],x['fit_test_identical_vector_hashes'],x['cal_test_identical_vector_hashes']] for x in roles]),'SHA交集为distinct精确向量值数量，非语义重叠率；行角色分开不保证语义独立。新表用另一遍按hub读取前12K残差的实现全量重建并逐项核验。']
 arrays=[]
 for ds in DS:
  e=json.loads((R/f'results/{ds}/environment.json').read_text());arrays.append([LABEL[ds],f"{e['old_backend_bytes']/2**20:.2f}",f"{e['block_backend_bytes']/2**20:.2f}",f"{e['reuse_array_bytes']/2**20:.2f}",f"{(e['old_backend_bytes']+e['block_backend_bytes']+e['reuse_array_bytes'])/2**20:.2f}"])
 lines += ['## 常驻数组与准备费用补充',tablemd(['数据','旧区域后端MiB','块布局MiB','新运行数组MiB','合计MiB'],arrays),'上述为共同benchmark载入的辅助数组payload，非全进程RSS或精确独立部署最低内存。旧/新布局存在重复存储，本轮未优化；GT10生产不需要这些补全数组。']
 build=json.loads((R/'reviews/build_receipt.json').read_text());qual=[json.loads((R/f'reviews/qualification_{ds}.receipt.json').read_text()) for ds in DS];lines += [f"成功编译{build['seconds']:.3f}s；COCO/Deep资格job分别{qual[0]['seconds']:.3f}s/{qual[1]['seconds']:.3f}s。前述suite已经包含计时批次；不把这些阶段费用写成全部人工开发或项目总wall。",'## 后续问题（本轮未执行）',note['next_gate']]
 post=json.loads((R/'reviews/posthoc_scoring_audit.json').read_text())['checks'];lines += ['## 事后补充：排序失真与重复向量边界',tablemd(['数据','方法','固定样本原遗漏','样本扫描覆盖','实际PQ96覆盖','float64精确96覆盖','全量短名单未返回','其中相同向量不同ID'],[[LABEL[x['dataset']],x['method'],x['sample_original_missing'],x['sample_scanned_GT_missing'],x['sample_actual_PQ96_GT_missing'],x['sample_float64_exact96_GT_missing'],x['all_query_shortlist_to_final_lost'],x['lost_with_returned_identical_vector']] for x in post]),'这是看到完整覆盖链后追加的只读诊断，随机种子20261028固定抽256query；未改模型/预算/测试点。float64全扫描评分只定位排序机会，不是实测在线方法或免费上界。所有短名单到最终输出的损失则检查全10K，并保留严格GT-ID与原tie语义。[逐例与诊断脚本证据](reviews/posthoc_scoring_audit.json)。']
 (R/'report_zh.md').write_text('\n\n'.join(lines)+'\n')
 def page(title,no):
  f=plt.figure(figsize=(12,8));f.suptitle(title,y=.94,fontsize=18);f.text(.05,.035,f'E189 | 2026-10-28 | 两集真实K100 / T1 / 历史曝光测试 | {no}/6',fontsize=9,color='#667788');return f
 def texts(f,ls,y=.84,step=.065,size=12):
  for s in ls:f.text(.065,y,s,fontsize=size,va='top');y-=step
 def table(f,headers,data,box=(.05,.14,.9,.67),size=9):
  ax=f.add_axes(box);ax.axis('off');tb=ax.table(cellText=data,colLabels=headers,cellLoc='center',loc='center');tb.auto_set_font_size(False);tb.set_fontsize(size);tb.scale(1,1.7)
  for (i,j),cell in tb.get_celld().items():
   cell.set_edgecolor('#d9e0e7');cell.set_facecolor('#eaf1f7' if i==0 else ('#f7f9fb' if i%2==0 else 'white'))
 pdf=R/'ACSG_复用路由与补全成本实验_20261028.pdf';figdir=R/'figures';figdir.mkdir(exist_ok=True)
 with PdfPages(pdf) as out:
  f=page('复用已有信息，能否降低有效补全的费用？',1);f.text(.06,.85,f'18个新点：{dom}个被已测GT10同时覆盖；速度筛选{speed}点，预算召回筛选{budget}点。',fontsize=13);table(f,['数据','方法 L200','Recall@100','完整QPS','增量 pp','额外μs'],key,box=(.04,.17,.92,.64),size=9);f.text(.06,.11,'默认E99 GT10保持。正式70点/210轮；另64点/192轮校准。完整计时，旧速度不拼接。',fontsize=10);out.savefig(f);plt.close(f)
  f=page('Recall–QPS：所有预定真实 L',2)
  for j,ds in enumerate(DS):
   ax=f.add_axes((.08+j*.48,.22,.4,.58))
   for m in METHODS:
    p=sorted([x for x in ps if x['dataset']==ds and x['method']==m],key=lambda x:int(x['L']));ax.plot([num(x,'recall_pct') for x in p],[num(x,'qps') for x in p],'-o',ms=3,label=m,linewidth=1.2)
   ax.set_title(LABEL[ds]);ax.set_xlabel('Recall@100 (%)');ax.set_ylabel('完整单线程 QPS');ax.grid(alpha=.2);ax.legend(fontsize=8)
  f.text(.08,.12,'线段仅连接实际测量点，不插值作判定；新方法只有L100/200/400。GT10含附近预算控制。',fontsize=11);f.text(.08,.08,'B32是历史16K训练表；新方法仅前12K拟合。较大的候选池不自动构成有效救回。',fontsize=10);out.savefig(f);f.savefig(figdir/'recall_qps.svg');plt.close(f)
  f=page('路由、访问与最终救回必须一起计算',3);table(f,['数据','方法 L200','粗代表','块代表','扫码','救回','损伤','源外'],detail,box=(.04,.27,.92,.52),size=9);texts(f,['REUSE-REG最多32个粗代表，仍做区域内块路由；原方案固定1024个粗代表。','REUSE-BLOCK最多32个块代表，MAIN-BLOCK最多8个；总扫码上限2048。','直接块法全局96候选，区域法每区48；这些差额不是纯路由成本的因果消融。'],y=.23,step=.045,size=10);out.savefig(f);plt.close(f)
  f=page('遗漏在哪一层丢失：L200 全10K查询覆盖链',4);data=[[LABEL[x['dataset']],x['method'],x['missing_members'],x['pool_covered'],x['scanned_covered'],x['shortlist_covered'],x['rescued']] for x in cov];table(f,['数据','方法','原遗漏','池覆盖','扫描覆盖','PQ96','最终救回'],data,box=(.04,.43,.92,.32),size=9);texts(f,['池覆盖：遗漏目标所在块进入最多32/8个候选块。','扫描覆盖：该块经过原metric中心排序和整块预算后被访问。','PQ96覆盖：遗漏目标进入原metric精算短名单；最终救回仍需实际Top100合并。','COCO固定256条诊断：扫描覆盖486；实际PQ96=53，float64精确96=486。','Deep各91个最终损失涉及8条query：都有已返回的相同向量不同ID。','精确96仅定位排序机会，未计在线费用；严格GT-ID与原tie规则保持。'],y=.39,step=.055,size=11);out.savefig(f);plt.close(f)
  f=page('实际预算对照：全部18个复用点',5);d=[[('COCO' if x['dataset']=='coco' else 'Deep'),x['method'],x['L'],x['target_GT_L'],f"{num(x,'target_speed_delta_pct'):+.2f}",x['budget_GT_L'],f"{num(x,'budget_recall_delta_pp'):+.4f}",'是' if x['dominated_by_GT_L'] else '否'] for x in selected];table(f,['数据','方法','L','阈值GT L','速度差%','预算GT L','Recall差pp','被GT覆盖'],d,box=(.03,.12,.94,.72),size=8);f.text(.05,.085,'阈值GT达到候选Recall，可能更高；预算GT耗时不高于候选。有限离散网格，不称精确等Recall。',fontsize=9);out.savefig(f);plt.close(f)
  f=page('费用、角色与可复现边界',6);table(f,['阶段','数据','suite 秒','采样RSS GiB','实际线程'],cost,box=(.06,.52,.88,.29),size=10);texts(f,[f"新映射/稀疏表构建：COCO {fit[0]['seconds']:.2f}s / {fit[0]['bytes']/2**20:.2f}MiB；Deep {fit[1]['seconds']:.2f}s / {fit[1]['bytes']/2**20:.2f}MiB。",'旧图、GT、PQ、块及教师成本继承原收据；完整wall包含在suite内，不重复相加。','前12K fit / 后4K诊断；旧B32排除校准。正式10K历史曝光，无新盲确认。',f"70点/210轮返回核验；{audit['historical_packets_equal']}个旧控制完整包一致；2145个E188封存文件未变。",'第二实现同一执行者；没有K1/其余五集的新证据，不从局部结果直接修改默认。','固定矩阵收口。完整数据、成员救损、严重失败与来源限制见配套报告及CSV。'],y=.48,step=.06,size=11);out.savefig(f);plt.close(f)
 (R/'reviews/report_build.json').write_text(json.dumps(dict(status='PASS_E189_REPORT_BUILD',pages=6,formal_points=len(ps),new_points=len(selected),dominated=dom,speed_screen=speed,budget_recall_screen=budget,seconds=time.perf_counter()-t),indent=2)+'\n');print(json.dumps(dict(dom=dom,speed=speed,budget=budget,pdf=str(pdf))),flush=True)
if __name__=='__main__':main()
