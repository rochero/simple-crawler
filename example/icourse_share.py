"""
@author Jacob
@describe 获取慕课所有课程信息
"""

import requests
from requests_html import HTMLSession
import json


# 所有课程类别id
c = {}
sql = []

# 解析json数据
def parsing_json(data, category, t):
    for item in data:
        if item.get('children'):
            parsing_json(item["children"], category + item["text"] + "；", t+item['id']+'|')
        else:
            print(category + item["text"] + "；")
            print(t+item['id']+'|')
            get_course_data(sql, category + item["text"] + "；", t+item['id']+'|')


# 获取课程数据
def get_course_data(sql, categ, tags):
    session = HTMLSession()
    url = "https://www.icourses.cn/web//sword/portal/shareSearchPage?kw=&eduLevel={}&priSubjectLevel={}&subSubjectLevel={}&thirdSubjectLevel=&provinceId=&curPage=1&pageSize=1000&listType=1"
    p = tags.split('|')
    lp = len(p)
    url = url.format(p[0] if lp>=1 else '',p[1] if lp>=2 else '',p[2] if lp>=3 else '')
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36 Edg/81.0.416.53",
    }
    response = session.get(url, headers=headers)
    for s in response.html.xpath('//li[@class="icourse-share-list-i"]'):
        link = s.xpath('.//a[@class="icourse-list-content-title-text"]/@href',first=True)
        intro = s.xpath('.//p[@class="icourse-list-content-text"]/text()',first=True)
        sql.append([
            '' if not link else link.split('=')[-1],
            s.xpath('.//a[@class="icourse-list-content-title-text"]/text()',first=True),
            categ,
            tags,
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
    res = json.load(open('icourse_share.json', 'r', encoding='utf-8'))['model']
    parsing_json(res, "", "")
    append_data_txt(sql)
