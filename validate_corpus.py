import csv, re
from pathlib import Path

D = Path('data/shopee-policies')
REQ = ['doc_id', 'title', 'source_url', 'retrieved_at', 'document_version', 'audience']
mds = sorted(D.glob('*.md'))
rows = list(csv.DictReader(open(D / 'sources.csv', encoding='utf-8')))

ids = []
auds = {}
for p in mds:
    fm_text = p.read_text(encoding='utf-8').split('---')[1]
    fm = dict(re.findall(r'^(\w+):\s*(.+)$', fm_text, re.M))
    ids.append(fm.get('doc_id'))
    auds[fm.get('audience')] = auds.get(fm.get('audience'), 0) + 1
    ok = all(k in fm for k in REQ) and fm.get('doc_id') == p.stem
    status = "OK" if ok else "THIEU METADATA"
    print(f"{p.name:50} {status}")

print(f"\nSo file : {len(mds)} (can 5-10)")
csv_ids = sorted(r['doc_id'] for r in rows)
print(f"csv khop: {'khop' if csv_ids == sorted(ids) else 'LECH'}")
print(f"audience: {auds}")
print(f"Du 2 gia tri khac nhau: {len(auds) >= 2}")
