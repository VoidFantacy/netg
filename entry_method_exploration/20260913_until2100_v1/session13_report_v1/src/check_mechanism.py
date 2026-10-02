"""Small-table arithmetic only; existing E60/E89 raw responses remain untouched."""
from pathlib import Path
import csv,json,hashlib,time
O=Path(__file__).resolve().parents[1];C=O.parent;DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
files=[C/'stage1_support_v1/protocol.md',C/'stage1_support_v1/results/actions.csv',
       C/'stage30_local_parent_restore_v1/protocol.md',C/'stage30_local_parent_restore_v1/src/train.py',
       C/'stage30_local_parent_restore_v1/supplement_training_v1/derivation.json',O/'mechanism_note.md',Path(__file__)]
for ds in DS:
    files.extend(C/'stage30_local_parent_restore_v1/results'/ds/'fit'/x for x in ['action_statistics.json','union_statistics.json'])
seal=O/'reviews/mechanism_input_freeze.json';assert not seal.exists()
seal.write_text(json.dumps(dict(epoch=time.time(),files=[dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]),ensure_ascii=False,indent=2)+'\n')
with files[1].open() as f:actions=list(csv.DictReader(f))
rows=[]
for i,ds in enumerate(DS):
    a=[r for r in actions if r['dataset']==ds];assert len(a)==120
    aux=sum(r['aux_quality_null']=='True' for r in a);transfer=sum(r['transfer_quality_null']=='True' for r in a)
    assert (aux,transfer)==[(108,93),(114,120)][i]
    positive=[r for r in a if int(r['aux_net_hits'])>0]
    assert len(positive)==[9,0][i] and all(r['train_legal']=='False' for r in positive)
    assert not any(r['auxiliary_supported']=='True' for r in a)
    p=C/'stage30_local_parent_restore_v1/results'/ds/'fit';b=json.loads((p/'action_statistics.json').read_text());u=json.loads((p/'union_statistics.json').read_text())
    mixed=sum(r['gain_hits']>0 and r['loss_hits']>0 for r in b)
    additive=sum(r['net_hits'] for r in b if r['accepted']);merged=next(r['net_hits'] for r in u if r['model']=='restore10')
    assert len(b)==32 and (mixed,additive,merged)==[(31,297,224),(26,125,114)][i]
    rows.append(dict(dataset=ds,E60_actions=120,E60_aux_null=aux,E60_transfer_null=transfer,E60_aux_positive=len(positive),E60_supported_states=0,E89_mixed_actions=mixed,E89_selected_sum=additive,E89_merged=merged))
r=dict(status='PASS_SMALL_TABLE_MECHANISM',records=rows,new_raw_scoring=0,new_ANN=0,new_training=0,scope='Different action families and data roles; no shared-representation impossibility or final per-profile causal claim')
(O/'reviews/mechanism_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
