import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import csv,json,time,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import font_manager
R=Path(__file__).resolve().parents[1];PDF='ACSG_COCO固定候选排序与完整费用_20261028.pdf'
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':10,'axes.unicode_minus':False,'pdf.fonttype':3})
def read(p):return list(csv.DictReader(p.open()))
def f(x,k):return float(x[k]) if x[k] else float('nan')
def md(head,rs):return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rs])
def main():
 t=time.perf_counter();points=read(R/'analysis/points.csv');pairs=read(R/'analysis/paired.csv');comp=read(R/'analysis/discrete_comparisons.csv');cal=read(R/'calibration_analysis/points.csv');sel=json.loads((R/'selection.json').read_text());audit=json.loads((R/'reviews/formal_results_audit.json').read_text());cov=json.loads((R/'reviews/scoring_formal_audit.json').read_text())['coverage'];env=json.loads((R/'results/coco/environment.json').read_text());methods=['GT10','B32','REUSE-BLOCK','SQ8-96']+(['PQ384-SQ8'] if sel['cascade_triggered'] else []);new=[x for x in comp if x['method'] in ['SQ8-96','PQ384-SQ8']];dom=sum(bool(x['dominated_by_GT_L']) for x in new);speed=sum(f(x,'target_speed_delta_pct')>=2 and x['target_speed_three_rounds_positive']=='True' for x in new);budget=sum(f(x,'budget_recall_delta_pp')>=.05 for x in new)
 get=lambda m,L:next(x for x in points if x['method']==m and x['L']==str(L));pair=lambda m,L:next(x for x in pairs if x['method']==m and x['L']==str(L));base=get('GT10',200)
 key=[]
 for m in methods:
  x=get(m,200);key.append([m,f"{f(x,'recall_pct'):.4f}%",f"{f(x,'qps'):.2f}",f"{f(x,'recall_pct')-f(base,'recall_pct'):+.4f}",f"{1e6/f(x,'qps')-1e6/f(base,'qps'):+.2f}",f"{f(x,'scanned_codes_per_query'):.1f}" if m not in ['GT10','B32'] else '—',f"{f(x,'sq8_scores_per_query'):.1f}"])
 compare=[]
 for x in new:compare.append([x['method'],x['L'],x['target_GT_L'] or '未覆盖',f"{f(x,'target_speed_delta_pct'):+.2f}",x['budget_GT_L'] or '未覆盖',f"{f(x,'budget_recall_delta_pp'):+.4f}",'是' if x['dominated_by_GT_L'] else '否'])
 coverage=[[x['method'],x['L'],x['missing_members'],x['pool_covered'],x['scanned_covered'],x['shortlist_covered'],x['rescued']] for x in cov]
 fail=[[x['method'],x['L'],x['members_rescued'],x['members_damaged'],x['rescued_source_out'],x['original_lt10'],x['final_lt10'],x['lt10_improved'],x['lt10_escaped'],x['new_lt10']] for x in pairs]
 costs=[]
 formal_role='formal_selected' if sel['cascade_triggered'] else 'formal'
 for role in ['prepare','qualification','calibration']+(['calibration_cascade'] if sel['cascade_triggered'] else [])+[formal_role]:
  x=json.loads((R/f'reviews/{role}_coco.receipt.json').read_text());costs.append([role,f"{x['seconds']:.3f}",f"{x['peak_sampled_rss_bytes']/2**20:.2f}",x['max_observed_threads']])
 arrays=[[k,f"{env[k]/2**20:.3f}"] for k in ['old_backend_bytes','block_backend_bytes','reuse_array_bytes','sq8_code_bytes','sq8_trained_bytes','sq8_idpos_bytes']]
 conclusion=f"{len(new)}个新评分点中{dom}个被实测GT10同时覆盖；速度筛选通过{speed}点，预算Recall筛选通过{budget}点。"
 if speed or budget:judgment='出现探索价值，但有限网格/单图/曝光查询证据不足以替换默认；需冻结独立确认及迁移。'
 else:judgment='该固定评分版本尚未形成可支付的Recall–QPS改进，停止本版本，默认E99 GT10保持。'
 sq=pair('SQ8-96',200);pq=pair('REUSE-BLOCK',200);sqpoint=get('SQ8-96',200);pqpoint=get('REUSE-BLOCK',200)
 effect=f"L200下，SQ8相对原PQ的Recall增量为{f(sqpoint,'recall_pct')-f(pqpoint,'recall_pct'):+.4f}pp；救回成员{pq['members_rescued']}→{sq['members_rescued']}，完整QPS{f(pqpoint,'qps'):.2f}→{f(sqpoint,'qps'):.2f}。新增近似评分的质量与完整费用分别报告。"
 condition=f"预先固定的PQ384-SQ8条件{'触发' if sel['cascade_triggered'] else '未触发'}：校准L200 SQ8−PQ={sel['L200_SQ8_minus_PQ_recall_pp']:+.4f}pp，SQ8探索门={sel['SQ8_passes_GT10_exploration_screen']}，PQ384遗漏覆盖/SQ8-96遗漏覆盖={sel['coverage_ratio']:.4f}（门槛0.75）。未试其他短名单宽度。"
 lines=['# E190：COCO固定候选的排序质量与完整费用','2026-10-28。COCO raw-IP、真实K100、完整单线程；默认E99 GT10保持。',conclusion,judgment,effect,'## 固定候选与评分方法','候选沿E189：三个入口每hub8块加主返回最高8块，合并最多32，原metric中心排序，整块扫描≤2048。所有评分版本逐query候选pool、块选择/顺序完全一致。旧PQ96沿原代码；SQ8-96对同一扫描ID使用逐维8bit近似IP，再最多96次原metric精算/严格合并。SQ8不创建无用PQ LUT；费用差包括实际准备工作。','SQ8使用原C++Faiss静态库QT_8bit、RS_minmax arg0，在全部原base训练及编码，不读取query/GT；码按原block ID布局保存。解码公式含(code+0.5)/255，非对query/base作新归一化。编码从另一实现全base逐字核对一致。','## 固定L200完整表现',md(['方法','Recall@100','完整QPS','增量pp','额外μs/query','扫码/query','SQ8评分/query'],key),'QPS为同一新二进制三轮中位数；完整Batch分配初始化、原路由/主搜、所有补全、六数组复制与销毁。旧E189绝对QPS不拼接；零NDC布局不是0次距离计算。B32原生Stats0是未插桩，候选精算费用已计wall。','## 全部新评分点的实际预算比较',md(['方法','L','阈值GT L','速度差%','预算GT L','Recall差pp','被GT覆盖'],compare),'阈值参照为达到候选Recall的最快已测GT10，其Recall可能更高；预算参照为QPS不低于候选的最高Recall已测GT10。有限离散网格，不称精确等Recall，不插值作通过判定。另保留全部B32/PQ参照，不能仅击败旧PQ就宣称优于已有补全。','## 全量覆盖链',md(['方法','L','原遗漏','池覆盖','扫描覆盖','短名单覆盖','最终救回'],coverage),'trace从实际timed GT10主包在wall外全排序重建；不是另存timed内部trace。池覆盖/扫描覆盖未支付全部原metric评分费用，不能当作免费Recall。源外救回的旧来源是E183原16K完整遗漏源，并非截断B32或新12K源。','## 校准与条件后继',condition,'原16K前12K形成冻结入口块表，后4K只按预先协议决定是否执行唯一384两级方案。旧16K B32含后4K标签，完全排除校准；正式保留历史参考，非训练量匹配对照。选定执行范围在读取本轮正式质量前保存selection.json。原GT10复用和历史公共测试曝光仍披露。','## 逐query救损与严格严重失败',md(['方法','L','成员救回','损伤','旧源外','原<10%','现<10%','原失败改善','脱离','新增'],fail),'失败严格为GT100交集0–9，恰好10不算。成员恢复、完整查询恢复、低召回改善及脱离分别计数；稀少尾部不外推。5000次配对bootstrap只是描述，无多比较或语义IID保证。','## 实际费用',md(['阶段','suite秒','采样RSS MiB','最大观察线程'],costs),md(['辅助数组payload','MiB'],arrays),'新增SQ8码57.75MiB，另有trained与运行时ID→位置映射；旧区域/PQ/块/入口表数组负担仍在。共同benchmark装载的RSS不是单独部署增量；GT10生产不依赖SQ8后端。suite含内部timed wall，不能重复相加。旧GT/图/PQ/块/教师构建成本沿原证据继承，不清零。','## 核验与证据边界',f"正式{len(points)}点/{len(points)*3}轮；primary校准{len(cal)}点/{len(cal)*3}轮"+('，另条件校准6点/18轮。' if sel['cascade_triggered'] else '。'),f"{audit['historical_packets_equal']}个旧控制完整返回包一致；实际timed包三轮bits/SHA、全量主包补全oracle、每query2048/96上限、第二份stdlib set质量与预算比较通过。原E189 {audit['old_E189_seal_files_unchanged']}件seal保持。SQ8/PQ短名单阈值及原metric返回分数另以float64抽核。",'全部是同一执行者的不同实现，非独立人员复现。只有COCO/K100、一套图/画像与历史曝光test；无新K1/Deep或其他集/新盲确认。编码改进本身属于既有量化工具，未据此主张算法创新。','## 下一边界',('保留通过点作冻结确认候选，再检查相邻L/新查询及迁移；默认替换另判。' if speed or budget else 'COCO固定评分版本收口。Deep后续可先诊断全块代表排序的覆盖机会，再决定是否做块代表ANN；本轮未执行。'),'[协议](protocol.md) · [冻结](freeze.json) · [条件决定](selection.json) · [全部实测点](analysis/points.csv) · [配对救损](analysis/paired.csv) · [预算比较](analysis/discrete_comparisons.csv) · [核验](reviews/formal_results_audit.json)']
 (R/'report_zh.md').write_text('\n\n'.join(lines)+'\n')
 def page(title,no):
  fig=plt.figure(figsize=(12,8));fig.suptitle(title,y=.94,fontsize=18);fig.text(.05,.035,f'E190 | 2026-10-28 | COCO raw-IP / K100 / T1 / 历史曝光 | {no}/6',fontsize=9,color='#64748b');return fig
 def table(fig,headers,rows,box,size=10):
  ax=fig.add_axes(box);ax.axis('off');tb=ax.table(cellText=rows,colLabels=headers,cellLoc='center',loc='center');tb.auto_set_font_size(False);tb.set_fontsize(size);tb.scale(1,1.75)
  for (i,j),cell in tb.get_celld().items():cell.set_edgecolor('#dce2e9');cell.set_facecolor('#e8f0f8' if i==0 else ('#f6f8fa' if i%2==0 else 'white'))
 def texts(fig,ls,y=.80,step=.07,size=12):
  for s in ls:fig.text(.065,y,s,fontsize=size,va='top');y-=step
 with PdfPages(R/PDF) as out:
  fig=page('固定扫描目标，改善排序能否换来有效补全？',1);texts(fig,[conclusion],y=.84,size=12);table(fig,['方法 L200','Recall@100','完整QPS','增量pp','额外μs','扫码','SQ8评分'],key,(.04,.32,.92,.46),10);texts(fig,['正式点来自同一二进制、同一套原图和入口；新方法均最多96次原metric精算。','SQ8训练仅原base，无query/GT；码57.75MiB，旧后端负担仍需支付。',judgment],y=.25,step=.06,size=11);out.savefig(fig);plt.close(fig)
  fig=page('Recall–QPS：完整线上费用与实际预算控制',2);ax=fig.add_axes((.09,.20,.65,.62))
  for m in methods:
   pp=sorted([x for x in points if x['method']==m],key=lambda x:int(x['L']));x=[f(z,'recall_pct') for z in pp];y=[f(z,'qps') for z in pp];err=[[f(z,'qps')-f(z,'qps_min') for z in pp],[f(z,'qps_max')-f(z,'qps') for z in pp]];ax.errorbar(x,y,yerr=err,marker='o',ms=4,label=m,capsize=2)
  ax.set_xlabel('Recall@100 (%)');ax.set_ylabel('完整单线程 QPS');ax.grid(alpha=.2);ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=10);fig.text(.09,.11,'GT10含20档真实L；补全仅L100/200/400。线段连接实测点，误差线为三轮范围。',fontsize=11);fig.text(.09,.075,'同L质量变化、跨L费用优势和已有B32收益分别判断；三轮计时不是三份质量样本。',fontsize=10);out.savefig(fig);fig.savefig(R/'reviews/recall_qps.svg');plt.close(fig)
  fig=page('全query覆盖链：同样扫描到了什么，保住多少？',3);table(fig,['方法','L','原遗漏','池覆盖','扫描覆盖','短名单','最终救回'],coverage,(.03,.30,.94,.53),9);texts(fig,['所有评分版本逐query pool和扫描块/顺序完全一致，扫码上限2048。','评分短名单最多96，最终保留还依赖原metric精算和严格Top100合并。','覆盖链由实际主包重建oracle trace，扫描覆盖不等于免费在线召回。'],y=.24,step=.055,size=11);out.savefig(fig);plt.close(fig)
  fig=page('相对GT10的实际预算门：所有新评分点',4);table(fig,['方法','L','阈值GT L','速度差%','预算GT L','Recall差pp','被GT覆盖'],compare,(.04,.42,.92,.39),10);texts(fig,['速度门：达到候选Recall的最快已测GT10参照上，QPS至少+2%且三轮同向。','质量门：候选费用内最好已测GT10之上，Recall至少+0.05个百分点。','有限网格筛选仅决定探索价值；不称精确等Recall，不自动替换默认。',f"条件PQ384-SQ8：{'触发' if sel['cascade_triggered'] else '未触发'}；校准PQ384/SQ8-96遗漏覆盖比 {sel['coverage_ratio']:.4f}，门槛0.75。"],y=.35,step=.065,size=11);out.savefig(fig);plt.close(fig)
  fig=page('救损、严重失败与统计边界',5);table(fig,['方法','L','救回','损伤','源外','原<10%','现<10%','改善','脱离','新增'],fail,(.035,.26,.93,.57),8.5);texts(fig,['严重失败为每query命中GT100的0–9个；恰好10命中排除。','成员救回、查询改善和脱离严重失败分别计数，不能互相代替。','配对区间只作描述；单图、公共test历史曝光、没有新的独立确认。'],y=.21,step=.05,size=11);out.savefig(fig);plt.close(fig)
  fig=page('实际成本、角色与可复核交付',6);table(fig,['阶段','suite秒','采样RSS MiB','线程'],costs,(.05,.48,.55,.34),9);table(fig,['辅助数组','MiB'],arrays,(.64,.48,.32,.34),8);texts(fig,['SQ8全base训练、无query/GT；入口块表前12K fit，末4K按冻结条件决定后继。','旧B32含校准标签，排除选择，仅正式参考；完整wall已包含于suite，费用不相加。',f"正式{len(points)}点/{3*len(points)}轮；旧控制{audit['historical_packets_equal']}点全包一致，E189封存1570件保持。",'返回三轮bits/SHA、全量补全oracle、预算、原metric分数和第二实现质量核验通过。','不同实现同一执行者，非独立人员复现；仅COCO/K100，未扩展Deep/K1。',judgment],y=.43,step=.058,size=10.5);out.savefig(fig);plt.close(fig)
 rec=dict(status='PASS_E190_REPORT_BUILD',pages=6,formal_points=len(points),primary_calibration_points=len(cal),cascade_calibration_points=6 if sel['cascade_triggered'] else 0,new_points=len(new),dominated=dom,speed_screen=speed,budget_recall_screen=budget,conclusion=conclusion,judgment=judgment,seconds=time.perf_counter()-t)
 (R/'reviews/report_build.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n');print(json.dumps(rec,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
