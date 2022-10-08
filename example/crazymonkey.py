from operator import truediv
from os import system
import re, json, traceback, logging, random, time
from threading import Lock, Thread
from queue import Queue
from requests.packages import urllib3
from requests_html import HTMLSession, HTMLResponse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from utils.tool import save_txt, save_xlsx, say

urllib3.disable_warnings()

# 保证写入文件时线程安全的锁
mutux = Lock()

# 保证请求URL的线程和解析响应数据的线程的同步关系的标记，false 代表请求线程结束
flag = True

# 响应数据入队，以供解析响应数据的线程使用
q = Queue()

# 解析响应数据时发生的异常会记录到日志中
logging.basicConfig(filename='log.txt', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 全局配置
cfg = {
    # 请求URL时的配置
    # 每个请求的最大重试次数
    'retry': 3,
    # 请求重试的最大等待时间
    'wait': 3.0,
    # 请求的时间间隔范围（最小间隔，最大间隔）
    'interval': (0, 0),

    # 记录错误信息相关文件配置
    # 解析响应数据时发生异常，对应的报错信息存入这里
    'log': 'log.txt',
    # 解析响应数据时发生异常，对应的请求URL存入这里
    'err': 'err.txt',
    # 请求失败对应的 URL 存入这里
    'lost': 'lost.txt',
    # 请求 404 对应的 URL 存入这里
    '404': '404.txt',
}


def get_data(pref):
    url = pref
    res = None
    session = HTMLSession()
    headers = {
        'accept-encoding': 'utf-8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.',
    }
    try_cnt = cfg['retry'] if cfg['retry'] and cfg['retry'] > 0 else 3
    wait_time = cfg['wait'] if cfg['wait'] and cfg['wait'] > 0 else 3.0
    while try_cnt > 0:
        try:
            res = session.get(
                url,
                headers=headers,
                timeout=20,
                verify=False,
                proxies={'http':'127.0.0.1:2334','https':'127.0.0.1:2334'}
            )
        except Exception:
            time.sleep(wait_time/float(try_cnt))
            try_cnt -= 1
            continue
        if is_right(res):
            return res
        else:
            if no_retry(res):
                break
            time.sleep(wait_time/float(try_cnt))
            try_cnt -= 1
    mutux.acquire(10)
    try:
        if not_found(res):
            print('not found: {}'.format(url))
            save_txt([[url]], '404.txt')
        else:
            print('request failed: {}'.format(url))
            say('request failed')
            save_txt([[url]], 'lost.txt')
    finally:
        mutux.release()
    return None


def is_right(res):
    """
    判断响应的数据是否正确
    """
    return res and (res.status_code == 200 or res.status_code == 304)


def no_retry(res):
    """
    根据响应的数据决定是否重试
    """
    return res and (res.status_code == 404 or res.status_code == 503)


def not_found(res):
    """
    判断请求的资源是否不存在
    """
    return res and res.status_code == 404


def parse_data(r: HTMLResponse):
    if not r:
        return None
    id = title = desc = tags = date = score = votes = 0
    try:
        if r:
            s = r.html
        if s:
            title = s.xpath('//h2[@class="clear"]/span[@class="section-title"]/text()', first=True)
            desc = s.xpath('//ul[@class="info"]/li[2]/text()', first=True)
            tags = s.xpath('//ul[@id="tags"]/li/a/text()')
            tags = '|'.join(tags) if tags else ''
            date = s.xpath('//ul[@class="info"]/li[3]/text()', first=True)
            id = s.xpath('//ul[@class="info"]/li[@id="gameID"]/text()', first=True)
            id = int(id) if id else ''
            score = s.xpath('//ul[@class="info"]/li[@id="ranking-list"]//span[@itemprop="average"]/text()', first=True)
            score = float(score) if score else ''
            votes = s.xpath('//ul[@class="info"]/li[@id="ranking-list"]//meta[@itemprop="count"]/@content', first=True)
            votes = int(votes) if votes else ''
        return [title, r.url, id, desc, tags, date, score, votes]
    except Exception:
        traceback.print_exc(limit=3)
        mutux.acquire(10)
        try:
            save_txt([[r.url]], 'err.txt')
        finally:
            mutux.release()
        logging.debug(traceback.format_exc(limit=3))
        return None

def append_data(d: list, r):
    if not r:
        return
    if isinstance(r, list):
        if isinstance(r[0], list):
            d.extend(r)
        else:
            d.append(r)
    else:
        d.append([r])

def scraper(l, i, prefs, max_workers):
    global flag
    min_lag, max_lag = cfg['interval'] if cfg['interval'] else (0, 0)
    with ThreadPoolExecutor(max_workers) as t:
        for r in tqdm(t.map(get_data, prefs), desc='scraping...{}/{}'.format(i, l), total=len(prefs)):
            if r and all(r):
                q.put(r)
            if max_lag > min_lag and min_lag > 0:
                time.sleep(random.uniform(min_lag, max_lag))
    flag = False


def parser(d: list):
    global flag
    while flag:
        if not q.empty():
            append_data(d, parse_data(q.get()))
    print('parsing...')
    if q.empty():
        return
    l = []
    while not q.empty():
        l.append(q.get())
    with ThreadPoolExecutor(16) as t:
        for r in t.map(parse_data, l):
            append_data(d, r)


def saver(d: list, save_path: str):
    print('saving...')
    save_xlsx(d, save_path)


def crawl(u_list=[], save_path: str = '', chunk_size: int = 0, max_workers: int = 1):
    """
    此爬虫将 URL 列表分成若干块，按块依次处理并保存。
    每块用线程池并发处理。

    参数：
    - u_list: 待爬取的 URL 列表
    - save_path: 保存最终数据的文件路径
    - chunk_size: URL 列表分块的大小
    - max_workers: 线程池的最大工作线程数量

    """
    global flag
    chunks = [u_list[i:i + chunk_size]
              for i in range(0, len(u_list), chunk_size)]
    for i, chunk in enumerate(chunks, 1):
        flag = True
        # 待保存数据的列表，列表每一项也是一个列表
        d_list = []
        t1 = Thread(target=scraper, args=(len(chunks), i, chunk, max_workers))
        t2 = Thread(target=parser, args=(d_list,))
        t1.start(), t2.start()
        t1.join(), t2.join()
        saver(d_list, save_path)
        system('cls')
