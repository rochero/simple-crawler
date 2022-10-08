import csv
import time
import traceback
import pyttsx3
from os import path, makedirs
import openpyxl
import time
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

# 输入毫秒级的时间，转出正常格式的时间


def timeStamp(timeNum):
    timeStamp = float(timeNum/1000)
    timeArray = time.localtime(timeStamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime


def load_txt(load_path, sep='\t'):
    f = open(load_path, 'r', encoding='utf-8', errors='ignore')
    return [l.strip().split(sep) for l in f.readlines()]


def load_pattern(pattern: str, params):
    return [pattern.format(x) for x in params]


def say(option: str):
    engine = pyttsx3.init()
    engine.say(option)
    try:
        engine.runAndWait()
    except RuntimeError:
        pass


def save_txt(data: list, save_path='data.txt', sep='\t', override=False):
    """
    向 txt 文件中追加数据。

    参数：
    - data: 数据列表，每一项也是一个列表
    - save_path: 文件保存的路径，路径包括文件名
    - override: 决定是否覆盖原文件中的内容
    """
    dir, __ = path.split(save_path)
    if dir:
        makedirs(dir, exist_ok=True)
    with open(save_path, "w+" if override else "a+", encoding="utf-8", errors="ignore") as f:
        if data:
            for d in data:
                if d:
                    f.write(sep.join(str(item) for item in d)+'\n')


def save_xlsx(data: list, save_path='data.xlsx', table_name='Sheet', backup=False):
    """
    向 xlsx 文件中追加数据。

    参数：
    - data: 数据列表，每一项也是一个列表
    - save_path: 文件保存的路径，路径包括文件名
    - table_name: 数据保存到 xlsx 的工作表名称
    - backup: 决定写入 xlsx 前是否先将原文件备份
    """
    dir, __ = path.split(save_path)
    if dir:
        makedirs(dir, exist_ok=True)
    cols_data = 0
    try:
        read_xlsx = openpyxl.load_workbook(save_path)
    except Exception:
        read_xlsx = openpyxl.Workbook()
    if backup:
        read_xlsx.save('backup_{}.xlsx'.format(int(time.time())))
    try:
        table = read_xlsx[table_name]
    except Exception:
        read_xlsx.create_sheet(table_name)
        table = read_xlsx[table_name]
    nrows = table.max_row
    if data:
        cols_data = len(data[0])
        for d in data:
            for j in range(0, cols_data):
                table.cell(nrows+1, j+1).value = (ILLEGAL_CHARACTERS_RE.sub(r'',
                                                                            d[j]) if (type(d[j]) == type('a')) else d[j])
            nrows = nrows + 1
        data.clear()
    read_xlsx.save(save_path)
    return data


def save_raw(raw, save_path):
    """
    保存原始数据。

    参数：
    - raw: 原始数据
    - save_path: 文件保存的路径，路径包括文件名
    """
    dir, __ = path.split(save_path)
    if dir:
        makedirs(dir, exist_ok=True)
    with open(save_path, 'wb+') as f:
        f.write(raw)


res = []
cat = {'Action','Adventure','Arcade', 'Board', 'Card', 
'Casino', 'Casual', 'Educational', 'Family', 'Music', 
'Puzzle', 'Racing', 'Role Playing', 'Simulation','Sports', 'Strategy', 'Trivia', 'Word'}
with open(r'C:\Users\rochero\Downloads\Compressed\archive_1\appleAppData.csv', newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        try:
            if reader.line_num == 1:
                res.append(row)
            else:
                if isinstance(row, list) and row[3] =='Games' and row[18] and int(row[18]) >= 30:
                    res.append(row)
        except Exception:
            traceback.print_exc()

with open('some.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(res)
