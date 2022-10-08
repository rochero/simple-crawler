from threading import Lock
from os import system
from utils.save import append_data_txt, append_data_xlsx
import requests
from requests_html import HTMLSession, Element
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

def get_data(pref):
    if not pref:
        return None
    is404=False
    u1 = pref
    requests.packages.urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'utf-8',
        'accept-language': 'en,zh-CN;q=0.9,zh;q=0.8',
        'cache-control': 'max-age=0',
        'cookie': 'dukenukem=a91f3f2f0f4da68c7c857e79dabb3da9; _ga=GA1.2.537671981.1627270510; _gid=GA1.2.1419802535.1627270510; dfp-npa={%22status%22:%22false%22%2C%22version%22:%221.0.13%22%2C%22chosen%22:%22true%22}; masterchief=6008334d0f6a32e98de04785ec524647',
        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55        }',
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
            return res1
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

def parse_data(r):
    score,votes=['']*2
    if r:
        s = r.html
        score = s.xpath('//div[@class="table tablerating"]/div[@class="score"]/span/text()',first=True)
        votes = s.xpath('//div[@class="rating"]/p/span/text()',first=True)
    return [score,votes]

def get_data_batch(rs):
    return list(map(get_data, rs)) if rs else None

def parse_data_batch(rs):
    return list(map(parse_data,rs)) if rs else None

def moddb(u_list=None, save_path:str='', chunk_len:int = 0, max_workers:float = 0, lag:float = 0):
    chunks = [u_list[i:i + chunk_len] for i in range(0, len(u_list), chunk_len)]
    if chunks:
        for chunk in chunks:
            if chunk:
                r_list=[]
                d_list = []
                bar = Bar('爬取进度：', width = 64, bar_prefix = ' [', bar_suffix = '] ', fill='▇',
                    max=len(chunk), suffix='第%(index)d/%(max)d项')
                with ThreadPoolExecutor(max_workers) as t:
                    for r in t.map(get_data, chunk):
                        if r:
                            r_list.append(r)
                            bar.next()
                        if lag > 0:
                            time.sleep(lag+2*lag*random.random())        
                bar.finish()
                bar = Bar('处理进度：', width = 64, bar_prefix = ' [', bar_suffix = '] ', fill='▇',
                    max=len(r_list), suffix='第%(index)d/%(max)d项')
                with ThreadPoolExecutor(64) as t:
                    for r in t.map(parse_data, r_list):
                        d_list.append(r)
                        bar.next()
                bar.finish()
                print('保存中...')
                append_data_txt(d_list,save_path)
                system('cls')