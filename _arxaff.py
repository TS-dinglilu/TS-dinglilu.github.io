import re, sys, urllib.request, gzip, io

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    r = urllib.request.urlopen(req, timeout=60)
    d = r.read()
    if r.headers.get('Content-Encoding') == 'gzip':
        d = gzip.decompress(d)
    return d.decode('utf-8', 'ignore')

for aid in sys.argv[1].split(','):
    try:
        h = get(f'https://arxiv.org/html/{aid}v1')
    except Exception as e:
        print(aid, 'ERR', e); continue
    m = re.search(r'<div class="ltx_authors">(.*?)</div>', h, re.S)
    if not m:
        m = re.search(r'(<h1.{0,60}</h1>)(.{0,4000}?)(abstract)', h, re.S)
        blob = m.group(0) if m else h[:4000]
    else:
        blob = m.group(1)
    txt = re.sub(r'<script.*?</script>', '', blob, flags=re.S)
    txt = re.sub(r'<[^>]+>', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()
    print('==', aid, '::', txt[:700])
