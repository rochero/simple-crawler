from threading import Lock
from os import system
from utils.save import append_data_txt, append_data_xlsx
import requests
from requests_html import HTMLSession, Element
import json
import re
from concurrent.futures import ThreadPoolExecutor
import traceback
import time
sql = []
mutux = Lock()
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
            response = session.get(
                url,
                headers=headers,
                timeout=10,
                verify=False,
                # proxies={'http':'127.0.0.1:2334'}
            )
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
    mutux.acquire(10)
    append_data_txt([[url]],'lost.txt')
    mutux.release()
    print('url request failed\n')
    return None

def videogamegeek(load_path='', save_path='', group_len = 200, max_workers = 16):
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
        prefs.append('https://videogamegeek.com/videogame/'+i)
        if ((cnt % group_len) == 0) or (cnt == l):
            with ThreadPoolExecutor(max_workers) as t:
                for r in t.map(get_data, prefs):
                    if r:
                        s = r.html
                        score = s.xpath('//span[@property="v:average"]/text()', first=True)
                        tmp = re.search('<a.*?href="/collection/items/videogame/(\d+).*?">.*?<.*?>.*?(\d+) Ratings</a>', r.text, re.S)
                        id = tmp.group(1)
                        vote = tmp.group(2)
                        info = s.xpath('//table[@class="geekitem_infotable"]', first=True).html
                        title = s.xpath('//table[@class="geekitem_infotable"]//div[@class="geekitem_name"]/text()',first=True).strip()
                        print(title)
                        p = re.findall('<a href="/videogameplatform/.*?">(.*?)</a>', info)
                        platform = '|'.join(p) if p else ''
                        g = re.findall('<a href="/videogamegenre/.*?">(.*?)</a>', info)
                        genre = '|'.join(g) if g else ''
                        th = re.findall('<a href="/videogametheme/.*?">(.*?)</a>', info)
                        theme = '|'.join(th) if th else ''
                        m = re.findall('<a href="/videogamemode/.*?">(.*?)</a>', info)
                        mode = '|'.join(m) if m else ''
                        tmp = re.search('<b>Developer</b>.*?<a.*?href="/.*?>(.*?)</a>', info, re.S)
                        dev = tmp.group(1).strip() if tmp else ''
                        tmp = re.search('<b>Publisher</b>.*?<a.*?href="/.*?>(.*?)</a>', info, re.S)
                        pub = tmp.group(1).strip() if tmp else ''
                        tmp = re.search('<div id="results_releasedate.*?">(.*?)</div>',info, re.S)
                        release = tmp.group(1).strip() if tmp else ''
                        ho = re.findall('<a href="/videogamehonor/.*?">(.*?)</a>', info, re.S)
                        honor = '|'.join(ho) if ho else ''
                        d_list.append([id, title, genre, score, vote, dev, pub, release, theme, mode, platform, honor])
            append_data_xlsx(d_list,save_path,'Sheet')
            system('cls')
            d_list.clear()
            prefs.clear()