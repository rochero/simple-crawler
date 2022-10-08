

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
    url = pref
    requests.packages.urllib3.disable_warnings()
    session = HTMLSession()
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36 Edg/81.0.416.53",
    }
    try_cnt = 3
    while try_cnt > 0:
        try:
            response = session.get(url, headers=headers, timeout=5, verify=False)
        except Exception:
            time.sleep(10.0/try_cnt)
            try_cnt -= 1
            continue                
        if response and response.json()['success']:
            return response
        else:
            if response.status_code == 404:
                return None
            time.sleep(10.0/float(try_cnt))
            try_cnt -= 1
    append_data_txt([[url]],'lost.txt')
    print('url request failed')
    return None

def taptap(load_path='', save_path='', group_len = 200, max_workers = 16):
    i_list = []
    d_list = []
    prefs = []
    with open(load_path,'r') as f:
	    for line in f:
		    i_list.append(line.strip())
    cnt = 0
    for i in i_list:
        l = len(i_list)
        cnt+=1
        prefs.append('https://www.taptap.com/webapiv2/app/v2/detail-by-id/{}?X-UA=V%3D1%26PN%3DWebApp%26LANG%3Dzh_CN%26VN_CODE%3D4%26VN%3D0.1.0%26LOC%3DCN%26PLT%3DPC%26DS%3DAndroid%26UID%3D581f4e9a-1adc-4a7d-841c-511cc69b8f7d%26DT%3DPC'.format(i))
        if ((cnt % group_len) == 0) or (cnt == l):
            with ThreadPoolExecutor(max_workers) as t:
                for r in t.map(get_data, prefs):
                    s = r.json().get('data') if r else None
                    if s:
                        identifier = s.get('identifier')
                        id = s.get('id')
                        title = s.get('title')
                        author = s.get('author')
                        desc = '' if not s.get('description') else re.sub(r'(<.*?>)|(&.*?;)|(\n)|(\t)','', s.get('description').get('text'))
                        tags = ''
                        if s.get('tags'):
                            tags = '|'.join(str(t.get('value')) for t in s.get('tags'))
                        stat = s.get('stat')
                        hits = stat.get('hits_total')
                        plays = stat.get('play_total')
                        fans = stat.get('fans_count')
                        score = float(stat.get('rating').get('score'))
                        reviews = stat.get('review_count')
                        v = stat.get('vote_info')
                        v1, v2, v3, v4, v5 = [-1]*5
                        if v:
                            v1, v2, v3, v4, v5 = [v['1'], v['2'],v['3'],v['4'],v['5']]
                        labels = ''
                        tmp = stat.get('review_tags')
                        if tmp and tmp.get('mappings'):
                            labels = '|'.join((t.get('show_mapping').strip()+'({})'.format(t.get('cnt'))) for t in tmp.get('mappings'))
                        d_list.append([
                            identifier,id,title, author, desc, tags, hits,plays,fans,
                            v5, v4, v3, v2, v1,
                            labels,
                            score,reviews
                            ])
                        print(id)
            append_data_xlsx(d_list,save_path)
            system('cls')
            d_list.clear()
            prefs.clear()