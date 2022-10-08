

from os import system
from utils.save import append_data_txt, append_data_xlsx
import requests
from requests_html import HTMLSession
import json
import re
from concurrent.futures import ThreadPoolExecutor
import traceback
import time
sql = []

# 获取课程数据
def get_data(pref):
    url, payload = pref
    requests.packages.urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
        "Connection": "keep-alive",
        "Content-Length": "47",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": "mtid=\"srZ9f4oYg1sovEDiE7vUBQ==\"; _gaexp=GAX1.2.QYf6kn8qQPGBOr76XWO3ng.18865.1; _gcl_au=1.1.367541204.1626490246; _gid=GA1.2.1695924830.1626490251; _fbp=fb.1.1626490264995.371611272; daily_feed=Y; recentSearch=spelunky%7C; JSESSIONID=661163D5ED82DD3B31ACB931A2973BB8; _ba_rand=63; _ga_BVR3TF4HPS=GS1.1.1626495337.2.1.1626497166.0; _ga=GA1.2.520242140.1626490246; _gat=1",
        "Host": "minimap.net",
        "Origin": "https://minimap.net",
        "Referer": "https://minimap.net/search/game?sort=0%2C0%2C-1&p=2",
        "sec-ch-ua": "\" Not;A Brand\";v=\"99\", \"Microsoft Edge\";v=\"91\", \"Chromium\";v=\"91\"",
        "sec-ch-ua-mobile": "?0",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67",
        "X-Requested-With": "XMLHttpRequest",
    }
    try_cnt = 3
    while try_cnt > 0:
        try:
            response = session.post(url, data=payload, headers=headers, timeout=5, verify=False)
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
    append_data_txt([[url]],'lost.txt')
    print('url request failed')
    return None

def minimap(load_path='', save_path='', group_len = 200, max_workers = 16):
    d_list = []
    prefs = []
    # i_list = []
    # with open(load_path,'r') as f:
	#     for line in f:
	# 	    i_list.append(line.strip())
    cnt = 0
    for i in range(0,5396):
        cnt+=1
        prefs.append(['https://minimap.net/view/search/searchGame', 'sort=0%2C0%2C-1&p={}&isInit=true&refreshCnt=true'.format(i)])
        if ((cnt % group_len) == 0) or (i == 5395):
            with ThreadPoolExecutor(max_workers) as t:
                for r in t.map(get_data, prefs):
                    ss = r.json().get('gameList') if r else None
                    if ss:
                        for s in ss:
                            sn = s.get('gameSn')
                            dev = '|'.join(str(t.get('name')) for t in s.get('developerList')) if s.get('developerList') else ''
                            pub = '|'.join(str(t.get('name')) for t in s.get('publisherList')) if s.get('publisherList') else ''
                            score = -1
                            scoreCnt = -1
                            if s.get('gameScoreList'):
                                for g in s.get('gameScoreList'):
                                    if g.get('crawlSource') == 90:
                                        score = g.get('score')
                                        scoreCnt = g.get('scoreCnt')
                            genre = '|'.join(str(t.get('nameEng')) for t in s.get('genreList')) if s.get('genreList') else ''
                            titleEng = s.get('nameEng')
                            title = s.get('nameOriginal')
                            platform = ''
                            release = ''
                            u = 'https://minimap.net/game/'+s.get('url')
                            if s.get('compactReleaseDateList'):
                                platform = '|'.join(str(h.get('comment')) for h in s.get('compactReleaseDateList'))
                                release = '|'.join(str(h.get('dateFormatReleaseDate')) for h in s.get('compactReleaseDateList'))
                            d_list.append([
                                sn, titleEng, title,
                                genre, dev, pub, platform, release,
                                score, scoreCnt,
                                u
                                ])
                            print(titleEng)
            append_data_xlsx(d_list,save_path)
            system('cls')
            d_list.clear()
            prefs.clear()