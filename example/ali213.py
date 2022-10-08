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

sql = []
mutux = Lock()
# 获取课程数据
def get_data(pref):
    is404=False
    u1,u2,cid = pref
    requests.packages.urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71',
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
            res2 = session.get(
                u2,
                headers=headers,
                timeout=30,
                verify=False,
                # proxies={'http':'127.0.0.1:2334','https':'127.0.0.1:2334'}
            )
        except Exception:
            time.sleep(10.0/try_cnt)
            try_cnt -= 1
            continue                
        if (res1 and res2) and (res1.status_code == 200 or res1.status_code == 304):
            return [res1,res2,cid]
        else:
            if res1.status_code == 404:
                is404=True
                break
            if res1.status_code == 503:
                break
            time.sleep(10.0/float(try_cnt))
            try_cnt -= 1
    mutux.acquire(10)
    append_data_txt([[u1,u2,'404' if is404 else '']],'lost.txt')
    mutux.release()
    if is404:
        print('404')
    else:
        print('爬取失败！')
        say('爬取失败！')
    return None

def ali213(load_path:str='', save_path:str='', group_len:int = 200, max_workers:int = 16, lag:int = 0):
    d_list = []
    prefs = []
    cnt=0
    f = open(load_path, 'r')
    urls = f.readlines()
    for url in urls:
        cnt+=1
        id = re.search('/(\d+?)\.html?',url).group(1)
        prefs.append([url.strip(),'https://0day.ali213.net/getvote_xs.php?Action=Show&OdayID={}'.format(id),id])
        if ((cnt % group_len) == 0) or (url==urls[-1]):
            with ThreadPoolExecutor(max_workers) as t:
                for r in t.map(get_data, prefs):
                    if r:
                        s,v,cid = r
                        s=s.html
                        v=v.json()['data']
                        if s:
                            pt=s.xpath('//div[@class="xs-c1-c-pt"]//li/text()')
                            pt = '|'.join(pt) if pt else ''
                            cn=s.xpath('//h1[@class="xs-c1-c-cn"]/span/text()',first=True)
                            en=s.xpath('//h2[@class="xs-c1-c-en"]/text()',first=True)
                            time=s.xpath('//div[@class="xs-c1-c-time"]/span/text()',first=True)
                            time = time.replace('上市','') if time else ''
                            genre=s.xpath('//div[@class="xs-c1-c-info"]/div[contains(text(),"游戏类型")]/text()',first=True)
                            dev=s.xpath('//div[@class="xs-c1-c-info"]/div[contains(text(),"制作公司")]/text()',first=True)
                            lang=s.xpath('//div[@class="xs-c1-c-info"]/div[contains(text(),"语言")]/span/text()',first=True)
                            pub=s.xpath('//div[@class="xs-c1-c-info"]/div[contains(text(),"发行公司")]/text()',first=True)
                            tags=s.xpath('//div[@class="xs-c1-c-tag"]/span/text()')
                            tags = '|'.join(tags) if tags else ''
                            _,score,votes,v1,v2,v3,v4,v5,like,_,x,y=v
                            print(cid, cn, score, votes, sep='\t')
                            d_list.append([cid,cn,en,genre,pt,time,tags,dev,pub,lang,score,votes,v1,v2,v3,v4,v5,like,x,y])
            append_data_xlsx(d_list,save_path)
            system('cls')
            d_list.clear()
            prefs.clear()