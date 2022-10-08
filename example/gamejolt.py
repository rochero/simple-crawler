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
    id, url = pref
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
                # proxies={'http':'127.0.0.1:2334','https':'127.0.0.1:2334'}
            )
        except Exception:
            time.sleep(10.0/try_cnt)
            try_cnt -= 1
            continue                
        if res and (res.status_code == 200 or res.status_code == 304):
            return [id,res]
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
    if not p:
        return None
    id, r = p
    cat,sys,dev_url = ['']*3
    try:
        if r:
            s = r.html.html
        if s:
            j = json.loads(s) if s else ''
            j = j.get('payload').get('game') if j else ''
            if j:
                cat = j.get('category')
                cat = j.get('category_slug') if cat else cat
                tmp = j.get('compatibility')
                sys = []
                if tmp:
                    for t1,t2 in tmp.items():
                        if t2 == True:
                            sys.append(t1)
                sys = '|'.join(sys) if sys else ''
                tmp = j.get('developer')
                dev_url = tmp.get('web_site')
                dev_url = tmp.get('url') if (tmp and not dev_url) else dev_url
            return [id,cat,sys,dev_url]
    except Exception:
        traceback.print_exc(limit=3)
        mutux.acquire(10)
        append_data_txt([[r.url]],'err.txt')
        mutux.release()
        return [id,cat,sys,dev_url]

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
        d.append(parse_data(e))
    print('处理中。。。')
    l = []
    while not q.empty():
        l.append(q.get())
    print(len(l))
    with ThreadPoolExecutor(16) as t:
        for r in t.map(parse_data,l):
            if r:
                d.append(r)

def gamejolt(u_list=None, save_path:str='', chunk_len:int = 0, max_workers:int = 0, lag:float = 0):
    global flag
    chunks = [u_list[i:i + chunk_len] for i in range(0, len(u_list), chunk_len)]
    for i, chunk in enumerate(chunks, 1):
        flag = True
        d_list, prefs = [], []
        for c in chunk:
            prefs.append([c,'https://gamejolt.com/site-api/web/discover/games/{}'.format(c)])
        t1 = Thread(target=scraper, args = (len(chunks), i, prefs, max_workers, lag))
        t2 = Thread(target=parser, args=(d_list,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        print('保存中。。。')
        append_data_xlsx(d_list,save_path,'detail')
        system('cls')