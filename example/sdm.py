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

def sdm(load_path:str='', save_path:str='', group_len:int = 200, max_workers:int = 16, lag:int = 0):
    d_list = []
    prefs = []
    cnt=0
    f = open(load_path, 'r')
    urls = f.readlines()
    for url in urls:
        cnt+=1
        prefs.append(url.strip())
        if ((cnt % group_len) == 0) or (url==urls[-1]):
            with ThreadPoolExecutor(max_workers) as t:
                for r in t.map(get_data, prefs):
                    if r:
                        s = r.html
                        if s:
                            name=s.xpath('//div[@class="name"]/h1/text()', first=True)
                            slug = s.xpath('//div[@class="name"]/a/@href', first=True)
                            id = s.xpath('//div[@class="gameinfo"]/input/@value', first=True)
                            score = s.xpath('//div[@class="scorewrap"]/div/font/text()', first=True)
                            votes = s.xpath('//div[@class="scorewrap"]/div/span[@class="num1"]/text()', first=True)
                            info = s.xpath('//div[@class="gameinfo"]/ul[@class="list"]/li')
                            for i in info:
                                if i.find('p',containing='游戏类型'):
                                    genre=i.xpath('.//span/text()', first=True)
                                elif i.find('p',containing='开发发行'):
                                    devpub=i.xpath('.//span/text()', first=True)
                                elif i.find('p',containing='日期'):
                                    time=i.xpath('.//span/text()', first=True)
                                elif i.find('p',containing='官方网站'):
                                    href=i.xpath('.//a/@href', first=True)
                                elif i.find('p',containing='标签'):
                                    tags='|'.join(i.xpath('.//i/a/text()')) if i.xpath('.//i/a/text()') else ''
                                elif i.find('p',containing='语言'):
                                    lang=i.xpath('.//span/text()', first=True)
                            title = s.xpath('//div[@class="GmL_1"]/p/strong/text()', first=True)
                            print(id, title)
                            d_list.append([id, name,title, slug, genre, devpub, time, href,tags, lang, score, votes])
            append_data_xlsx(d_list,save_path)
            system('cls')
            d_list.clear()
            prefs.clear()