from threading import Lock
from os import system
from utils.save import append_data_txt, append_data_xlsx
import requests
from requests_html import HTMLSession, HTML
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
    is404=False
    u1 = pref
    requests.packages.urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
		'Accept': '*/*',
		'Accept-Encoding': 'utf-8',
		'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8',
		'Connection': 'keep-alive',
		'Cookie': '_ga=GA1.2.447737190.1627286368; _gid=GA1.2.697313503.1627286368; itchio_token=Im9hOEo2Qk8zRE5Zb0FSVyBVUiBCVVRUIG5rcGdhYjJ2bEJJUURXNyI%3d%2e4%2b8KrLt1vPjSV6tJjb2KOXATZjs%3d; ref%3aregister%3areferrer=https%3a%2f%2fitch%2eio%2f',
		'Host': 'itch.io',
		'Referer': 'https://itch.io/games/top-rated',
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
        append_data_txt([[u1,'404' if is404 else '']],'lost.txt')
    else:
        print('爬取失败！')
        say('爬取失败！')
        append_data_txt([[u1]],'lost.txt')
    mutux.release()   
    return None

def parse_data(r):
    if not r:
        return None
    data=[]
    j = r.json()['content']
    s = HTML(html=j)
    info = s.xpath('//div[@class="game_cell_data"]')
    for i in info:
        title=i.xpath('.//div[@class="game_title"]/a/text()', first=True)
        id = i.xpath('.//div[@class="game_title"]/a/@data-label', first=True)
        id = id.replace("game:","").replace(":title","") if id else ''
        text = i.xpath('.//div[@class="game_text"]/text()', first=True)
        author = i.xpath('.//div[@class="game_author"]/a/text()', first=True)
        score = i.xpath('.//div[@class="game_rating"]/div/div[@class="star_fill"]/@style', first=True)
        score = score.replace("width: ","").replace(r"%","") if score else ''
        votes = i.xpath('.//div[@class="game_rating"]/span[@class="rating_count"]/text()', first=True)
        votes = votes.replace("(","").replace(")","") if votes else ''
        genre = i.xpath('.//div[@class="game_genre"]/text()', first=True)
        platform = i.xpath('.//div[@class="game_platform"]/span/@class')
        platform = '|'.join(x for x in platform) if platform else ''
        data.append([id,title,text,author,genre,platform,score,votes])
    return data

def itch(u_list=None, save_path:str='', chunk_len:int = 0, max_workers:int = 0, lag:int = 0):
    chunks = [u_list[i:i + chunk_len] for i in range(0, len(u_list), chunk_len)]
    for chunk in chunks:
        r_list=[]
        d_list = []
        bar = Bar('爬取进度：', width = 64, bar_prefix = ' [', bar_suffix = '] ', fill='▇',
            max=len(chunk), suffix='第%(index)d/%(max)d项')
        with ThreadPoolExecutor(max_workers) as t:
            for r in t.map(get_data, chunk):
                r_list.append(r)
                if lag > 0:
                    time.sleep(lag+2*lag*random.random())
                bar.next()
        bar.finish()
        print('爬取顺利')
        bar = Bar('处理进度：', width = 64, bar_prefix = ' [', bar_suffix = '] ', fill='▇',
            max=len(r_list), suffix='第%(index)d/%(max)d项')
        with ThreadPoolExecutor(40) as t:
            for r in t.map(parse_data, r_list):
                if r:
                    for i in r:
                        d_list.append(i)
                    bar.next()
        print('处理顺利')
        append_data_xlsx(d_list,save_path)
        print('保存顺利')
        system('cls')