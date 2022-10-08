

from os import system
from utils.save import append_data_txt, append_data_xlsx
import requests
from requests_html import HTMLSession
import json
import re
from concurrent.futures import ThreadPoolExecutor
import traceback
import time
sql = []

# 获取课程数据
def get_data(pref):
    url = pref
    requests.packages.urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36 Edg/81.0.416.53",
    }
    try_cnt = 3
    while try_cnt > 0:
        try:
            response = session.get(url, headers=headers, timeout=10, verify=False,proxies={'http':'127.0.0.1:2334'})
        except Exception:
            time.sleep(10.0/try_cnt)
            try_cnt -= 1
            continue                
        if response and response.status_code == 200:
            return response
        else:
            if response.status_code == 404:
                return None
            time.sleep(10.0/float(try_cnt))
            try_cnt -= 1
    append_data_txt([[url]],'lost.txt')
    print('url request failed\n')
    return None

def phoneky(load_path='', save_path='', group_len = 200, max_workers = 16):
    i_list = []
    d_list = []
    prefs = []
    with open(load_path,'r') as f:
	    for line in f:
		    i_list.append(line.strip())
    cnt = 0
    l = len(i_list)
    for i in i_list:
        cnt+=1
        prefs.append(i)
        if ((cnt % group_len) == 0) or (cnt == l):
            with ThreadPoolExecutor(max_workers) as t:
                for r in t.map(get_data, prefs):
                    if r:
                        s = r.html
                        title = s.xpath('//h1[@class="title"]/text()',first=True)
                        id = s.xpath('//dd[@class="id-num"]/text()', first=True)
                        id = int(id) if id else ''
                        up = s.xpath('//a[@title="Like"]//text()',first=True)
                        up = float(up) if up else 0.001
                        down = s.xpath('//a[@title="Dislike"]//text()',first=True)
                        down = float(down) if down else 0.1
                        genre = s.xpath('//span[@class="category"]/a/text()',first=True)
                        d_list.append([id, title, genre, int(up), int(down)])
                        if id and up:
                            print('\t'.join(str(x) for x in [id, int((up+0.01)/(up+down+1)*100), up+down, genre, title]))
                        else:
                            print('void')
            append_data_xlsx(d_list,save_path,'Symbian')
            system('cls')
            d_list.clear()
            prefs.clear()