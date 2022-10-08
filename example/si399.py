from threading import Lock
from multiprocessing import Pool
from os import system
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
def get_data(pref):
    is404=False
    id, url = pref
    urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        'accept-encoding': 'utf-8',
        'user-agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.',
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
    return None

def parse_data(p):
    global mutux_stat,stat
    id, r = p
    if not r:
        return None
    try:
        if r:
            s = r.html
        if s:
            if not stat[id]['title']:
                stat[id]['title'] = s.xpath('//title/text()', first=True)
                stat[id]['title'] = stat[id]['title'].replace('评论','') if stat[id]['title'] else ''
            items = s.xpath('//div[@class="star"]')
            mutux_stat.acquire()
            if items:
                for item in items:
                    t = item.xpath('.//span')
                    if t:
                        stat[id]['stars'] += len(t)
                        stat[id]['votes'] += 1
            mutux_stat.release()
    except Exception:
        traceback.print_exc(limit=3)
        mutux.acquire(10)
        append_data_txt([[id]],'err.txt')
        mutux.release()

def si399(u_list=None, save_path:str='', chunk_len:int = 0, max_workers:int = 0, lag:float = 0):
    global stat, mutux_stat
    chunks = [u_list[i:i + chunk_len] for i in range(0, len(u_list), chunk_len)]
    for i, chunk in enumerate(chunks, 1):
        r_list, d_list, prefs = [], [], []
        for c in chunk:
            id, cnt = c
            stat.update({id:{'title':'','stars':0,'votes':0}})
            for j in range(1, int(cnt)+1):
                prefs.append([id,'http://cdn.comment.4399pk.com/htm-{}-{}.htm'.format(id, j)])
        bar = Bar('爬取中。。。{}/{}块'.format(i,len(chunks)), 
                width=64,bar_prefix='【', bar_suffix = '】',fill='▇',max=len(prefs),suffix='%(index)d/%(max)d个')
        with ThreadPoolExecutor(max_workers) as t:
            for r in t.map(get_data, prefs):
                if r and all(r):
                    r_list.append(r)
                    bar.next()
                if lag > 0:
                    time.sleep(lag+2*lag*random.random())
        bar.finish()
        bar = Bar('处理中。。。',width=64,bar_prefix='【', bar_suffix = '】',fill='▇',max=len(r_list), suffix='%(index)d/%(max)d个')
        with ThreadPoolExecutor(128) as t:
            for _ in t.map(parse_data, r_list):
                bar.next()
        bar.finish()
        for k,v in stat.items():
            d_list.append([int(k),v.get('title'),v.get('stars'), v.get('stars')/v.get('votes') if v.get('votes') else '', v.get('votes')])
        print('保存中。。。')
        append_data_xlsx(d_list,save_path)
        stat.clear()
        system('cls')