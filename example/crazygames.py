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

sql = []
mutux = Lock()
# 获取课程数据
def get_data(pref):
    url = pref
    requests.packages.urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        'accept': 'text/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71',
        }
    try_cnt = 3
    while try_cnt > 0:
        try:
            response = session.get(
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
        if response and (response.status_code == 200 or response.status_code == 304):
            return response
        else:
            if response.status_code == 404:
                print('404')
                return None
            if response.status_code == 503:
                break
            time.sleep(10.0/float(try_cnt))
            try_cnt -= 1
    mutux.acquire(10)
    append_data_txt([[url]],'lost.txt')
    mutux.release()
    print('爬取失败！')
    say('爬取失败！')
    return None

def crazygames(load_path:str='', save_path:str='', group_len:int = 200, max_workers:int = 16, lag:int = 0):
    d_list = []
    prefs = []
    cnt=0
    f = open(load_path, 'r')
    param = f.readlines()
    f.close()
    for i in param:
        cnt+=1
        prefs.append('https://www.crazygames.com/api/v2/en_US/page/game/{}?limit=1'.format(i.strip()))
        if ((cnt % group_len) == 0) or (i == 'warfare-classic'):
            with ThreadPoolExecutor(max_workers) as t:
                for r in t.map(get_data, prefs):
                    if r:
                        s = r.json()['game']
                        if s:
                            name = s.get('name') if s.get('name') else ''
                            up = s.get('upvotes') if s.get('upvotes') else ''
                            down = s.get('downvotes') if s.get('downvotes') else ''
                            url = s.get('desktopUrl') if s.get('desktopUrl') else ''
                            cat = s.get('category').get('name') if s.get('category') else ''
                            tag = '|'.join(x.get('name') for x in s.get('tags')) if s.get('tags') else ''
                            desc = s.get('metaDescription') if s.get('metaDescription') else ''
                            dev = s.get('developer') if s.get('developer') else ''
                            print(name, up, down, sep='\t')
                            d_list.append([name, url, desc, cat, tag, desc, dev, up, down])
            append_data_xlsx(d_list,save_path,'Sheet')
            system('cls')
            d_list.clear()
            prefs.clear()