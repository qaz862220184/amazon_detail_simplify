# 通用scrapy爬虫框架

## 简介
此项目为scrapy爬虫的通用项目，目前可用于商品详情数据的爬取和下拉词数据的爬取

## 基础环境
在开始之前，请确保你已经安装了以下环境依赖：

- Python3.10
- scrapy
- scrapyd
- redis
- supervisor
- requests
- pysocks

## 项目环境

在安装完基础环境后，需要将此项目上传至服务器并配置

1.新建项目文件夹
```
mkdir -p /data/python/commodity
```
2.进入项目目录并使用git拉取
```
cd /data/python/commodity
git pull
```
3.安装python相关模块
```
# 进入目录
cd /data/python/commodity
# 执行安装
pip install -r requirements.txt
```


## 相关命令
1. 进入爬虫文件夹
`cd commodity`
2. 运行爬虫
`scrapy crawl detail`
3. 命令教程：https://blog.csdn.net/huisoul/article/details/121204936

其他蜘蛛模块标识：

| 标识        | 业务名称    |
|-----------|---------|
| commodity | 商品详情页爬虫 |

## 相关配置

- 蜘蛛配置文件
`project_root_path/scrapy_project/demo/demo/settings.py`

- 项目配置文件
`project_root_path/common/settings.py`

## 爬虫任务管理（包含守护进程）

**打包爬虫项目：**
1. 进入打包目录
`cd demo1`
2. 打包
`scrapyd-deploy 部署名称 -p 项目名称`

**运行爬虫任务管理：**

`scrapyd`

**scrapyd相关教程：**

- 接口调用：https://blog.csdn.net/u010154424/article/details/123694909


## 其他说明
- xpath教程：https://blog.csdn.net/qq_50854790/article/details/123610184

- 蜘蛛配置大全：https://www.jianshu.com/p/5b54bde9f9f3
