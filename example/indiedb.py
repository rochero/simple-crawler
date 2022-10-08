from threading import Lock
from os import replace, system
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

sql = []
mutux = Lock()
# 获取课程数据
def get_data(pref):
    is404=False
    u1 = pref
    requests.packages.urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'utf-8',
        'accept-language': 'en,zh-CN;q=0.9,zh;q=0.8',
        'cache-control': 'max-age=0',
        'cookie': 'dukenukem=2749f395ca7fa9c489dc8c6c4d8c6cbe; _ga=GA1.2.1938480638.1627191091; _gid=GA1.2.784205934.1627191091; masterchief=8ef424950a0cc32cd94c13e9a6dd4867; _gat=1',
        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55',
        }
    try_cnt = 3
    while try_cnt > 0:
        try:
            res1 = session.get(
                u1,
                headers=headers,
                timeout=30,
                verify=False,
                # proxies={'http':'127.0.0.1:2334','https':'127.0.0.1:2334'}
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
        append_data_txt([[u1,'404' if is404 else '']],'lost.txt')
    else:
        print('爬取失败！')
        say('爬取失败！')
        append_data_txt([[u1]],'lost.txt')
    mutux.release()   
    return None

def parse_data(r):
    s = r.html
    tmp=s.xpath('//div[@class="headercorner"]/div[@class="title"]', first=True)
    title = tmp.xpath('.//h2/a/text()', first=True)
    href = tmp.xpath('.//h2/a/@href', first=True)
    author = tmp.xpath('.//h3/a/text()')
    author = '|'.join(a.strip() for a in author) if author else ''
    date = tmp.xpath('.//h3/time/@datetime', first=True)
    score = s.xpath('//div[@class="table tablerating"]/div[@class="score"]/span/text()',first=True)
    votes = s.xpath('//div[@class="rating"]/p/span/text()',first=True)
    desc = s.xpath('//div[@class="headernormalbox normalbox"]/div/div/p/text()',first=True)
    poll=s.xpath('//div[@class="poll"]/a[@class="rating"]/div/div[@class="barinner"]/text()')
    v10,v9,v8,v7,v6,v5,v4,v3,v2,v1=poll if len(poll)==10 else ['']*10
    # print(title,date,score,votes,sep='\t')
    return [href,title,author,date,desc,
    v10,v9,v8,v7,v6,v5,v4,v3,v2,v1,
    score,
    votes]

def indiedb(load_path:str=None, save_path:str='', group_len:int = 200, max_workers:int = 16, lag:int = 0,start=0,end=0):
    r_list = []
    d_list = []
    prefs = []
    urls = []
    cnt=0
    if load_path:
        f = open(load_path, 'r')
        urls = f.readlines()
    else:
        for i in range(start,end):
            urls.append('https://www.indiedb.com/games/page/{}?sort=visitstotal-desc'.format(i))
    for url in urls:
        cnt+=1
        # id = re.search('/(\d+?)\.html?',url).group(1)
        prefs.append(url.strip())
        if ((cnt % group_len) == 0) or (url==urls[-1]):
            bar = Bar('爬取进度', width = 64, bar_prefix = ' [', bar_suffix = '] ', fill='▇',
                max=len(prefs), suffix='第%(index)d/%(max)d项')
            with ThreadPoolExecutor(max_workers) as t:
                for r in t.map(get_data, prefs):
                    if r:
                        r_list.append(r)
                        bar.next()
            prefs.clear()
            bar.finish()
            bar = Bar('处理进度', width = 64, bar_prefix = ' [', bar_suffix = '] ', fill='▇',
                max=len(r_list), suffix='第%(index)d/%(max)d项')
            with ThreadPoolExecutor(8) as t:
                for d in t.map(parse_data, r_list):
                    d_list.append(d)
                    bar.next()
            r_list.clear()
            bar.finish()
            append_data_xlsx(d_list,save_path)
            d_list.clear()
            system('cls')