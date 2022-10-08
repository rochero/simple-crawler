from concurrent.futures import ThreadPoolExecutor as Pool
from math import ceil
from os import system
import random
import time
import traceback
import logging
from threading import Lock, Thread
from msedge.selenium_tools import Edge, EdgeOptions
from tqdm import tqdm
from utils.tool import load_txt, save_txt, save_xlsx, say

# 保证写入文件时线程安全的锁
mutux = Lock()

# 解析响应数据时发生的异常会记录到日志中
logging.basicConfig(filename='log.txt', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
# 全局配置
cfg = {
    # 浏览器驱动配置
    # 浏览器启动后默认请求的URL
    'test_url': "https://www.vgtime.com",
    # 浏览器驱动文件位置
    'driver_path': "C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe",
    # 浏览器选择禁止加载项，默认全部禁用（图片, CSS, JS, 扩展程序）
    'disable': (True, True, True, True),

    # 请求URL时配置
    # 每个请求的最大重试次数
    'retry': 3,
    # 请求重试的最大等待时间
    'wait': 3.0,
    # 请求的时间间隔范围（最小间隔，最大间隔）
    'interval': (0, 0),
}


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


def processor(pref):
    res, driver, urls, bar = pref
    max_retry = cfg['retry'] if cfg['retry'] and cfg['retry'] > 0 else 3
    wait_time = cfg['wait'] if cfg['wait'] and cfg['wait'] > 0 else 3.0
    min_lag, max_lag = cfg['interval'] if cfg['interval'] else (0, 0)
    for url in urls:
        error = False
        try_cnt = max_retry
        while try_cnt > 0:
            try:
                driver.get(url)
            except Exception:
                time.sleep(wait_time/float(try_cnt))
                try_cnt -= 1
                continue
            if is_right(driver):
                append_data(res, parse_data(driver))
                break
            else:
                if no_retry(driver):
                    error = True
                    break
                time.sleep(wait_time/float(try_cnt))
                try_cnt -= 1
        if error or try_cnt == 0:
            mutux.acquire(10)
            try:
                if not_found(driver):
                    print('not_found: {}'.format(url))
                    save_txt([[url]], '404.txt')
                else:
                    print('request failed: {}'.format(url))
                    say('request failed')
                    save_txt([[url]], 'lost.txt')
            finally:
                mutux.release()
        bar.update(1)
        if max_lag > min_lag and min_lag > 0:
            time.sleep(random.uniform(min_lag, max_lag))


def is_right(driver):
    """
    判断响应的数据是否正确
    """
    return True


def no_retry(driver):
    """
    根据响应的数据决定是否重试
    """
    return True


def not_found(driver):
    """
    判断请求的资源是否不存在
    """
    return False


def parse_data(driver: Edge):
    # title = platform = None
    # try:
    #     title = driver.find_element_by_xpath('//h2/a')
    #     title = title.text if title else ''
    #     platform = driver.find_elements_by_xpath(
    #         '//div[@class="descri_box"]/div[@class="jizhong_tab"]/span')
    #     platform = '|'.join(p.text for p in platform) if platform else ''
    # except Exception:
    #     traceback.print_exc(limit=3)
    #     mutux.acquire(10)
    #     try:
    #         save_txt([[driver.current_url]], 'err.txt')
    #     finally:
    #         mutux.release()
    #     logging.debug(traceback.format_exc(limit=3))
    return ['test']


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
    save_xlsx(d, save_path)


def crawl(u_list=[], save_path: str = '', chunk_size: int = 0, max_workers: int = 1):
    """
    此爬虫通过浏览器模拟用户访问资源，将 URL 列表分块依次处理并保存。
    每块通过多个浏览器进程并行处理。

    参数：
    - u_list: 待爬取的 URL 列表
    - save_path: 保存最终数据的文件路径
    - chunk_size: URL 列表分块的大小
    - max_workers: 最大工作线程数量，等于大块拆分后的小块数量

    """
    chunks = [u_list[i:i + chunk_size]
              for i in range(0, len(u_list), chunk_size)]
    drivers = []
    for i in range(max_workers):
        drivers.append(start_driver())
    for i, chunk in enumerate(chunks, 1):
        d_list = []
        ts: list[Thread] = []
        with tqdm(desc='scraping and parsing...{}/{}'.format(i, len(chunks)), total=len(chunk)) as bar:
            slice_size = ceil(len(chunk)/max_workers)
            slices = [chunk[i:i+slice_size]
                      for i in range(0, len(chunk), slice_size)]
            args = ((d_list, driver, slice, bar)
                    for driver, slice in zip(drivers, slices))
            with Pool(max_workers) as t:t.map(processor, args)
        saver(d_list, save_path)
        system('cls')
