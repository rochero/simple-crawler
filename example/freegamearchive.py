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
    u1= pref
    requests.packages.urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        'accept-encoding': 'utf-8',
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
        append_data_txt([[u1,'404' if is404 else '']],'lost.txt')
    else:
        print('爬取失败！')
        say('爬取失败！')
        append_data_txt([[u1]],'lost.txt')
    mutux.release()   
    return None

def parse_data(p):
    r,u=p
    s = r.html
    pros=s.xpath('//div[@class="recenze-plus"]/ul/li/text()')
    pros = '|'.join(x.strip() for x in pros) if pros else ''
    cons = s.xpath('//div[@class="recenze-minus"]/ul/li/text()')
    cons = '|'.join(x.strip() for x in cons) if cons else ''
    info = s.xpath('//div[@class="stick game-info"]/ul/li')
    d1,d2,d3,d4,d5,d6,d7,d8,d9,d10=['']*10
    if info:
        l = len(info)
        d1= str(info[0].xpath('.//span',first=True).text) if l>=1 and info[0].xpath('.//span',first=True) else ''
        d2= str(info[1].xpath('.//span',first=True).text) if l>=2 and info[1].xpath('.//span',first=True) else d1
        d3= str(info[2].xpath('.//span',first=True).text) if l>=3 and info[2].xpath('.//span',first=True) else d2
        d4= str(info[3].xpath('.//span',first=True).text) if l>=4 and info[3].xpath('.//span',first=True) else d3
        d5= str(info[4].xpath('.//span',first=True).text) if l>=5 and info[4].xpath('.//span',first=True) else d4
        d6= str(info[5].xpath('.//span',first=True).text) if l>=6 and info[5].xpath('.//span',first=True) else d5
        d7= str(info[6].xpath('.//span',first=True).text) if l>=7 and info[6].xpath('.//span',first=True) else d6
        d8= str(info[7].xpath('.//span',first=True).text) if l>=8 and info[7].xpath('.//span',first=True) else d7
        d9= str(info[8].xpath('.//span',first=True).text) if l>=9 and info[8].xpath('.//span',first=True) else d8
        d10=str(info[9].xpath('.//span',first=True).text) if l>=10 and info[9].xpath('.//span',first=True) else d9
    return [u,pros,cons,d1,d2,d3,d4,d5,d6,d7,d8,d9,d10]

def freegamearchive(load_path:str=None, save_path:str='', group_len:int = 200, max_workers:int = 16, lag:int = 0,start=0,end=0):
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
            urls.append('http://www.freegamearchive.com/search-result/{}/?title=&score=&order=downloaded&direction=asc&section=0&subsection=0&category=0'.format(i))
    for url in urls:
        cnt+=1
        # id = re.search('/(\d+?)\.html?',url).group(1)
        prefs.append(url.strip())
        if ((cnt % group_len) == 0) or (url==urls[-1]):
            bar = Bar('爬取进度', width = 64, bar_prefix = ' [', bar_suffix = '] ', fill='▇',
                max=len(prefs), suffix='第%(index)d/%(max)d项')
            with ThreadPoolExecutor(max_workers) as t:
                for x in t.map(get_data, prefs):
                    if x:
                        r,u=x
                        r_list.append([r,u])
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
            append_data_xlsx(d_list, save_path,'detail')
            d_list.clear()
            system('cls')