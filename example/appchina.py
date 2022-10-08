"""
@author Jacob
@describe 获取慕课所有课程信息
"""

import requests
from requests_html import HTMLSession
import json
import time
sql = []
c = [
    # {
    #     "id": 411,
    #     "text": "益智"
    # },
    # {
    #     "id": 412,
    #     "text": "射击"
    # },
    # {
    #     "id": 413,
    #     "text": "策略"
    # },
    # {
    #     "id": 414,
    #     "text": "动作冒险"
    # },
    # {
    #     "id": 415,
    #     "text": "赛车竞速"
    # },
    # {
    #     "id": 416,
    #     "text": "模拟经营"
    # },
    # {
    #     "id": 417,
    #     "text": "角色扮演"
    # },
    # {
    #     "id": 418,
    #     "text": "体育运动"
    # },
    # {
    #     "id": 419,
    #     "text": "棋牌桌游"
    # },
    # {
    #     "id": 420,
    #     "text": "虚拟养成"
    # },
    # {
    #     "id": 421,
    #     "text": "音乐"
    # },
    # {
    #     "id": 422,
    #     "text": "对战格斗"
    # },
    # {
    #     "id": 423,
    #     "text": "辅助工具"
    # },
    {
        "id": 424,
        "text": "网络游戏"
    }
]
# 获取课程数据
def get_data(sql, id, type):
    session = HTMLSession()
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36 Edg/81.0.416.53",
    }
    cnt = 1
    while True:
        url = "http://m.appchina.com/ajax/cat/{}/{}".format(id, cnt)
        try_cnt = 3
        res = {}
        while try_cnt > 0:
            try:
                response = session.get(url, headers=headers)
                res = response.json()
            except Exception:
                time.sleep(6/try_cnt)
                try_cnt -= 1
                continue                
            if res:
                break
            else:
                time.sleep(6/try_cnt)
                try_cnt -= 1
        print(url)
        cnt+=1
        for s in res['list']:
            sql.append(
                [
                    s.get('packageName'),
                    s.get('name'),
                    type,
                    s.get('shortDesc'),
                    s.get('size'),
                    s.get('likePercentage'),
                    s.get('apkUrl')
                ]
            )
        if not res['nextPage']:
            break

def append_data_txt(data:list):
        file = open("a.txt","a+",errors='ignore')
        if data:
            for d in data:
                file.write('\t'.join(str(item) for item in d)+'\n')
        file.close()

def appchina():
    for i in c:
        get_data(sql, i['id'], i['text'])
    append_data_txt(sql)