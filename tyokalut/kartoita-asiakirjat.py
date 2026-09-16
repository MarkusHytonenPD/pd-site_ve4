import re, subprocess, json, html
from urllib.parse import urljoin, unquote

JUURI = 'https://www.plandisain.fi/'

def hae(url):
    return subprocess.run(['curl','-sL','--max-time','40',url],
                          capture_output=True, text=True).stdout

# 1. Etusivun linkeistä koko sivukartta
etusivu = hae(JUURI)
sivut = {JUURI}
for h in re.findall(r'href="([^"]+\.html)"', etusivu):
    u = urljoin(JUURI, html.unescape(h))
    if u.startswith(JUURI):
        sivut.add(u)
print(f'Etusivulta {len(sivut)} sivua. Haravoidaan myös niiden linkit...')

# 2. Yksi taso syvemmälle (asiakirjasivut ovat projektisivujen alla)
for u in list(sivut):
    for h in re.findall(r'href="([^"]+\.html)"', hae(u)):
        v = urljoin(JUURI, html.unescape(h))
        if v.startswith(JUURI):
            sivut.add(v)
print(f'Yhteensä {len(sivut)} sivua haravoitavana.\n')

# 3. Tiedostolinkit. Entiteetit puretaan ja polku URL-koodataan oikein.
PAATE = r'\.(?:pdf|zip|docx?|xlsx?|pptx?)'
tiedostot = {}
for u in sorted(sivut):
    sisalto = hae(u)
    for h in set(re.findall(r'href="([^"]*?/uploads/[^"]*?' + PAATE + r')"', sisalto, re.I)):
        puhdas = urljoin(JUURI, html.unescape(h))
        tiedostot.setdefault(puhdas, set()).add(u.replace(JUURI,''))

print(f'{len(tiedostot)} uniikkia tiedostoa. Mitataan...\n')

def mittaa(url):
    r = subprocess.run(['curl','-sIL','--max-time','40',url], capture_output=True, text=True)
    k = re.findall(r'HTTP/[\d.]+ (\d+)', r.stdout)
    n = re.findall(r'(?i)^content-length:\s*(\d+)', r.stdout, re.M)
    return (k[-1] if k else '000'), (int(n[-1]) if n else 0)

tulos, summa, rikki = [], 0, []
for u in sorted(tiedostot):
    k, n = mittaa(u)
    tulos.append({'url': u, 'koodi': k, 'tavua': n, 'sivut': sorted(tiedostot[u])})
    summa += n
    if k != '200': rikki.append((k, u))

for t in sorted(tulos, key=lambda x: -x['tavua']):
    print(f"  {t['koodi']} {t['tavua']/1048576:7.1f} MB  {unquote(t['url'].split('/')[-1])[:52]:54} {','.join(t['sivut'])[:34]}")

print(f'\nYHTEENSÄ {len(tulos)} tiedostoa, {summa/1048576:.1f} MB')
print(f'Toimivia: {sum(1 for t in tulos if t["koodi"]=="200")}  Rikki: {len(rikki)}')
for k,u in rikki: print(f'   {k}  {unquote(u)}')
json.dump(tulos, open('/tmp/asiakirjat.json','w'), indent=1, ensure_ascii=False)
