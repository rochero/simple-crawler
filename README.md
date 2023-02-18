# simple-crawler

Simple crawler templates written by Python.

简单的 Python 爬虫脚本模板，有如下特性：

- 支持多线程请求；
- 支持浏览器模拟请求；
- 支持在终端显示进度条；
- 自动记录爬取失败的 URL 和错误信息；
- 可将数据保存到 Excel 或 csv 文件；
- 排名脚本 `rank.py`会根据数据的平均评分和评分数量使用基于用户投票的排名算法自动并且快速地对数据进行排序处理。

## 依赖

见 `requirements.txt`。

## 版本

template 目录下：

- __example.py 是主要模板，基于 requests_；
- _selenium.py 是备用策略，基于 selenium 模拟浏览器发起请求。
