# 夜间执行台账

- 2026-09-07 23:54 北京时间：恢复授权，完整读取交接，保护源码/文档快照，P0/P1 并行准备。
- 当前阶段：P0/P1 未通过；P2–P8 NOT_STARTED。
- 资源：启动时可用 RAM 约120 GiB，/data 空闲约20 GiB；仅单个重数据集进程。
- 控制：control/taskctl.py；正式 watchdog 已启动，06:59 soft-stop，07:00 hard deadline。
- 下一行动：通过输入审计和独立纯 timer/正确性检查，再启动 P2 机制对照。
- 文件删除：无。

- 2026-09-07T16:05:27.369084+00:00：P0 PASS；full审计35.27秒，两个图输入一致/无非法边；68固定点/数据集图内外base字节一致。P1：paired20K Fast及真实数据plain/count/legacy验收待完成。

- 2026-09-07T16:13:54.125082+00:00：P1 PASS；双数据集512查询×L64/128真实同入口kernel/count/plain/5round身份一致，m4/6/8各32查询全部入口被实际消费；累计实值核验84.37秒，最大RSS10.20GiB。下一步P2固定64区域机制对照，不训练完整层次模型。

- 2026-09-07T16:18:11.789385+00:00：启动WebVid固定64仅图分区；METIS CPU单线程，CSR行排序16线程；mmap只读adjacency，不复制base/图，labels输出约5MB。预计10分钟初值，观察1分钟后更新。

- 2026-09-07T16:20:35.612328+00:00：首个WebVid分区28.12秒后因容量/空区检查FAILED，未进入评测。METIS内部ubfactor额外+0.0000499（options.c:121），尚待实值sizes确认原因；保持门槛，先修失败诊断保存。原产物p2/webvid_partition/manifest.json为INCOMPLETE，labels未生成。

- 2026-09-07T16:24:10.549538+00:00：容量失败证据确认，12区各超2节点；补偿METIS内部epsilon以落实原1.2硬约束，原参数/门槛不变。记录partition_contract_amendment_v1.json，机制修订计数仍0。

- 2026-09-07T16:26:42.405573+00:00：WebVid strict-v3分区COMPLETE，最大46968=hardcap，64区全覆盖/非空，METIS25.49秒、总27.78秒，peakRSS5.85GiB；epsilon契约问题解除，开始仅20K画像/门户。

- 2026-09-07T16:31:16.764485+00:00：Yandex strict-v3分区COMPLETE，max187499<=187500，64区全覆盖非空；METIS155.56秒、总171.64秒，peakRSS约33.9GiB。两个分区入模契约通过，准备10K pilot五项对照。

- 2026-09-07T16:33:33.375597+00:00：WebVid P2完整count/timing5round/trace16完成，耗时62.47秒，peakRSS6.12GiB；初值显示oracle保护与真实几何保护相反，仅为待复核pilot观察。开始同协议Yandex，禁止据单数据集过gate。

## 2026-09-07T16:43:12.511049+00:00 P2 measurements complete; mechanism review
Both datasets count/plain/full-route/five-round checks PASS. Real geometric protected queues harm Recall and wall; oracle protected queues improve Recall at higher cost. Analysis p2/analysis_v1. Started saved-trace replay p2_trace_analysis_v1. No P2 gate yet; P3 not started; validation/heldout untouched. Handoff stale stage blocks consolidated with snapshots retained.

## 2026-09-07T16:58:59.343451+00:00 P2 PASS: limited oracle/prediction mechanism gate
P2 gate saved gates/P2.json with all source/evidence SHA. Saved capacity audit COMPLETE, equalcapacity mismatches0; geometric weights nearlyuniform, top4selectiongap localized. RealP2 negative andoraclemorecost retained. Preregistered p3/protocol.json beforeP3implementation/data: common16x16init, directedleafJ lambda0/1 exact2passes, coarseinit1.1/finalbothlevels1.2, frequency3/greedy3 2x2 fixed768portals. P3 counts as firstrepresentationrevision. P4 stillgateblocked.

## 2026-09-07T17:35:18.495913+00:00 P3 structure implementation accepted; real builds
Partition source78cd1347/release3f379668: 11 synthetic groups,336 exact delta cases, independent lambda0/full-J references, full256 two-pass fixture, ASan/UBSan/leaks PASS. WebVid build COMPLETE40.03s peak6.10GiB: lambda0 J1=.75645687, mean fitGT10 regions4.33285; lambda1 J1=.56807908, mean2.60275, strict caps PASS. Training structure only; no pilot benefit claim. Yandex single heavy build running; no other heavy process; watchdog ARMED, artifact1.34GiB/free18.67GiB. Next fixed two-branch portal suite then P1 256-leaf real acceptance and four-model oracle pilot.

## 2026-09-07T17:43:07.523686+00:00 P1 P3 reacceptance PASS; start full oracle pilot
Both portal suites completed and all256 caches independently rechecked; fixed four models per dataset retained incl negative per-leaf proxy cases. Actual32 count/plain5 and4 trace queries eachdataset PASS,16 traces/dataset; Fast matches old64 acceptance. gates/P1_P3_reacceptance.json binds evidence and current evaluator2f234d12/sourcecf40032d. Full four-model count10K/plain5 pilot starts WebVid; no model choice, no P4 or heldout.

## 2026-09-07T18:06:54.694924+00:00 P3 completed NOPASS; bounded frozen-model diagnosis
Structure conditions bothPASS. Mainoracleλ1greedy−0greedy: Web−.866/−.790pp negative95CI; Yan−.095/−.017pp intervalsinclude0. Full8portalcontrastsuncertain;16oraclequeueprotectionpositivewithhigherNDC/lowerQPS. gates/P3.json NOPASS independentlyreviewed. No P4/validation/heldout/newmodel. Preregistereddiagnosis4bdd1cd9 targetgeneralization+portalexposure, no newCI/refit. FrozenP2remaining7originaltraceIDs planned, noCI/gatechange. Metadataaddenda preserveoriginalanalysis andFast unmeasuredcounters.

## 2026-09-07T18:14:34.011299+00:00 P2 original trace evidence complete
UnchangedP2binary/source,remaining7originalIDs/ds only;140newtrace rows matchfull10Kcounts exactly. Completion114.47s;full460trace/276pairreplay12.05sPASS,all23IDsall12dataset/L/comparisoncells. Supplementarymetadata only; originalP2/P3gatesunchanged. Noheavyactive; P3frozendiagnosticsawaitindependentreview.

## 2026-09-07T18:21:32.925692+00:00 Portal exposure diagnosis complete
Frozen e76ad337 source + 25 author/33 independent tiny checks; controlled job14.06s, application12.00s, rusage457012KiB. All8cells10K actualentrysetschange; previousallRecall/pairedsign/counterresultsreproduced. ReturnIDsetequal68.34–93.36%; six Weblambda1 weightedexposuresundefined. NoGT/labels/graph/queryreads,ANN0,newCI0,gateunchanged. Targetdiagnosisreviewpending; noheavyactive.

## 2026-09-07T18:34:13.300322+00:00 Target generalization diagnosis complete; finite local-scale protocol
Target app13.1755s/job14.0602s/rusage435476KiB,allGT-IDhits/oracle/globaltop4/40contrasts+440stratareconciled. Web partialconcentrationtransfer(M4+1.808pp)withseen-targetRecallloss;Yanfitconcentrationlargelyfailsaggregatepilottransfer(M4−.004pp). Noall-unseenfailureexplanation,noRecallupperboundfromM4. Frozenobjective_local_scale_protocol_v1 abae80a4 beforeimplementation/data, motivatedbytargetevidence+independentmathPASS719cd9d; noCI/tuning/newmodel/gate. Reportingredients72measurement/60contrasttablesindependentlyreconciled;twoexisting-evidencefiguresvisuallychecked. Originalreportstillabsent,onlyafter23UTC.

## 2026-09-07T18:56:24.378784+00:00 Frozen diagnoses complete; consolidate handoffs
Local-scale job COMPLETE28.11475s/application27.23485s/rusage788028KiB. All118811/188913 fit-seen targets satisfy d*9Q<M; occurrence-weighted100%, both datasets31groups independently reconciled. All three bounded diagnoses complete; no new ANN/model/CI/gate. P3 NOPASS, P4-P8 prohibited. Three handoffs/current_findings/state synchronized; snapshot hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/handoff_snapshots/20260907T185624Z. No heavy task active; deadline watchdog remains armed. Final report only after23UTC stop verification.

## 2026-09-07T18:57:27.141310+00:00 Pure-algebra local comparison addendum accepted
Frozen choose_move integer score verified by root; independent4374candidate-pairs/1944subsets PASS. At fixed current labels/candidates/feasibility, allnodes lambda1 comparisons prioritize integer deltaS then deltaC; stay zero ties retained, strictly improving move ties lowestleafID. No globaloptimum/trajectory/Recallcausal claim. Current findings and threehandoffs synchronized; gate unchanged.

## 2026-09-07T19:00:50.274381+00:00 Validation access wording clarified from existing P0 source/audit
P0 read validation query/GT for header/fullSHA, query fingerprints/duplicates/overlap/finite and GT ID range/duplicates; no fitting/selection/ANN performance. Heldout never opened. Earlier broad unread prose superseded by p0/validation_access_scope_addendum_v1.json; all immutable artifacts retained, no dataset reread or gate change. Current findings/state/three handoffs updated.

## 2026-09-07T19:02:48.561557+00:00 Research launch closed early; wait for required deadline
P3 NOPASS and all bounded diagnoses complete. Scanned registered tokens across all PGIDs: no active task process. control/CLOSED.json prevents new task launches; watchdog remains until23UTC. Only existing-evidence/doc review and monitoring now. This is not finaldeadlineverification or longtermgoal completion.

## 2026-09-07T22:59:30.128890+00:00 06:59 checkpoint
Research launch alreadyclosed, globaltoken/PGID scan has noactive taskprocess; no terminationrequired, no signals sent. Current state/findings/report ingredients/handoffs checkpoint hashes incontrol/milestone_0659.json. Await23UTC finalwatchdog+independentprocess verification beforeformalreport.

## 2026-09-07T23:01:24.825137+00:00 Final deadline stop PASS
Watchdog recordedallstoppedat23:00:00.312452UTC; independent/proc registeredtokens/allPGIDs+leaderstartidentity+newtaskexecutable scan hasnoactive matches;watchdogsameidentitynotactive. No signals, nojobsendedafterdeadline. Now existing-evidence/doc report only;longtermresearchunfinished.

## 2026-09-07T23:10:04.760519+00:00 Report written afterstop; final handoffs synchronized
实验总结.md created23:06:00UTC afterfinalstop; firstparagraph4sentences104characters. Finalsource/settings/CMakeprotection and34heavynonoverlap auditPASS. Threehandoffs/currentfindings/state nowreflect stoppedwatchdog/noactivejobs/completeP3NOPASS, reportdocumentreviewpending; no newexperiment. Snapshot hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/handoff_snapshots/20260907T231004Z.

## 2026-09-07T23:14:26.903137+00:00 Final report delivery complete
Report /data/netg/ACSG/实验总结.md SHA4bda0c093a3169fbe2f376d756ac2f718e2f5f7b83b83b55646ba40444651d54 independentreviewPASS0substantive/blockingissues. Four-sentence104-character opening,20measurementrows/4primaryCIs/26costvalues source-matched, oracle/split/causal/cost boundaries verified. Finalstop/sourceprotection/resources and all handoffs/state complete. Timeboxed execution/report fulfilled;longtermresearchunfinished;P3NOPASS,P4-P8notrun. No postdeadline experiments.
