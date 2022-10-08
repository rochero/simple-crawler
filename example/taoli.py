import imp
from socket import timeout
from ssl import VerifyFlags
from xml.dom.minidom import Element
from lxml import etree
from threading import Lock, Thread
from weakref import proxy
from wsgiref import headers
from aiohttp import ClientSession, ClientResponse, ClientRequest, TCPConnector
import asyncio
from queue import Queue
from os import system
from requests.packages import urllib3
from requests_html import HTMLSession, HTMLResponse
import re
from concurrent.futures import ThreadPoolExecutor
import traceback
import time
import random
from tqdm import tqdm
from utils.save import append_data_raw, append_data_txt
from utils.reminder import say

mutux = Lock()
flag = True
q = Queue()
async def get_data(client:ClientSession, pref):
    is404=False
    url = pref
    headers = {
        # 'accept-encoding': 'utf-8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.',
    }
    try_cnt = 3
    while try_cnt > 0:
        try:
            async with await client.get(url, headers=headers) as resp:
                if resp and (resp.status == 200 or resp.status == 304):
                    return resp
                else:
                    if resp.status == 404:
                        is404=True
                        break
                    if resp.status == 503:
                        break
                    time.sleep(10.0/float(try_cnt))
                    try_cnt -= 1
        except Exception:
            time.sleep(10.0/try_cnt)
            try_cnt -= 1
            continue 
    mutux.acquire(10)
    if is404:
        # print('404')
        append_data_txt([[url]],'404.txt')
    else:
        print('爬取失败！')
        say('爬取失败！')
        append_data_txt([[url]],'lost.txt')
    mutux.release()   
    return None

async def parse_data(p:ClientResponse):
    if not p:
        return None
    r = p
    # r = p.text().replace('.whtml', '.html').encode() if p.url.name.endswith('html') else p.content
    # append_data_raw('taoli/'+re.sub('^https?:\/\/[^/]+\/', '', p.url.name).replace('.whtml', '.html'), r.)
    
    # init param
    hrefs, srcs, links = [[], [], []]
    # end init

    try:
        if r:
            s = etree.HTML(await r.text())
        if s:
            hrefs = s.xpath("//@href")
            srcs = s.xpath("//@src")
            links = list(set( filter(lambda x:re.search("(html|\.css|\.js|\.png|\.jpg)$", x), hrefs+srcs)))
            links = ['https://taolitop.com/'+re.sub('^\.?/', '', u) if not u.startswith('http') else u for u in links]
        return links
    except Exception:
        traceback.print_exc(limit=3)
        mutux.acquire(10)
        append_data_txt([[r.url]],'err.txt')
        mutux.release()
        return None

async def scraper(l, i, prefs, max_workers, lag):
    global flag
    conn = TCPConnector(
        verify_ssl=False, 
        limit=max_workers)
    async with ClientSession(connector=conn) as client:
        for pref in tqdm(prefs,desc='爬取中。。。{}/{}块'.format(i,l),total=len(prefs)):
            r = await get_data(client, pref)
            if r:
                q.put(r)
            if lag > 0:
                time.sleep(lag+2*lag*random.random())
    q.put(None)
    flag = False

async def parser(d):
    global flag
    while flag:
        e = q.get()
        if not e:
            return
        r = await parse_data(e)
        if r:
            d.extend([x] for x in r)
    print('处理中。。。')
    l = []
    while not q.empty():
        e = q.get()
        l.append(e)
    with ThreadPoolExecutor(16) as t:
        for r in t.map(await parse_data,l):
            if r:
                d.extend([x] for x in r)

def taoli(u_list=None, save_path:str='', chunk_len:int = 0, max_workers:int = 0, lag:float = 0):
    global flag
    chunks = [u_list[i:i + chunk_len] for i in range(0, len(u_list), chunk_len)]
    for i, chunk in enumerate(chunks, 1):
        flag = True
        d_list = []
        loop=asyncio.get_event_loop()
        async
        loop.run_until_complete(scraper(len(chunks), i, chunk, max_workers, lag))
        t2 = Thread(target=parser, args=(d_list,))
        t2.start()
        t2.join()
        print('保存中。。。')
        append_data_txt(d_list,save_path)
        # system('cls')