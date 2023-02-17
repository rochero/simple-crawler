from os import system
from winsound import Beep
import re
import json
import traceback
import logging
import random
import time
from threading import Lock, Thread
from queue import Queue
from requests.packages import urllib3
from requests import Session, Response
from parsel import Selector
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from utils.tool import save_raw, save_txt, save_xlsx, save_csv

urllib3.disable_warnings()

# lock for writing logs
lock = Lock()

# sign of the end of scraping
_end = object()

# store response waiting for parse
q = Queue(1000)

# session pool for reuse
sq = Queue()

# consecutive request failed count
failed_cnt = 0

# global config
cfg = {
    # max retry count per request
    'retry': 2,
    # max consecutive request failed count
    'max_failed_count': 100,
    # min wait seconds for next retry request
    'wait': 3,
    # request delay interval (min, max)
    'interval': (0.1, 0.1),
    'parse_worker_num': 16,
    'log': './log/log.txt',
    'parse_error': './log/err.txt',
    'scrape_error': './log/lost.txt',
    '404': './log/404.txt',
    'headers': {
        'accept': '*/*',
        'origin': 'https://www.google.com',
        'referer': 'https://www.google.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.46'
    },
    'proxies': {'http': '127.0.0.1:2334', 'https': '127.0.0.1:2334'},
}

logging.basicConfig(filename=cfg['log'], level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_data(pref, session=None):
    global failed_cnt
    url = pref
    res = None
    if not session:
        try:
            session = sq.get(timeout=20)
        except Exception:
            session = Session()
    headers = cfg.get('headers')
    retry_cnt = cfg.get('retry') or 2
    wait_time = cfg.get('wait') or 2
    while retry_cnt >= 0:
        try:
            res = session.get(
                url,
                headers=headers,
                timeout=10,
                verify=False,
                proxies=cfg.get('proxies')
            )
            if is_right(res):
                sq.put(session)
                failed_cnt -= 1 if failed_cnt else 0
                return res
        except:
            logging.info(traceback.format_exc(limit=3))
        if no_retry(res):
            break
        time.sleep(wait_time*random.uniform(1, 2))
        retry_cnt -= 1
    lock.acquire()
    try:
        print('request failed: {}'.format(url))
        save_txt([[url,res.status_code]], cfg['scrape_error'])
    finally:
        lock.release()
        failed_cnt += 1
        if failed_cnt > cfg['max_failed_count']:
            Beep(440, 1000)
            exit(0)
        sq.put(session)
    return None


def is_right(res: Response):
    return res and (res.status_code//100 == 2 or res.status_code//100 == 3)


def no_retry(res: Response):
    return res and (res.status_code == 404 or res.status_code == 503)


def not_found(res: Response):
    return res and res.status_code == 404


def parse_data(r: Response):
    if not r:
        return None
    if not r.content:
        raise Exception('response content is empty')
    global failed_cnt
    res = []
    title = alt = id = date = year = genre = theme = sys = tags = desc = dev = pub = size = score = votes = 0
    try:
        s = Selector(r.text)
        # j = r.json()['content']
        if s:
            s.xpath()
            return None
        raise Exception('target data not found')
    except Exception as e:
        traceback.print_exc(limit=3)
        lock.acquire()
        try:
            save_txt([[r.url, e]], cfg['parse_error'])
        finally:
            lock.release()
            failed_cnt += 1
        logging.info(traceback.format_exc(limit=3))
        return None


def append_data(d: list, r):
    if not r:
        return
    if isinstance(r, list):
        d += r if isinstance(r[0], list) else [r]
    else:
        d.append([r])


def sleep(interval=None):
    min, max = interval or cfg.get('interval')
    if max > min and min > 0:
        time.sleep(random.uniform(min, max))


def scraper(l, i, prefs, max_workers):
    with ThreadPoolExecutor(max_workers) as t:
        for r in tqdm(t.map(get_data, prefs), desc='scraping...{}/{}'.format(i, l), total=len(prefs)):
            q.put(r)
            sleep()
    q.put(_end)
    while q.qsize() > 1:
        print(f'\rparsing...{q.qsize()-1:8d} left', end='', flush=True)


def parse_worker(d: list):
    while True:
        r = q.get()
        if r is _end:
            q.put(r)
            return
        append_data(d, parse_data(r))


def parser(d: list):
    with ThreadPoolExecutor(cfg['parse_worker_num']) as t:
        for _ in range(cfg['parse_worker_num']):
            t.submit(parse_worker, d)


def saver(d: list, save_path: str):
    print('saving...')
    if save_path.endswith('txt'):
        save_txt(d, save_path)
    elif save_path.endswith('xlsx'):
        save_xlsx(d, save_path)
    elif save_path.endswith('csv'):
        save_csv(d, save_path)
    else:
        raise RuntimeError('not saved: unsupported file format')


def one_worker_crawl(chunks: list, save_path: str):
    session = Session()
    for chunk in chunks:
        d_list = []
        for c in chunk:
            print(c)
            append_data(d_list, parse_data(get_data(c, session)))
            sleep()
        saver(d_list, save_path)
        system('cls')


def multi_workers_crawl(chunks: list, save_path, max_workers: int = 2):
    for _ in range(0, max_workers):
        sq.put(Session())
    for i, chunk in enumerate(chunks, 1):
        while not q.empty():
            q.get()
        # d_list: [[],[]...,[]]
        d_list = []
        t1 = Thread(target=scraper, args=(
            len(chunks), i, chunk, max_workers,), daemon=True)
        t2 = Thread(target=parser, args=(d_list,), daemon=True)
        t1.start(), t2.start()
        t1.join(), t2.join()
        saver(d_list, save_path)
        system('cls')


def crawl(u_list=[], save_path: str = '', chunk_size: int = 0, max_workers: int = 1):
    chunks = [u_list[i:i + chunk_size]
              for i in range(0, len(u_list), chunk_size)]
    if max_workers < 2:
        one_worker_crawl(chunks, save_path)
    else:
        multi_workers_crawl(chunks, save_path)
