from threading import Lock,Thread
from queue import Queue
from os import system
from utils.save import append_data_txt, append_data_xlsx
from requests.packages import urllib3
from requests_html import HTMLSession
import json
import re
from utils.reminder import say
from concurrent.futures import ThreadPoolExecutor
import traceback
import time
import random
from utils.tool import timeStamp
from progress.bar import Bar

mutux = Lock()
stat = {}
flag = True
mutux_stat = Lock()
q = Queue()
d = Queue()
def get_data(pref):
    is404=False
    url = pref
    urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        'accept-encoding': 'utf-8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.',
        }
    try_cnt = 3
    while try_cnt > 0:
        try:
            res = session.get(
                url,
                headers=headers,
                timeout=60,
                verify=False,
                proxies={'http':'127.0.0.1:2334','https':'127.0.0.1:2334'}
            )
        except Exception:
            time.sleep(10.0/try_cnt)
            try_cnt -= 1
            continue                
        if res and (res.status_code == 200 or res.status_code == 304):
            return res
        else:
            if res.status_code == 404:
                is404=True
                break
            if res.status_code == 503:
                break
            time.sleep(10.0/float(try_cnt))
            try_cnt -= 1
    mutux.acquire(10)
    if is404:
        # print('404')
        append_data_txt([[url]],'404.txt')
    else:
        print('爬取失败！')
        say('爬取失败！')
        append_data_txt([[url]],'lost.txt')
    mutux.release()   
    return None

def parse_data(p):
    if not p:
        return None
    r = p
    try:
        if r:
            s = r.html
        if s:
            m = s.xpath('//script[@type="application/ld+json"]/text()',first=True)
            title = re.search('"name":"(.*?)",',m,re.S)
            title = title.group(1) if title else ''
            author = re.search('"author":{"@type":".*?","name":"(.*?)"}',m,re.S)
            author = author.group(1) if author else ''
            votes = re.search('"ratingCount":(.*?)[,|}]',m,re.S)
            votes = int(votes.group(1)) if votes else ''
            score = ''
            up = s.xpath('//div[@class="uf"]/button[1]/text()',first=True)
            down = s.xpath('//div[@class="uf"]/button[2]/text()',first=True)
            tags = s.xpath('//ul[@class="xc hc"]/li/a/text()')
            tags = '|'.join(tags) if tags else ''
            if up and down:
                if 'K' in up:
                    up = int(float(up.replace('"','').replace('K',''))*1000)
                elif 'M' in up:
                    up = int(float(up.replace('"','').replace('M',''))*1000000)
                else:
                    up = int(up.replace('"',''))
                if 'K' in down:
                    down = int(float(down.replace('"','').replace('K',''))*1000)
                elif 'M' in down:
                    down = int(float(down.replace('"','').replace('M',''))*1000000)
                else:
                    down = int(down.replace('"',''))
                score = up/(up+down)
            return [title,r.url,author,tags,score,votes]
    except Exception:
        traceback.print_exc(limit=3)
        mutux.acquire(10)
        append_data_txt([[r.url]],'err.txt')
        mutux.release()
        return None

def scraper(l, i, prefs, max_workers, lag):
    global flag
    bar = Bar('爬取中。。。{}/{}块'.format(i,l), 
            width=64,bar_prefix='【', bar_suffix = '】',fill='▇',max=len(prefs),suffix='%(index)d/%(max)d个')
    with ThreadPoolExecutor(max_workers) as t:
        for r in t.map(get_data, prefs):
            if r and all(r):
                q.put(r)
                bar.next()
            if lag > 0:
                time.sleep(lag+2*lag*random.random())
    q.put(None)
    flag = False
    bar.finish()

def parser(d):
    global flag
    while flag:
        e = q.get()
        if not e:
            return
        r = parse_data(e)
        if r:
            d.append(r)
    print('处理中。。。')
    l = []
    while not q.empty():
        l.append(q.get())
    with ThreadPoolExecutor(16) as t:
        for r in t.map(parse_data,l):
            if r:
                d.append(r)

def poki(u_list=None, save_path:str='', chunk_len:int = 0, max_workers:int = 0, lag:float = 0):
    global flag
    chunks = [u_list[i:i + chunk_len] for i in range(0, len(u_list), chunk_len)]
    for i, chunk in enumerate(chunks, 1):
        flag = True
        d_list = []
        t1 = Thread(target=scraper, args = (len(chunks), i, chunk, max_workers, lag))
        t2 = Thread(target=parser, args=(d_list,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        print('保存中。。。')
        append_data_xlsx(d_list,save_path)
        system('cls')