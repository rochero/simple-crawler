from os import system
from winsound import Beep
import re
import json
import traceback
import logging
import random
import time
from threading import Lock, Thread, Event
from queue import Queue
from requests.packages import urllib3
from requests_html import HTMLSession, HTMLResponse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from utils.tool import save_raw, save_txt, save_xlsx, save_csv

urllib3.disable_warnings()

# lock for writing logs
lock = Lock()

# unfinished flag for scraping
unfinished = Event()

# store response waiting for parse
q = Queue()

# session pool for reuse
sq = Queue()

# consecutive request failed count
failed_cnt = 0

# global config
cfg = {
    # max retry count per request
    'retry': 2,
    # max consecutive request failed count
    'max_failed_count': 5,
    # min wait seconds for next retry request
    'wait': 3,
    # request delay interval (min, max)
    'interval': (0.1, 0.2),
    'parse_worker_num': 16,
    'log': './log/log.txt',
    'error_while_parsing': './log/err.txt',
    'error_while_scraping': './log/lost.txt',
    '404': './log/404.txt',
    'headers': {
        'accept': '*/*',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.46'
    },
    'proxies': {'http': '127.0.0.1:2334', 'https': '127.0.0.1:2334'},
}

logging.basicConfig(filename=cfg['log'], level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_data(pref, session=None):
    global failed_cnt
    url = pref
    res = None
    if not session:
        try:
            session = sq.get(timeout=20)
        except Exception:
            session = HTMLSession()
    headers = cfg.get('headers')
    try_cnt = cfg.get('retry') if cfg.get(
        'retry') and cfg.get('retry') > 0 else 3
    wait_time = cfg.get('wait') if cfg.get(
        'wait') and cfg.get('wait') > 0 else 3.0
    while try_cnt >= 0:
        try:
            res = session.get(
                url,
                headers=headers,
                timeout=10,
                verify=False,
                proxies=cfg.get('proxies')
            )
        except Exception:
            time.sleep(wait_time*random.uniform(1, 2))
            try_cnt -= 1
            continue
        if is_right(res):
            sq.put(session)
            failed_cnt = 0
            return res
        else:
            if no_retry(res):
                break
            time.sleep(wait_time*random.uniform(1, 2))
            try_cnt -= 1
    lock.acquire(10)
    try:
        if not_found(res):
            print('not found: {}'.format(url))
            save_txt([[url]], cfg['404'])
        else:
            print('request failed: {}'.format(url))
            save_txt([[url]], cfg['error_while_scraping'])
    finally:
        lock.release()
        failed_cnt += 1
        if failed_cnt > cfg['max_failed_count']:
            Beep(440, 1000)
            exit(1)
        sq.put(session)
    return None


def is_right(res):
    return res and (res.status_code == 200 or res.status_code == 304)


def no_retry(res):
    return res and (res.status_code == 404 or res.status_code == 503)


def not_found(res):
    return res and res.status_code == 404


def parse_data(r: HTMLResponse):
    if not r:
        return None
    global failed_cnt
    res = []
    title = alt = id = date = year = genre = theme = sys = tags = desc = dev = pub = size = score = votes = 0
    try:
        s = r.html
        if s:
            title = s.xpath(
                '//a[@itemprop="mainEntityOfPage"]/text()', first=True)
            dev = s.xpath(
                '//span[@itemprop="author"]//span[@itemprop="name"]/text()', first=True)
            pub = s.xpath(
                '//h5[contains(text(),"Publisher")]/following-sibling::span[1]/a/text()')
            pub = '|'.join(pub) if pub else ''
            date = s.xpath(
                '//time[@itemprop="datePublished"]/@datetime', first=True)
            desc = s.xpath('//p[@itemprop="description"]/text()', first=True)
            sys = s.xpath('//span[@itemprop="operatingSystem"]/a/text()')
            sys = '|'.join(sys) if sys else ''
            score = s.xpath(
                '//meta[@itemprop="ratingValue"]/@content', first=True)
            votes = s.xpath(
                '//span[@itemprop="ratingCount"]/text()', first=True)
            tags = s.xpath(
                '//div[@id="tagsform"]//a[contains(@href, "/tags/")]/text()')
            tags = '|'.join(tags) if tags else ''
            genre = s.xpath('//span[@itemprop="genre"]/a/text()')
            genre = '|'.join(genre) if genre else ''
            theme = s.xpath(
                '//h5[contains(text(),"Theme")]/following-sibling::span[1]/a/text()')
            theme = '|'.join(theme) if theme else ''
            engine = s.xpath(
                '//h5[contains(text(),"Engine")]/following-sibling::span[1]/a/text()')
            engine = '|'.join(engine) if engine else ''
            players = s.xpath(
                '//h5[contains(text(),"Player")]/following-sibling::span[1]/a/text()', first=True)
            project = s.xpath(
                '//h5[contains(text(),"Project")]/following-sibling::span[1]/a/text()', first=True)
            return [title, r.url, genre, date, sys, project, engine, theme, tags, desc, dev, pub, players, score, votes]
        return None
    except Exception:
        traceback.print_exc(limit=3)
        lock.acquire(10)
        try:
            save_txt([[r.url]], cfg['error_while_parsing'])
        finally:
            lock.release()
            failed_cnt += 1
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
    min_lag, max_lag = cfg.get('interval') if cfg.get('interval') else (0, 0)
    with ThreadPoolExecutor(max_workers) as t:
        for r in tqdm(t.map(get_data, prefs), desc='scraping...{}/{}'.format(i, l), total=len(prefs)):
            if r and all(r):
                q.put(r)
            if max_lag > min_lag and min_lag > 0:
                time.sleep(random.uniform(min_lag, max_lag))
    unfinished.clear()


def parse_worker(d: list):
    while unfinished.isSet():
        try:
            r = q.get(timeout=1)
            if r:
                append_data(d, parse_data(r))
        except Exception:
            pass


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


def crawl(u_list=[], save_path: str = '', chunk_size: int = 0, max_workers: int = 1):
    chunks = [u_list[i:i + chunk_size]
              for i in range(0, len(u_list), chunk_size)]
    if max_workers < 2:
        session = HTMLSession()
        for chunk in chunks:
            d_list = []
            for c in chunk:
                print(c)
                append_data(d_list, parse_data(get_data(c, session)))
                min_lag, max_lag = cfg.get(
                    'interval') if cfg.get('interval') else (0, 0)
                if max_lag > min_lag and min_lag > 0:
                    time.sleep(random.uniform(min_lag, max_lag))
            saver(d_list, save_path)
            system('cls')
        return
    for _ in range(0, max_workers):
        sq.put(HTMLSession())
    for i, chunk in enumerate(chunks, 1):
        unfinished.set()
        # d_list: [[],[]...,[]]
        d_list = []
        t1 = Thread(target=scraper, args=(
            len(chunks), i, chunk, max_workers,), daemon=True)
        t2 = Thread(target=parser, args=(d_list,), daemon=True)
        t1.start(), t2.start()
        t1.join(), t2.join()
        saver(d_list, save_path)
        system('cls')
