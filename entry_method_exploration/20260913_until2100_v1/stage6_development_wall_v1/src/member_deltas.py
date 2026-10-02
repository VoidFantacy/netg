"""Post-hoc member-set accounting. Does not run ANN or alter paired.csv."""
from pathlib import Path
import csv,json,array,time
O=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((O/'results/paired.csv').open()))
output=[]
def masks(path):
    a=array.array('H');a.frombytes(path.read_bytes());assert len(a)==2048;return a
for row in rows:
    root=O/'results'/row['dataset'];L=row['L']
    new=masks(root/f'best_new_L{L}'/'hitmask.u16')
    base=masks(root/f"{row['comparator']}_L{L}"/'hitmask.u16')
    gain=sum((a & ~b).bit_count() for a,b in zip(new,base))
    loss=sum((b & ~a).bit_count() for a,b in zip(new,base))
    positive=sum(max(a.bit_count()-b.bit_count(),0) for a,b in zip(new,base))
    negative=sum(max(b.bit_count()-a.bit_count(),0) for a,b in zip(new,base))
    assert gain-loss==int(row['net_hits'])
    assert positive==int(row['gain_hits']) and negative==int(row['loss_hits'])
    assert gain-positive==loss-negative>=0
    output.append(dict(dataset=row['dataset'],L=L,comparator=row['comparator'],
        GT10_members_gained=gain,GT10_members_lost=loss,net_hits=gain-loss,
        positive_query_net_hits=positive,negative_query_net_hits=negative,
        within_query_canceled_member_changes=gain-positive))
with (O/'results/member_deltas.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
(O/'reviews/member_delta_verification.json').write_text(json.dumps(dict(status='PASS',epoch=time.time(),
    comparisons=len(output),paired_csv_unchanged=True,new_ANN=0,
    distinction='paired.gain_hits/loss_hits are positive/negative parts of query net hit changes; member_deltas counts GT10 set gains/losses independently'),indent=2)+'\n')
print(json.dumps(output,indent=2))
