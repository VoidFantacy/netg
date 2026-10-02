import hashlib,json,shutil,struct,time,urllib.request
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text())
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return h.hexdigest()
def key(row):return hashlib.sha256(row.tobytes()).digest()
def fetch(url,start,end,total,path):
    attempts=[]
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'})
            with urllib.request.urlopen(request,timeout=60) as response:
                assert response.status==206 and response.headers['Content-Range']==f'bytes {start}-{end}/{total}'
                data=response.read(end-start+2);assert len(data)==end-start+1;headers=dict(response.headers)
            attempts.append({'attempt':attempt,'status':'PASS','bytes':len(data),'unix':time.time()});break
        except Exception as e:
            attempts.append({'attempt':attempt,'status':'FAIL','error':repr(e),'unix':time.time()})
            (R/'reviews/network_attempts.json').write_text(json.dumps({'url':url,'range':[start,end],'attempts':attempts},indent=2)+'\n')
            if attempt==2:raise
    with Path(path).open('xb') as f:f.write(data)
    return data,{'url':url,'range':[start,end],'status':206,'headers':headers,'sha256':hashlib.sha256(data).hexdigest(),'attempts':attempts}
def main():
    started=time.perf_counter();models=json.loads((R/'reviews/models_before_source.json').read_text());assert models['status']=='FROZEN_BEFORE_NEW_SOURCE';allrecords={}
    for path,v in models['files'].items():assert Path(path).stat().st_size==v['bytes'] and sha(path)==v['sha256']
    for ds,dc in C['datasets'].items():
        d=dc['dimension'];src=Path(dc['dataset_dir']);manifest=json.loads((src/'manifest.json').read_text());seen=set();excluded=[]
        for name,v in manifest['files'].items():
            if not(name.startswith('query.') and name.endswith('.fvecs')):continue
            p=src/name;assert sha(p)==v['sha256'];a=np.memmap(p,'<f4',mode='r').reshape(-1,d+1);assert (a[:,0].view('i4')==d).all()
            seen.update(key(row) for row in a[:,1:]);excluded.append({'path':str(p),'rows':len(a),'sha256':v['sha256']})
        for path in dc['excluded_extra_files']:
            a=np.fromfile(path,'<f4').reshape(-1,d);seen.update(key(row) for row in a);excluded.append({'path':path,'rows':len(a),'sha256':sha(path)})
        prefixmeta=None
        if dc['source_kind']=='HTTP_Range':
            prefix,prefixmeta=fetch(dc['source'],0,8+16*d*4-1,40000000008,R/'inputs'/f'{ds}.prefix.bin')
            with (src/'source/query.learn.first45K.fbin').open('rb') as f:assert prefix==f.read(len(prefix))
            assert struct.unpack('<II',prefix[:8])==(50000000,d)
        for batch in range(2):
            case=f'{ds}_b{batch}';c=C['cases'][case];out=R/'inputs'/case;out.mkdir();begin=time.perf_counter()
            assert shutil.disk_usage(R).free>=C['min_free_bytes'] and time.time()<C['deadline_unix']
            first=c['source_start'];count=c['candidate_count'];n=c['n']
            if dc['source_kind']=='local':
                source=Path(dc['source'])
                with source.open('rb') as f:
                    assert struct.unpack('<II',f.read(8))==(2500000,d);f.seek(8+first*d*4);data=f.read(count*d*4)
                assert len(data)==count*d*4
                with (out/'candidate_source.f32').open('xb') as f:f.write(data)
                st=source.stat();provenance={'source':str(source),'source_rows':[first,first+count],'source_stat':{'bytes':st.st_size,'mtime_ns':st.st_mtime_ns},
                    'slice_sha256':hashlib.sha256(data).hexdigest(),'inherited_full_source_sha256':manifest['local_sources']['source/webvid.query.train.2.5M.fbin']['sha256']}
            else:
                start=8+first*d*4;end=start+count*d*4-1;data,provenance=fetch(dc['source'],start,end,40000000008,out/'candidate_source.f32')
                assert provenance['headers'].get('ETag')==prefixmeta['headers'].get('ETag')
                provenance.update(header_verification=prefixmeta,local_prefix_bytes_match=True,source_rows=[first,first+count])
            a=np.frombuffer(data,'<f4').reshape(count,d);queries=[];rows=[];duplicates=invalid=0
            for j,row in enumerate(a):
                if not np.isfinite(row).all() or np.linalg.norm(row)==0:invalid+=1;continue
                h=key(row)
                if h in seen:duplicates+=1;continue
                seen.add(h);queries.append(row);rows.append(first+j)
                if len(rows)==n:break
            assert len(rows)==n,'insufficient fresh queries in frozen window'
            q=np.array(queries,dtype='f4');q.tofile(out/'queries.f32');np.array(rows,dtype='i8').tofile(out/'source_rows.i64')
            record={'status':'PASS_SOURCE_AND_DEDUP','case':case,'dataset':ds,'n':n,'dimension':d,'source':provenance,'excluded_files':list(excluded),
                'duplicates_skipped':duplicates,'invalid_skipped':invalid,'new_vs_known_inputs_byte_overlap':0,'selected_queries_unique':True,
                'selection':'first eligible source rows; no GT or model outputs','seconds':time.perf_counter()-begin,'unix':time.time(),
                'files':{p.name:sha(p) for p in out.iterdir() if p.is_file()},'scope':'no known registered/exposed byte overlap; not semantic independence or exhaustive unregistered exposure'}
            dump(out/'manifest.json',record);allrecords[case]=record
            excluded.append({'path':str(out/'queries.f32'),'rows':n,'sha256':sha(out/'queries.f32')});print(case,'FROZEN',n,'excluded',duplicates,flush=True)
    for path,v in models['files'].items():assert sha(path)==v['sha256']
    dump(R/'reviews/query_freeze.json',{'status':'ALL_FOUR_CASES_FROZEN_BEFORE_GT','unix':time.time(),'seconds':time.perf_counter()-started,'cases':allrecords})
if __name__=='__main__':main()
