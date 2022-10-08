from threading import Lock,Thread
from queue import Queue
from os import system
import re
from utils.save import append_data_txt, append_data_xlsx
from requests.packages import urllib3
from requests_html import HTMLSession
from utils.reminder import say
from concurrent.futures import ThreadPoolExecutor
import traceback
import time
import random
from progress.bar import Bar

mutux = Lock()
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

def parse_data(r):
    if not r:
        return None
    try:
        s = r.html
        id,title,alt,score,votes = ['']*5
        meta = ['','','','']
        if s:
            items = s.xpath('//li[contains(@id,"item_")]')
            for i in items:
                id = i.xpath('.//h3/a/@href',first=True)
                id = int(id.replace('/subject/','')) if id else ''
                title = i.xpath('.//h3/a/text()', first=True)
                alt = i.xpath('.//h3/small/text()', first=True)
                info = i.xpath('.//p[@class="info tip"]/text()', first=True)
                info = re.search('(.*?) / (.*?) / (.*?) / (.*)',info, re.S) if info else ''
                if info:
                    for j in range(4):
                        meta[j] = info.group(j+1)
                        meta[j] = meta[j].strip() if meta[j] else ''
                score = i.xpath('.//p[@class="rateInfo"]/small[@class="fade"]/text()', first=True)
                score = float(score) if score else ''
                votes = i.xpath('.//span[@class="tip_j"]/text()',first=True)
                votes = int(votes.replace('(','').replace('人评分)','')) if votes else ''
                d.put([id,title,alt,meta[0],meta[1],meta[2],meta[3],score,votes])
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
            if r:
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
    
def bangumi(u_list=None, save_path:str='', chunk_len:int = 0, max_workers:int = 0, lag:float = 0):
    global stat, mutux_stat
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