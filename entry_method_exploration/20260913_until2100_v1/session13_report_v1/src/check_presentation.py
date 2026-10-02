from pathlib import Path
from html.parser import HTMLParser
import csv,json,hashlib,re,time
O=Path(__file__).resolve().parents[1];F=O.parent/'stage35_final_comparison_v1'
def csvrows(p):
    with p.open() as f:return list(csv.DictReader(f))
doc=(O/'report.html').read_text(); data=json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',doc,re.S).group(1))
assert data==json.loads((O/'presentation_data.json').read_text())
assert data['points']==csvrows(F/'analysis_v1/points.csv')
expected={}
for r in csvrows(F/'supplement_v1/failed_queries_all_L.csv'):
    key=(r['dataset'],int(r['source_row']),int(r['L']),r['model'])
    expected[key]=(r['namespace'],int(r['hits']),r['GT10'],r['entries'],r['returned'])
actual={}
for q in data['queries']:
    for L,m,h,e,r in q['cells']:
        key=(q['dataset'],q['row'],L,m)
        assert key not in actual
        actual[key]=(q['namespace'],h,' '.join(map(str,q['GT10'])),' '.join(map(str,e)),' '.join(map(str,r)))
assert expected==actual and len(actual)==10730 and len(data['queries'])==401
assert sum(q['dataset'].startswith('web') for q in data['queries'])==271
class Inspect(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[];self.external=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and 'href' in a:self.links.append(a['href'])
        if 'src' in a and not a['src'].startswith('data:'):self.external.append(a['src'])
parser=Inspect();parser.feed(doc)
assert len(parser.ids)==len(set(parser.ids)) and not parser.external
assert all((O/x).exists() for x in parser.links if not x.startswith(('#','data:')))
assert not re.findall(r'(?:fetch\(|XMLHttpRequest|https?://)',doc)
records=json.loads((O/'input_freeze.json').read_text())['files']
for x in records:
    p=Path(x['path']);assert p.stat().st_size==x['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],str(p)
result=dict(status='PASS_COMPLETE_PRESENTATION_DATA',epoch=time.time(),point_rows=50,failure_queries=401,failure_cells=10730,
            field_equality='namespace/source_row/L/model/hits/GT10/entries/returned all equal to E94 CSV',
            input_identities=len(records),unique_HTML_ids=len(parser.ids),local_links=len(parser.links),external_resources=0,
            browser_layout_verified=False,new_raw_scoring=0,new_ANN=0,new_training=0)
(O/'reviews/presentation_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
