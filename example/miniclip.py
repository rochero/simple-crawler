from threading import Lock,Thread
from queue import Queue
from os import error, system
from utils.save import append_data_txt, append_data_xlsx
from requests.packages import urllib3
from requests_html import HTMLSession
import json
import demjson
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
mutux_stat = Lock()
q = Queue()
d = Queue()
def get_data(pref):
    is404=False
    url = pref
    urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en,zh-CN;q=0.9,zh;q=0.8',
        'cache-control': 'max-age=0',
        'cookie': 'donation-identifier=36f4d25603e5430bf5987b2b808c8b69; abtest-identifier=c6bfe7ead427495a88939f0c71ac4326; PHPSESSID=6uskfqkrj6qp0slfs0sit19bod',
        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
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
            return [res.url,res]
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
    return [id,None]

def parse_data(p):
    id, r = p
    if not r:
        return None
    try:
        if r:
            s = r.html
        if s:
            genre = s.xpath('//nav[@class="breadcrumbs"]/a[contains(@href,"genre")]/text()',first=True)
            title = s.xpath('//nav[@class="breadcrumbs"]/h2/text()',first=True)
            tags = s.xpath('//div[@class="toolbar-tags"]//a[contains(@href,"tag")]/text()')
            tags = '|'.join(tags) if tags else ''
            meta = s.xpath('//script[@type="application/ld+json"]/text()',first=True)
            j = demjson.decode(meta) if meta else ''
            date,pub,score,votes,desc=['']*5
            if j:
                if not title:
                    title = j.get('name')
                if not genre:
                    genre = j.get('genre')
                date = j.get('datePublished')
                if not date:
                    date = j.get('dateCreated')
                pub = j.get('productionCompany')
                pub = pub.get('name') if pub else ''
                rating = j.get('aggregateRating')
                score = rating.get('ratingValue') if rating else ''
                votes = rating.get('reviewCount') if rating else ''
                desc = j.get('description')
            d.put([id,title,genre,desc,tags,date,pub,score,votes])
    except Exception:
        traceback.print_exc(limit=3)
        mutux.acquire(10)
        append_data_txt([[r.url]],'err.txt')
        mutux.release()

def scraper(l, i, prefs, max_workers, lag):
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
    bar.finish()

def parser():
    while True:
        r = q.get()
        if not r:
            break
        parse_data(r)
    
def miniclip(u_list=None, save_path:str='', chunk_len:int = 0, max_workers:int = 0, lag:float = 0):
    chunks = [u_list[i:i + chunk_len] for i in range(0, len(u_list), chunk_len)]
    for i, chunk in enumerate(chunks, 1):
        d_list = []
        t1 = Thread(target=scraper, args = (len(chunks), i, chunk, max_workers, lag))
        t2 = Thread(target=parser)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        while not d.empty():
            d_list.append(d.get())
        print('保存中。。。')
        append_data_xlsx(d_list,save_path)
        system('cls')