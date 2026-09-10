#!/usr/bin/env python3
import hashlib,json,copy
from pathlib import Path
import numpy as np

RUN=Path(__file__).resolve().parents[1];OUT=RUN.parent
DATASETS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];LS=[64,128,256,400,800]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()
def dump(path,obj):Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')

def main():
    configs=[];manifest={'threads':1,'queries_per_dataset':2000,'seed':20260828,'L':LS,'heldout_accessed':False,
                         'same_joint_model_across_all_L':True,'joint_training_label_L':128,'datasets':{}}
    for linked in json.loads((OUT/'reviews/linked_sources_verified.json').read_text()):
        assert sha(linked['path'])==linked['sha256'],linked['path']
    frozen=json.loads((OUT/'inputs/evaluation/validation/models_frozen_before_evaluation.json').read_text())
    for record in frozen['files']:assert sha(record['path'])==record['sha256'],record['path']
    manifest['frozen_model_files_verified']=len(frozen['files'])
    for di,ds in enumerate(DATASETS):
        original=OUT/'inputs/evaluation/validation'/ds/'seed20260828.json';c=json.loads(original.read_text());d=c['dim']
        dest=RUN/'inputs'/ds;assert not dest.exists();dest.mkdir()
        q=np.memmap(c['queries_file'],mode='r',dtype='float32',shape=(10000,d))[:2000].copy()
        gt=np.memmap(c['gt_file'],mode='r',dtype='int64',shape=(10000,100))[:2000].copy()
        rows=np.fromfile(c['row_ids'],dtype='int64')[:2000];assert np.array_equal(rows,np.arange(2000))
        q.tofile(dest/'queries.f32');gt.tofile(dest/'gt.i64');rows.tofile(dest/'row_ids.i64')
        fast=next(m for m in c['methods'] if m['family']=='fast30k_3' and m['L']==128)
        joint=next(m for m in c['methods'] if m['family']=='joint' and m['L']==128)
        variants=[{'family':'nsg_medoid','seed':20260828,'k':1},fast,joint];methods=[]
        for li,L in enumerate(LS):
            offset=(li+di)%3
            for k in range(3):
                m=copy.deepcopy(variants[(k+offset)%3]);m['L']=L;m['name']=m['family']+f'_L{L}'
                if m['family']=='joint':m['training_label_L']=128
                methods.append(m)
        out={'dataset':ds,'split':'validation2000_exploration','dim':d,'num_queries':2000,'gt_k':100,'threads':1,
             'index_path':c['index_path'],'queries_file':str(dest/'queries.f32'),'gt_file':str(dest/'gt.i64'),
             'row_ids':str(dest/'row_ids.i64'),'methods':methods,'L':LS,'timing_repeats':1,
             'protocol_sha256':sha(RUN/'protocol.md')}
        fp=dest/'config.json';dump(fp,out);configs.append(str(fp))
        identities={str(Path(m[k])):sha(m[k]) for m in [fast,joint] for k in ['W','mapping','tie_ids']}
        identities.update({str(dest/name):sha(dest/name) for name in ['queries.f32','gt.i64','row_ids.i64']})
        manifest['datasets'][ds]={'config':str(fp),'sha256':identities,'source_validation_config':str(original),
            'source_config_sha256':sha(original),'fixed_joint_W_sha256':sha(joint['W']),
            'fixed_joint_mapping_sha256':sha(joint['mapping']),'row_range':[0,2000],
            'frozen_graph_source':'Original input preflight and linked source manifests; graph unchanged'}
    manifest['configs']=configs;manifest['status']='PREPARED';dump(RUN/'inputs/manifest.json',manifest)
    print(json.dumps({'status':'PREPARED','configs':configs,'same_model_for_all_L':True}))

if __name__=='__main__':main()
