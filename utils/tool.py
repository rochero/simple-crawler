import gzip
import time
import os
from os import path, makedirs
import pandas as pd
import numpy as np
import time


def time_stamp(timeNum, date_only=True):
    timeStamp = timeNum/1000
    timeArray = time.localtime(timeStamp)
    otherStyleTime = time.strftime('%Y-%m-%d'+ '' if date_only else ' %H:%M:%S', timeArray)
    return otherStyleTime

def load_txt(load_path, first=False, sep='\t'):
    with open(load_path, 'r', encoding='utf-8', errors='ignore') as f:
        return [l.strip().split(sep)[0] if first else l.strip().split(sep) for l in f.readlines()]


def make_dir(save_path = None):
    dir, __ = path.split(save_path)
    if dir:
        makedirs(dir, exist_ok=True)


def save_txt(data: list, save_path='data.txt', sep='\t', override=False):
    if not data: return
    make_dir(save_path)
    with open(save_path, "w+" if override else "a+", encoding="utf-8", errors="ignore") as f:
        f.writelines(sep.join(str(item) for item in d)+'\n' for d in data if any(d))


def save_raw(raw, save_path):
    make_dir(save_path)
    with open(save_path, 'wb+') as f:
        f.write(raw)


def save_csv(data: list, save_path='data.csv', sep=',', override=False, col:list | bool = False):
    make_dir(save_path)
    df = pd.DataFrame(np.array(data))
    df.to_csv(save_path, sep=sep, mode='w' if override else 'a', header = col, index=False)

def save_xlsx(data: list, save_path='data.xlsx', sheet_name='Sheet1', override=False,col:list | bool = False):
    make_dir(save_path)
    df = pd.DataFrame(np.array(data))
    with pd.ExcelWriter(save_path, mode='w' if override or not path.exists(save_path) else 'a', engine='openpyxl') as writer:
        df.to_excel(writer,sheet_name=sheet_name, header = col, index=False)

def un_gz(file_path, delete_source=False):
    f_name = file_path.replace('.gz', '')
    g_file = gzip.GzipFile(file_path)
    open(f_name, "wb+").write(g_file.read())
    g_file.close()
    if delete_source:
        os.remove(file_path)
