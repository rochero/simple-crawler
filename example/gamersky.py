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
    u1 = pref
    requests.packages.urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        'Accept': 'text/json',
        'Accept-Encoding': 'utf-8',
        'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8',
        'Connection': 'keep-alive',
        'Cookie': 'UM_distinctid=17ad603ec7716b-08b3f79d354c99-7a697f6c-e1000-17ad603ec786d0; CNZZDATA1256195895=1658884713-1627085711-%7C1627106635; ASP.NET_SessionId=cvmhcdgiyi03cn4c0xyjhdrz; Hm_lvt_dcb5060fba0123ff56d253331f28db6a=1625836894,1627083510,1627114683; Hm_lpvt_dcb5060fba0123ff56d253331f28db6a=1627115998',
        'Host': 'ku.gamersky.com',
        'Referer': 'https://ku.gamersky.com/sp/',
        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"',
        'sec-ch-ua-mobile': '?0',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55',
        'X-Requested-With': 'XMLHttpRequest',
}
    try_cnt = 3
    while try_cnt > 0:
        try:
            res1 = session.get(
                u1,
                headers=headers,
                timeout=120,
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

def gamersky(load_path:str=None, save_path:str='', group_len:int = 200, max_workers:int = 16, lag:int = 0,start=0,end=0):
    d_list = []
    prefs = []
    urls = []
    cnt=0
    if load_path:
        f = open(load_path, 'r')
        urls = f.readlines()
    else:
        for i in range(start,end):
            urls.append('https://ku.gamersky.com/SearchGameLibAjax.aspx?jsondata={{"rootNodeId":"20039","pageIndex":{},"pageSize":"5000","sort":"00"}}'.format(i))
    for url in urls:
        cnt+=1
        # id = re.search('/(\d+?)\.html?',url).group(1)
        prefs.append(url.strip())
        if ((cnt % group_len) == 0) or (url==urls[-1]):
            with ThreadPoolExecutor(max_workers) as t:
                for r in t.map(get_data, prefs):
                    if r:
                        s=re.search('\((.*)\)', r.html.html,re.S).group(1)
                        v=json.loads(s)['result']
                        if v:
                            for vv in v:
                                id=vv.get('id')
                                date=vv.get('allTimeT')
                                spent=vv.get('gameTime')
                                print(id, date, spent,sep='\t')
                                d_list.append([id, date, spent])
            append_data_txt(d_list)
            time.sleep(3)
            system('cls')
            d_list.clear()
            prefs.clear()