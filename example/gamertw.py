from threading import Lock
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

def get_data(pref):
    is404=False
    url = pref
    if not url:
        return None
    res = None
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
                timeout=30,
                verify=False,
                # proxies={'http':'127.0.0.1:2334','https':'127.0.0.1:2334'}
            )
        except Exception:
            time.sleep(10.0/try_cnt)
            try_cnt -= 1
            continue                
        if res and (res.status_code == 200 or res.status_code == 304):
            return [res,int(url.replace('https://acg.gamer.com.tw/acgDetail.php?s=',''))]
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
        append_data_txt([[url]],'404.txt')
    else:
        print('爬取失败！')
        say('爬取失败！')
        append_data_txt([[url]],'lost.txt')
    mutux.release()   
    return None

def parse_data(p):
    r, id = p
    id = int(id)
    title,alt,sys,genre,date,play,dev,pub,rating,score,vote = ['']*11
    if not r:
        return None
    try:
        s = r.html
        if not s:
            return None
        title = s.xpath('//h1/text()', first=True)
        score = s.xpath('//div[@class="ACG-score"]/text()',first=True)
        score = score.replace('"','').replace('"','') if score else ''
        score = float(score) if score else ''
        vote = s.xpath('//div[@class="ACG-score"]/span/text()',first=True)
        vote = vote.replace('人','') if vote else ''
        vote = int(vote) if vote else ''
        alt = s.xpath('//div[@class="BH-lbox ACG-mster_box1 hreview-aggregate hreview"]/h2/text()')
        alt = '|'.join(alt) if alt else ''
        sys = s.xpath('//li[contains(text(),"平台")]/a/text()', first=True)
        genre = s.xpath('//li[contains(text(),"類型")]/a/text()', first=True)
        date = s.xpath('//li[contains(text(),"台灣")]/text()', first=True)
        date = date.replace('台灣發售：','').replace('台灣封測：','') if date else ''
        play = s.xpath('//li[contains(text(),"人數")]/text()', first=True)
        play = play.replace('遊戲人數：','') if play else ''
        dev = s.xpath('//li[contains(text(),"製作")]/a/text()', first=True)
        pub = s.xpath('//li[contains(text(),"發行")]/a/text()', first=True)
        rating = s.xpath('//li[contains(text(),"分級")]/text()', first=True)
        rating = rating.replace('作品分級：','') if rating else ''
    except Exception:
        traceback.print_exc(limit=3)
        mutux.acquire(10)
        append_data_txt([[id]],'err.txt')
        mutux.release()
    return [id,title,alt,sys,genre,date,play,dev,pub,rating,score,vote]

def gamertw(u_list=None, save_path:str='', chunk_len:int = 0, max_workers:int = 0, lag:float = 0):
    chunks = [u_list[i:i + chunk_len] for i in range(0, len(u_list), chunk_len)]
    for i, chunk in enumerate(chunks, 1):
        r_list, d_list = [], []
        bar = Bar('爬取中。。。{}/{}块'.format(i,len(chunks)), 
        width = 64, bar_prefix = '【', bar_suffix = '】', fill='▇',
        max=len(chunk), suffix='%(index)d/%(max)d项')
        with ThreadPoolExecutor(max_workers) as t:
            for r in t.map(get_data, chunk):
                if r and all(r):
                    r_list.append(r)
                if lag > 0:
                    time.sleep(lag+2*lag*random.random())
                bar.next()
        bar.finish()
        bar = Bar('处理中。。。',
        width = 64, bar_prefix = '【', bar_suffix = '】', fill='▇',
        max=len(r_list), suffix='%(index)d/%(max)d项')
        with ThreadPoolExecutor(128) as t:
            for r in t.map(parse_data, r_list):
                if r:
                    d_list.append(r)
                bar.next()
        bar.finish()
        print('保存中。。。')
        append_data_xlsx(d_list,save_path)
        system('cls')