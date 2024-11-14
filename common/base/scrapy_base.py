import json
import time
from abc import ABC
from scrapy import Spider, signals, Request
from common.helpers import get_value, get_dynamic_class
from common.utils.encryption import Base64Encrytion, ApiSign
from common.core.mongodb.mongo import MongoDb
from bson.objectid import ObjectId
from urllib.parse import urlencode
from common.exceptions.exception import SystemException
from common.utils.date_time import ScrapyDateTimeManage
from tool.callback.crawl_result_call import CrawlResultCall
from common.exceptions.handler import ExceptionHandler
from tool.config import Config
from datetime import datetime
# 新方法
from tool.request.proxys.vps_proxies import VpsProxiesTactic
from gerapy_pyppeteer import PyppeteerRequest


class SpiderBase(Spider, ABC):
    # 运行状态
    EXECUTE_STATUS_RUNNING = 'running'
    EXECUTE_STATUS_ERROR = 'error'
    EXECUTE_STATUS_SUCCESS = 'success'
    # 当前状态
    execute_status = EXECUTE_STATUS_RUNNING
    # 请求参数
    request_params = {}
    # 异常对象列表
    exceptions = []

    def __init__(self, params=None, *args, **kwargs):
        """
        初始化
        :param params:
        :param args:
        :param kwargs:
        """
        super(SpiderBase, self).__init__(*args, **kwargs)
        # 参数解析和验签
        if params:
            params = Base64Encrytion.decode(params)
            self.params = json.loads(params)
        else:
            raise SystemException('Parameter parsing error')
        if ApiSign.ver_sign(self.params) is False:
            raise SystemException('Signature verification fails')
        # 获取子任务和主任务
        sub_task_id = self.get_params('sub_task_id')
        if not sub_task_id:
            # 参数错误
            raise ValueError('sub_task_id cannot be empty')
        sub_task = MongoDb.table('crontab_sub_task', 'task').find_one({'_id': {'$eq': ObjectId(sub_task_id)}})
        if not sub_task:
            # 任务不存在
            raise ValueError('The sub task does not exist')
        if sub_task['status'] not in [0, 2]:
            # 任务状态错误
            raise ValueError('Sub task status error')
        # 主任务
        scrapy_task = MongoDb.table('crontab_task', 'task').find_one(
            {'_id': {'$eq': ObjectId(sub_task['task_id'])}})
        if not scrapy_task:
            # 主任务不存在
            raise ValueError('The task does not exist')

        # 线路数据
        self.network_line_id = None
        self.uuid = None

        # 子任务赋值
        self.subtask = sub_task
        self.subtask['start_time'] = time.time()  # 爬虫开始执行时间
        self.sub_task_id = str(self.get_subtask('_id'))
        self.subtask_handle_data = self.get_subtask('handle_data')

        # 主任务
        self.task = scrapy_task
        self.task_id = str(self.get_task('_id'))

    def get_task(self, name=None, default=None):
        """
        获取主任务数据
        :param name:
        :param default:
        :return:
        """
        return get_value(self.task, name, default)

    def get_subtask(self, name=None, default=None):
        """
        获取子任务数据
        :param name:
        :param default:
        :return:
        """
        return get_value(self.subtask, name, default)

    def get_params(self, name=None, default=None):
        """
        获取参数
        :param name:
        :param default:
        :return:
        """
        return get_value(self.params, name, default)

    def set_request_param(self, name, param):
        """
        设置请求参数
        :param name:
        :param param:
        :return:
        """
        self.request_params[name] = param
        return self

    def get_request_param(self, name=None, default=None):
        """
        获取请求参数的值
        :param name:
        :param default:
        :return:
        """
        return get_value(
            self.request_params,
            name=name,
            default=default
        )

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """
        document：https://www.osgeo.cn/scrapy/topics/signals.html?highlight=%E4%BF%A1%E5%8F%B7#topics-signals-ref
        信号回调处理
        :param crawler:
        :param args:
        :param kwargs:
        :return:
        """
        # 获取当前蜘蛛
        spider = super(SpiderBase, cls).from_crawler(crawler, *args, **kwargs)
        # 设置回调
        crawler.signals.connect(spider.started, signal=signals.engine_started)
        crawler.signals.connect(spider.stopped, signal=signals.engine_stopped)

        return spider

    def started(self):
        """
        蜘蛛引擎启动
        :return:
        """
        MongoDb.table('crontab_sub_task', 'task').update_one(
            {'_id': {'$eq': ObjectId(self.sub_task_id)}},
            {'$set': {'status': 2, 'start_time': self.get_subtask('start_time'),
                      'updated_at': self.__get_uct_time()}}
        )

    def stopped(self):
        """
        蜘蛛引擎结束
        :return:
        """
        # 解除线路占用
        if self.uuid:
            VpsProxiesTactic.close_line(self.network_line_id, self.uuid)
        if self.is_success():
            # 爬虫执行成功
            self.execute_success_call()
        else:
            if not self.exceptions:
                # 发生未知错误
                try:
                    raise SystemException('An unknown error occurred')
                except Exception as ex:
                    exception = ex
            else:
                exception = self.exceptions[-1]
            # 回调自定义方法
            self.execute_error_call(exception)

    def execute_success_call(self):
        """
        爬虫执行成功回调
        :return:
        """
        end_time = time.time()
        execution_time = round((end_time - self.get_subtask('start_time')), 2)
        MongoDb.table('crontab_sub_task', 'task').update_one(
            {'_id': {'$eq': ObjectId(self.sub_task_id)}},
            {'$set': {'status': 1, 'end_time': end_time, 'execution_time': execution_time,
                      'updated_at': self.__get_uct_time(), 'network_line_id': self.network_line_id}}
        )
        # 成功回调
        CrawlResultCall.call(
            sub_task_id=self.sub_task_id,
            action=CrawlResultCall.ACTION_SUCCESS
        )

    def execute_error_call(self, exception):
        """
        爬虫执行失败回调
        :param exception:
        :return:
        """
        last_trace = ExceptionHandler.get_last_exception_stack(exception)
        error = {}
        if last_trace:
            error = {
                'msg': str(exception),
                'file-line': last_trace['filename'],
                'lineno': last_trace['lineno'],
            }
        # 填充其他数据
        request_param = self.get_request_param()
        for name in self.get_request_param():
            error[name] = request_param[name]
        # 时间计算
        end_time = time.time()
        execution_time = round((end_time - self.get_subtask('start_time')), 2)
        MongoDb.table('crontab_sub_task', 'task') \
            .update_one(
            {'_id': {'$eq': ObjectId(self.sub_task_id)}},
            {'$set': {'status': 3, 'end_time': end_time, 'execution_time': execution_time,
                      'updated_at': self.__get_uct_time(), 'error': error, 'network_line_id': self.network_line_id}}
        )
        # 失败回调
        CrawlResultCall.call(
            sub_task_id=self.sub_task_id,
            action=CrawlResultCall.ACTION_ERROR
        )

    def set_execute_status(self, status):
        """
        设置爬虫运行状态
        :param status:
        :return:
        """
        self.execute_status = status
        return self

    def get_execute_status(self):
        """
        获取爬虫运行状态
        :return:
        """
        return self.execute_status

    def is_success(self):
        """
        爬取是否成功
        :return:
        """
        return self.get_execute_status() == self.EXECUTE_STATUS_SUCCESS

    def add_exception(self, exception, type=None, param=None):
        """
        添加异常
        :param exception:
        :param type:
        :param param:
        :return:
        """
        # 设置爬虫状态为错误
        self.set_execute_status(
            status=self.EXECUTE_STATUS_ERROR
        )
        if isinstance(exception, Exception):
            self.exceptions.append(exception)
        else:
            if not type:
                type = 'system'
            class_str = f"common.exceptions.exception.{type.capitalize()}Exception"
            class_obj = get_dynamic_class(class_str)
            if class_obj:
                try:
                    param = {} if not param else param
                    raise class_obj(exception, param)
                except Exception as ex:
                    self.exceptions.append(ex)
        return self

    def errback(self, failure):
        """
        错误回调【处理所有的错误】
        """
        # 日志记录
        self.logger.error(failure)
        try:
            failure.raiseException()
        except Exception as exception:
            self.add_exception(exception)

    def http_get(self, url, params, **options):
        """
        get请求
        :param url:
        :param params:
        :param options:
        :return:
        """
        # 请求地址解析
        if not url or '://' not in url:
            # 抛出异常
            raise ValueError('The request url format is incorrect')
        # 请求参数解析
        if params:
            url = f'{url}?{urlencode(params)}'
        # 请求方式
        options['method'] = 'GET'
        if 'errback' not in options:
            options['errback'] = self.errback
        return PyppeteerRequest(url, **options)

    def form_request(self, url, params, **options):
        """
        form表单
        :param url:
        :param params:
        :param options:
        :return:
        """
        if not url or '://' not in url:
            # 抛出异常
            raise ValueError('The request url format is incorrect')
        # 请求参数解析
        if params:
            url = f'{url}?{urlencode(params)}'
        if 'errback' not in options:
            options['errback'] = self.errback
        return Request(url, **options)

    @classmethod
    def __get_uct_time(cls):
        res = ScrapyDateTimeManage.date_time().date_time()
        return datetime.strptime(res, "%Y-%m-%d %H:%M:%S")


class CommoditySpiderBase(SpiderBase, ABC):

    def __init__(self, params=None, *args, **kwargs):
        # 调用父类
        super().__init__(params, * args, ** kwargs)
        # 国家参数初始化
        handle_data = self.get_subtask("handle_data")
        country_code = handle_data.get("country_code")
        country = Config.get_country(country_code)
        if not country:
            raise ValueError("The Country code does not exist")
        self.country = country

    def get_country(self, name=None, default=None):
        """
        获取国家参数
        """
        return get_value(
            result=self.country,
            name=name,
            default=default
        )

    def get_country_site(self):
        """
        获取国家域名
        """
        return self.get_country(
            name='domain',
            default='www.amazon.com'
        )

    def get_zip_code(self):
        """
        获取邮编
        """
        handle_data = self.get_subtask("handle_data")
        zip_code = handle_data.get("zip_code")
        return zip_code

    def get_language(self):
        """
        获取语言
        """
        return self.get_country(
            name='language',
            default=''
        )


class DropdownSpiderBase(SpiderBase, ABC):

    def __init__(self, params=None, *args, **kwargs):
        # 调用父类
        super().__init__(params, * args, ** kwargs)
        # 国家参数初始化
        handle_data = self.get_subtask("handle_data")
        country_code = handle_data.get("country_code")
        country = Config.get_country(country_code)
        if not country:
            raise ValueError("The Country code does not exist")
        self.country = country

    def get_country(self, name=None, default=None):
        """
        获取国家参数
        """
        return get_value(
            result=self.country,
            name=name,
            default=default
        )

    def get_country_site(self):
        """
        获取国家域名
        """
        return self.get_country(
            name='domain',
            default='www.amazon.com'
        )

    def get_zip_code(self):
        """
        获取邮编
        """
        handle_data = self.get_subtask("handle_data")
        zip_code = handle_data.get("zip_code")
        return zip_code


if __name__ == '__main__':
    params = {"sub_task_id": "67346b64d8b3a5dd950bd006", "task_id": "67346b64d8b3a5dd950bd005", "time": 1704904975.7675}
    sign = ApiSign.create_sign(params)
    params = dict(params, **{"sign": sign})

    params = json.dumps(params)
    params = Base64Encrytion.encode(params)
    print(params)
