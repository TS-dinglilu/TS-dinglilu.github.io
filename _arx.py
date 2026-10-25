import re, sys, urllib.request, urllib.parse

IDS = sys.argv[1].split(',')

def fetch(idl):
    url = 'https://export.arxiv.org/api/query?' + urllib.parse.urlencode({'id_list': idl, 'max_results': 50})
    req = urllib.request.Request(url, headers={'User-Agent': 'daily-report/1.0'})
    return urllib.request.urlopen(req, timeout=60).read().decode('utf-8')

s = fetch(','.join(IDS))
for e in re.findall(r'<entry>(.*?)</entry>', s, re.S):
    idm = re.search(r'<id>(.*?)</id>', e).group(1).split('/abs/')[-1]
    t = re.sub(r'\s+', ' ', re.search(r'<title>(.*?)</title>', e, re.S).group(1).strip())
    pub = re.search(r'<published>(.*?)</published>', e).group(1)[:10]
    authors = [re.sub(r'\s+', ' ', a) for a in re.findall(r'<name>(.*?)</name>', e)]
    aff = re.findall(r'<arxiv:affiliation[^>]*>(.*?)</arxiv:affiliation>', e, re.S)
    com = re.findall(r'<arxiv:comment[^>]*>(.*?)</arxiv:comment>', e, re.S)
    summ = re.sub(r'\s+', ' ', re.search(r'<summary>(.*?)</summary>', e, re.S).group(1).strip())
    cats = re.findall(r'<category term="([^"]+)"', e)
    print('=' * 100)
    print('ID:', idm, '| PUB:', pub, '| CATS:', ','.join(cats[:3]))
    print('TITLE:', t)
    print('AUTHORS:', '; '.join(authors))
    print('AFFIL:', '; '.join(re.sub(r'\s+', ' ', a) for a in aff[:6]))
    print('COMMENT:', ' '.join(re.sub(r'\s+', ' ', c) for c in com))
    print('ABSTRACT:', summ)
