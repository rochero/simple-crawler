"""
@author Jacob
@describe 获取学堂在线所有课程信息
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor

c = {}

# 获取课程id
def get_course(page):
    querystring = {"cpage": str(page)}

    url = "http://ssvideo.superlib.com/cxvideo/classify/series/info?videoType=3&orderType=zx"

    payload = "{\"query\":\"\",\"chief_org\":[],\"classify\":[],\"selling_type\":[],\"status\":[],\"appid\":10000}"

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.59',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'http://ssvideo.superlib.com/cxvideo/classify/init?videoType=3',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8',
        'Cookie': 'Hm_lvt_8e8115bd9c8e8f019cfe3083c2210d3f=1624977648,1624979899,1624982389,1624982714; Hm_lvt_8e8115bd9c8e8f019cfe3083c2210d3f=1625016778; Hm_lpvt_8e8115bd9c8e8f019cfe3083c2210d3f=1625016778; JSESSIONID=BAB64202F3614ADCC54AA1B4229AF03C.cxvideo_web_17.40; route=d18b8421f50240421f7cb21f7239f278; lv=1; fid=503; _uid=54108193; uf=569b376a64ccf0319dbf35210ecb914530c7216e74382eb3bf2252b7413f732fdedbdc3d3748995b64749ac8214b027dd807a544f7930b6abeaaa6286f1f1754d0a00e417958448600726a3426cc7f6ca82e5ea415ce939843055ac19f901bafcf2a05f50a9b71be; _d=1625027381261; UID=54108193; vc=5E9C8E69F207525C952ABDDD8545DFF9; vc2=C6432C05EA6C97026661199A25E5350C; vc3=Mn5z5UEcUELuRXHOlHoPml%2FizuE01%2BxD2aMy82z9wxLnlBpTILhzEbPdp0f54dyamvCoqWxJYaWSyLK9sGbEgjC2Mh7R4HA8BFModYMUyCVtRYgFpvOHAiXOcwaQ%2BoQVmmnW1N4wESgZxud8PwirIErbB9ysGmNvjOJ0EMk51D8%3Dc94137b858908cb527abd546b9a00e2c; xxtenc=1cf8be4e40c537e0aa317aa6c3176f36; msign=157893569571200; username=13675555071; uid=54108193; loginType=passport; deptid=328; enc=67333088f1cec82bcd3111cdf6783a71; DSSTASH_LOG=C_33-UN_328-US_54108193-T_1625027381266; ruot=1625027383156; Hm_lpvt_8e8115bd9c8e8f019cfe3083c2210d3f=1625027445'
    }
    try_count = 3
    while try_count > 0:
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            break
        except Exception:
            time.sleep(18/try_count)
    json_list = json.loads(response.text)["serirsPage"]
    return json_list

def parsing_json(data, category):
    for item in data:
        if item.get("cxClassifyList"):
            parsing_json(item["cxClassifyList"], category + item["classifyName"] + "；")
            if not c.get(str(item["cid"])):
                c[str(item["cid"])] = category + item["classifyName"] + "；"
        else:
            c[str(item["cid"])] = category + item["classifyName"] + "；"

# 存储到数据库
def save_to_mysql(sql, course):
    sid, cid, cardD = [course["sid"], course['cid'], course['cardD']]
    intro = course.get('intro')
    sql.append([sid,
                cid,
                c.get(str(cid)),
                "\""+course["sname"].strip()+"\"",
                "http://ssvideo.superlib.com/cxvideo/play/page?sid={}&d={}&cid={}".format(sid,cardD,cid),
                course.get('playcount'),
                "\""+intro.strip().replace("\t","").replace("\n","")+"\"" if intro else '',
                time.strftime('%Y-%m-%d', time.localtime(float(course.get('createDate')/1000))),
                course.get('score'),
                course.get('scorecount'),
                course.get('tdept').strip(),
                course.get('tname').strip(),
                course.get('videonum'),
    ])
    print(sql[-1][3])

def append_data_txt(data:list):
        file = open("a.txt","a+",errors='ignore')
        if data:
            for d in data:
                file.write('\t'.join(str(item) for item in d)+'\n')
        file.close()

def xuetang_online():
    params = []
    file = open("c3.json", "r", encoding='utf-8')
    data = json.load(file)
    file.close()
    parsing_json(data, "")
    for i in range(1,103):
        params.append(i)
    sql = []
    with ThreadPoolExecutor(max_workers=4) as t:
        for result in t.map(get_course, params):
            if len(result) > 0:
                for r in result:
                    save_to_mysql(sql, r)
    append_data_txt(sql)
