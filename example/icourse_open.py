"""
@author Jacob
@describe 获取慕课所有课程信息
"""

import requests
from requests_html import HTMLSession
import json


# 所有课程类别id
c = [
    {
        "id": "01",
        "text": "哲学",
        "cnt": 3
    },
    {
        "id": "02",
        "text": "经济学",
        "cnt": 3
    },
    {
        "id": "03",
        "text": "法学",
        "cnt": 4
    },
    {
        "id": "04",
        "text": "教育学",
        "cnt": 2
    },
    {
        "id": "05",
        "text": "文学",
        "cnt": 6
    },
    {
        "id": "06",
        "text": "历史学",
        "cnt": 3
    },
    {
        "id": "07",
        "text": "理学",
        "cnt": 6
    },
    {
        "id": "08",
        "text": "工学",
        "cnt": 12
    },
    {
        "id": "09",
        "text": "农学",
        "cnt": 2
    },
    {
        "id": 10,
        "text": "医学",
        "cnt": 6
    },
    {
        "id": 12,
        "text": "管理学",
        "cnt": 4
    },
    {
        "id": 13,
        "text": "艺术学",
        "cnt": 4
    },
    {
        "id": 14,
        "text": "就业创业课",
        "cnt": 1
    }
]
sql = []

# 获取课程数据
def get_course_data(sql, id, text, page):
    session = HTMLSession()
    url = "https://www.icourses.cn/web//sword/portal/videoSearchPage?kw=&catagoryId={}&currentPage={}&listType=1"
    
    url = url.format(id,page)
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36 Edg/81.0.416.53",
    }
    response = session.get(url, headers=headers)
    for s in response.html.xpath('//li[@class="icourse-video-list-i"]'):
        link = s.xpath('.//a[@class="icourse-list-content-title-text"]/@href',first=True)
        print(link)
        intro = s.xpath('.//p[@class="icourse-list-content-text"]/text()',first=True)
        sql.append([
            '' if not link else link.split('=')[-1],
            s.xpath('.//a[@class="icourse-list-content-title-text"]/text()',first=True),
            text,
            'https:'+link,
            s.xpath('.//span[@class="icourse-list-school"]/text()',first=True),
            s.xpath('.//span[@class="icourse-list-teacher"]/text()',first=True),
            s.xpath('.//span[@class="icourse-list-number"]/text()',first=True),
            s.xpath('.//span[@class="icourse-list-number-comment"]/text()',first=True),
            "" if not intro else "\""+intro.strip().replace("\t","").replace("\n","")+"\""
        ]
        )

def append_data_txt(data:list):
        file = open("a.txt","a+",errors='ignore')
        if data:
            for d in data:
                file.write('\t'.join(str(item) for item in d)+'\n')
        file.close()

def icourse():
    for i in c:
        for j in range(1, i['cnt']+1):
            get_course_data(sql, i['id'], i['text'], j)
    append_data_txt(sql)