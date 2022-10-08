from threading import Lock
from os import system
from utils.save import append_data_txt, append_data_xlsx
import requests
from requests_html import HTMLSession, Element
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

def get_data(pref):
    is404=False
    u1 = pref
    requests.packages.urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        'accept-encoding': 'utf-8',
        'user-agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.',
        }
    try_cnt = 3
    while try_cnt > 0:
        try:
            res1 = session.get(
                u1,
                headers=headers,
                timeout=30,
                verify=False,
                proxies={'http':'127.0.0.1:2334','https':'127.0.0.1:2334'}
            )
            # res2 = session.get(
            #     u2,
            #     headers=headers,
            #     timeout=30,
            #     verify=False,
            #     # proxies={'http':'127.0.0.1:2334','https':'127.0.0.1:2334'}
            # )
        except Exception:
            time.sleep(10.0/try_cnt)
            try_cnt -= 1
            continue                
        if (res1) and (res1.status_code == 200 or res1.status_code == 304):
            return [res1,u1]
        else:
            if res1.status_code == 404:
                is404=True
                break
            if res1.status_code == 503:
                break
            time.sleep(10.0/float(try_cnt))
            try_cnt -= 1
    mutux.acquire(10)
    if is404:
        print('404')
        append_data_txt([[u1]],'404.txt')
    else:
        print('爬取失败！')
        say('爬取失败！')
        append_data_txt([[u1]],'lost.txt')
    mutux.release()   
    return None

def parse_data(p):
    r, u = p
    title, genre, desc, score, votes = ['']*5
    if not r:
        return None
    try:
        s = r.html
        if s:
            s = s.xpath('//script[@type="application/ld+json"]/text()',first=True)
        if not s:
            return None
        s = s.replace("\\","").replace('a "name"','"name"')
        j = demjson.decode(s)
        title = j.get("name")
        genre = j.get("genre")
        desc=j.get("description")
        tmp = j.get("aggregateRating")
        score = tmp.get("ratingValue") if tmp else ''
        votes = None
        if tmp:
            votes = tmp.get("ratingCount")
            if not votes:
                votes = tmp.get("reviewCount")
    except Exception:
        traceback.print_exc(limit=1)
        mutux.acquire(10)
        append_data_txt([[u]],'err.txt')
        mutux.release()   
        pass
    if not votes:
        return None
    return [u,title, desc, genre, score, votes]
    # title = s.xpath('//div[@class="responsive product-details"]//h1/text()', first=True)
    # platform = s.xpath('//h2[@class="product-platform"]/text()', first=True)
    # genres = s.xpath('//h2/a[contains(@href,"genre")]/text()', first=True)
    # desc = s.xpath('//div[@class="description"]', first=True)
    # desc = desc.text.strip() if desc else ''
    # size = s.xpath('//p[@class="game-filesize"]/text()', first=True)
    # size = size.replace("(","").replace(")","") if size else ''
    # score = s.xpath('//span[@itemprop="ratingValue"]/text()', first=True)
    # votes = s.xpath('//span[@itemprop="reviewCount"]/text()', first=True)
    # return [u,title,platform,genres,desc,size,score,votes]

def bigfish(u_list=None, save_path:str='', chunk_len:int = 0, max_workers:int = 0, lag:float = 0):
    chunks = [u_list[i:i + chunk_len] for i in range(0, len(u_list), chunk_len)]
    for chunk in chunks:
        r_list=[]
        d_list = []
        bar = Bar('爬取进度：', width = 64, bar_prefix = ' [', bar_suffix = '] ', fill='▇',
            max=len(chunk), suffix='第%(index)d/%(max)d项')
        with ThreadPoolExecutor(max_workers) as t:
            for r in t.map(get_data, chunk):
                if r:
                    r_list.append(r)
                if lag > 0:
                    time.sleep(lag+2*lag*random.random())
                bar.next()
        bar.finish()
        print('爬取顺利')
        bar = Bar('处理进度：', width = 64, bar_prefix = ' [', bar_suffix = '] ', fill='▇',
            max=len(r_list), suffix='第%(index)d/%(max)d项')
        with ThreadPoolExecutor(64) as t:
            for r in t.map(parse_data, r_list):
                if r:
                    d_list.append(r)
                bar.next()
        bar.finish()
        print('处理顺利')
        append_data_xlsx(d_list,save_path)
        print('保存顺利')
        system('cls')