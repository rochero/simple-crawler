# simple-crawler

Simple crawler templates written by Python.

简单的爬虫 Python 模板。

## 依赖

- http 请求发起与响应内容解析：requests_html
- 控制台进度条：tqdm
- Excel文件处理：openpyxl
- 出错信息语音播报：pyttsx3
- 浏览器模拟：msedge.selenium_tools（配合浏览器的 driver）

## 版本

template 目录下：
- _example.py 是主要模板，基于 requests_html；
- _selenium.py 是备用策略，基于 selenium 模拟浏览器发起请求。

example 目录下有部分之前写过的示例。
