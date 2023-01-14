from concurrent.futures import ThreadPoolExecutor as Pool
from math import ceil
import re
import json
import traceback
import logging
import random
import time
from winsound import Beep
from os import system
from threading import Lock
from msedge.selenium_tools import Edge, EdgeOptions
from tqdm import tqdm
from utils.tool import load_txt, save_csv, save_txt, save_xlsx

# lock for writing logs
lock = Lock()

# consecutive request failed count
failed_cnt = 0

# global config
cfg = {
    # default url for test after the browser starts
    'test_url': '',
    'driver_path': 'C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe',
    # choose to disable load options(picture, css, js, extension)
    'disable': (True, True, True, True),
    # max retry count per request
    'retry': 3,
    # min wait seconds for next retry request
    'wait': 3,
    # max consecutive request failed count
    'max_failed_count': 5,
    # request delay interval (min, max)
    'interval': (0, 0),
    'log': './log/log.txt',
    'error_while_parsing': './log/err.txt',
    'error_while_scraping': './log/lost.txt',
    '404': './log/404.txt',
}

logging.basicConfig(filename=cfg['log'],
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s \n %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def start_driver(test_url: str = '', disable: tuple = ()):
    options = EdgeOptions()
    options.use_chromium = True
    test_url = cfg['test_url'] if not test_url else test_url
    disable_img, disable_css, disable_js, disable_ext = cfg['disable'] if not disable else disable
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2 if disable_img else 1,
            'permissions.default.stylesheet': 2 if disable_css else 1,
            'javascript': 2 if disable_js else 1
        }
    }
    options.add_experimental_option('prefs', prefs)
    options.add_argument("disable-gpu")
    options.add_argument("start-maximized")
    options.add_argument("log-level=3")
    options.add_argument("disable-infobars")
    if disable_ext:
        options.add_argument("disable-extensions")
    driver = Edge(executable_path=cfg['driver_path'], options=options)
    if test_url:
        driver.get(test_url)
    return driver


def processor(driver: Edge, urls: list, bar: tqdm):
    global failed_cnt
    rs = []
    max_retry = cfg['retry'] if cfg['retry'] and cfg['retry'] > 0 else 3
    wait_time = cfg['wait'] if cfg['wait'] and cfg['wait'] > 0 else 3.0
    min_lag, max_lag = cfg['interval'] if cfg['interval'] else (0, 0)
    for url in urls:
        error = False
        try_cnt = max_retry
        while try_cnt >= 0:
            try:
                driver.get(url)
            except Exception:
                time.sleep(wait_time*random.uniform(1, 2))
                try_cnt -= 1
                continue
            if is_right(driver):
                r = parse_data(driver)
                if r:
                    rs.append(r)
                failed_cnt = 0
                break
            else:
                if no_retry(driver):
                    error = True
                    break
                time.sleep(wait_time*random.uniform(1, 2))
                try_cnt -= 1
        if error or try_cnt < 0:
            lock.acquire(10)
            try:
                if not_found(driver):
                    print('not_found: {}'.format(url))
                    save_txt([[url]], cfg['404'])
                else:
                    print('request failed: {}'.format(url))
                    save_txt([[url]], cfg['error_while_scraping'])
            finally:
                lock.release()
                failed_cnt += 1
                if failed_cnt > cfg['max_failed_count']:
                    Beep(440, 1000)
                    driver.close()
                    exit(1)
        bar.update(1)
        if max_lag > min_lag and min_lag > 0:
            time.sleep(random.uniform(min_lag, max_lag))
    return rs


def is_right(driver):
    return True


def no_retry(driver):
    return True


def not_found(driver):
    return False


def parse_data(driver: Edge):
    title = year = pub = tags = score = votes = genre = None
    try:
        title = xpath(driver, '//h1')
        title = title.text if title else ''
        year = xpath(
            driver, '//td[contains(text(), "Release")]/following-sibling::td/a[contains(@href,"year")]')
        year = int(year.text) if year and year.text else ''
        pub = xpath(
            driver, '//td[contains(text(), "Creator") or contains(text(), "Develop")]/following-sibling::td/a[contains(@href, "list.php")]')
        pub = pub.text if pub else ''
        genre = xpath(
            driver, '//td[contains(text(), "Genre:")]/following-sibling::td/a[contains(@href,"genre")]')
        genre = genre.text if genre else ''
        tags = xpath(
            driver, '//td[contains(text(), "Tags")]/following-sibling::td/a[contains(@href,"tags")]', False)
        tags = '|'.join(t.text for t in tags) if tags else ''
        script = xpath(driver, '//script[@type="application/ld+json"]')
        script = script.get_attribute('innerHTML') if script else ''
        p = re.search('"ratingValue":\s?"(.*?)"', script, re.S)
        score = float(p.group(1)) if p else ''
        q = re.search('"reviewCount":\s?"(\d+?)"', script, re.S)
        votes = int(q.group(1)) if q else ''
    except Exception:
        traceback.print_exc(limit=3)
        lock.acquire(10)
        try:
            save_txt([[driver.current_url]], cfg['error_while_parsing'])
        finally:
            lock.release()
        logging.error(traceback.format_exc(limit=3))
    return [title, driver.current_url, year, pub, genre, tags, score, votes]


def xpath(driver, pattern: str, first=False, text=False):
    e = None
    try:
        e = driver.find_element(
            'xpath', pattern) if first else driver.find_elements('xpath', pattern)
        if e and text:
            e = [x.text if x.text else x.get_atrribute('innerHTML') for x in e] if isinstance(
                e, list) else e.text if e.text else e.get_attribute('innerHTML')
    except Exception:
        logging.error(traceback.format_exc(limit=3))
    finally:
        return e


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
    drivers = []
    for i in range(max_workers):
        drivers.append(start_driver())
    for i, chunk in enumerate(chunks, 1):
        d_list = []
        with tqdm(desc='scraping and parsing...{}/{}'.format(i, len(chunks)), total=len(chunk)) as bar:
            slice_size = ceil(len(chunk)/max_workers)
            slices = [chunk[i:i+slice_size]
                      for i in range(0, len(chunk), slice_size)]
            with Pool(max_workers) as t:
                for r in t.map(processor, drivers, slices, [bar]*max_workers):
                    for x in r:
                        append_data(d_list, x)
        saver(d_list, save_path)
        system('cls')
