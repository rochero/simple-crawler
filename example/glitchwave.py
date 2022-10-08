from threading import Lock
from os import system
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

sql = []
mutux = Lock()
# 获取课程数据
def get_data(pref):
    url,payload = pref
    requests.packages.urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        'accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en,zh-CN;q=0.9,zh;q=0.8',
        'content-length': '127',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'cookie': '_ga=GA1.2.738977607.1626608161; _gid=GA1.2.1531817368.1626608161; sec_bs=e0a33e514db68139ff799eab8071403f; sec_ts=1626664584; sec_id=3fc3af3f9c137ce59f2ae7bab1c49bbd',
        'origin': 'https://glitchwave.com',
        'referer': 'https://glitchwave.com/games/genre/action/4/',
        'sec-ch-ua': '" Not;A Brand";v="99", "Microsoft Edge";v="91", "Chromium";v="91"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.70',
        'x-requested-with': 'XMLHttpRequest',
        'Host': 'glitchwave.com',
    }
    try_cnt = 3
    while try_cnt > 0:
        try:
            response = session.post(
                url,
                data=payload,
                headers=headers,
                timeout=30,
                verify=False,
                proxies={'http':'127.0.0.1:2334','https':'127.0.0.1:2334'}
            )
        except Exception:
            time.sleep(30.0/try_cnt)
            try_cnt -= 1
            continue                
        if response and response.status_code == 200:
            return response
        else:
            if response.status_code == 404:
                return None
            if response.status_code == 503:
                break
            time.sleep(30.0/float(try_cnt))
            try_cnt -= 1
    mutux.acquire(10)
    append_data_txt([[payload]],'lost.txt')
    mutux.release()
    print('爬取失败！')
    say('爬取失败！')
    return None

def glitchwave(load_path:str='', save_path:str='', group_len:int = 200, max_workers:int = 16, lag:int = 0):
    m = [
    # ['arcade',34769,1,7],
    # ['driving',35135,1,4],
    # ['edutainment',34522,1,3],
    # ['fitness',34534,1,1],
    # ['incremental-game',37068,1,2],
    # ['maze',34460,1,6],
    # ['mmo',34702,1,6],
    # ['open-world',34488,10,12],
    # ['party',34494,1,3],
    # ['racing',34447,1,21],
    # ['rhythm',34471,1,6],
    # ['roguelite',35228,1,5],
    # ['social-network-game',34958,1,1],
    # ['sports',34451,1,36],
    # ['stealth',34455,1,5],
    ['themes',34482,156,188],
    ['trivia',34742,1,3],
    ['user-generated-content',34546,1,2]
    ]
    for x in m:
        type,typeid,start,end = x
        d_list = []
        prefs = []
        cnt=0
        for i in range(start,end+1):
            cnt+=1
            prefs.append(['https://glitchwave.com/httprequest/PageObjectDiscographyLoad', 'object=game&filter=genre&filter_id={}&credit_filter=&page={}&action=PageObjectDiscographyLoad&rym_ajax_req=1&request_token='.format(typeid,i)])
            if ((cnt % group_len) == 0) or (i == end):
                for pref in prefs:
                    r = get_data(pref)
                    if r:
                        s = None
                        try:
                            s = json.loads(r.text.strip().replace('RYMobjectListPage._loadCallback(','').replace(');','')).get('items')
                        except Exception:
                            append_data_txt([[pref[1]]],'lost.txt')
                            time.sleep(8*random.random())
                            pass
                        if s:
                            for item in s:
                                id = item.get('game_id')
                                genre = '|'.join(x.get('name_display') for x in item.get('genres'))
                                r = item.get('rating_info')
                                score = r.get('avg_rating')
                                total_weight = r.get('total_weight')
                                indicator = r.get('indicator')
                                num_all = r.get('num_all')
                                num_ratings = r.get('num_ratings')
                                num_reviews_all = r.get('num_reviews_all')
                                num_want_all = r.get('num_want_all')
                                num_plays = r.get('num_plays')
                                rating_dist='|'.join(str(d) for d in r.get('rating_dist')) if r.get('rating_dist') else ''
                                rating_trend='|'.join((str(d.get('avg'))+','+str(d.get('cnt'))+','+str(d.get('year'))) for d in r.get('rating_trend')) if r.get('rating_trend') else ''
                                release = item.get('release_year')
                                title = item.get('title_display')
                                url = 'https://glitchwave.com/game/'+item.get('url')
                                d_list.append([id, title, genre, score, num_all, num_ratings,indicator,
                                num_reviews_all, num_want_all, num_plays, rating_dist, rating_trend, release, url,total_weight,
                                type])
                            print(pref[1])
                            if lag > 0:
                                time.sleep(lag*(0.2*random.random()+0.1))
                append_data_xlsx(d_list,save_path,'genre',True)
                system('cls')
                d_list.clear()
                prefs.clear()