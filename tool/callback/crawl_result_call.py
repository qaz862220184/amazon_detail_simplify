import json
import time
import urllib3
import requests
from common.helpers import get_value
from common.settings import CRAWL_RESULT_CALL_CONF
from common.core.mongodb.mongo import MongoDb
from bson.objectid import ObjectId
from common.utils.encryption import ApiSign
from common.exceptions.exception import SystemException


class CrawlResultCall(object):
    # 回调方法名称
    ACTION_SUCCESS = 'success'
    ACTION_ERROR = 'error'
    ACTIONS = {
        ACTION_SUCCESS: '爬取成功回调',
        ACTION_ERROR: '爬取失败回调',
    }

    # 通知状态
    INFORM_STATUS_0 = 0
    INFORM_STATUS_1 = 1
    INFORM_STATUS_2 = 2
    INFORM_STATUS = {
        INFORM_STATUS_0: '未通知',
        INFORM_STATUS_1: '成功通知',
        INFORM_STATUS_2: '通知失败',
    }
    CONFIG = CRAWL_RESULT_CALL_CONF

    @classmethod
    def call(cls, sub_task_id, action, custom=None):
        """
        回调
        :param sub_task_id:
        :param action:
        :param custom:
        :return:
        """
        if custom is None:
            custom = {}
        call = RequestCall(sub_task_id, action, custom)
        call.dispatch().inform()

    @classmethod
    def get_conf(cls):
        """
        获取配置文件
        :return:
        """
        return cls.CONFIG


class RequestCall(object):
    """
    回调请求
    """

    def __init__(self, sub_task_id, action, custom):
        sub_task = MongoDb.table('crontab_sub_task', 'task').find_one({'_id': {'$eq': ObjectId(sub_task_id)}})
        if not sub_task:
            # 任务不存在
            raise SystemException('Sub task does not exist:' + sub_task_id)
        sub_task['_id'] = str(sub_task['_id'])
        self.sub_task = sub_task
        task = MongoDb.table('crontab_task', 'task').find_one({'_id': {'$eq': ObjectId(sub_task['task_id'])}})
        if not task:
            # 主任务不存在
            raise SystemException('The main task does not exist')
        task['_id'] = str(task['_id'])
        self.task = task
        if self.sub_task['inform_status'] in [CrawlResultCall.INFORM_STATUS_1]:
            # 通知状态错误
            raise SystemException('Task notification status error')
        if not self.get_conf_by_key('enable'):
            # 当前通知状态已关闭
            raise SystemException('The current notification status is disabled')
        self.action = action
        self.custom = custom
        self.inform_status = CrawlResultCall.INFORM_STATUS_0
        self.inform_error = ''

    def dispatch(self):
        """
        调度
        :return:
        """
        response = self._post()
        content = response.text
        # json解析
        try:
            res = json.loads(content)
        except Exception as e:
            res = content
        if not isinstance(res, dict):
            # 非json
            self.set_inform_status(CrawlResultCall.INFORM_STATUS_2).set_inform_error(content)
        else:
            # json
            if res['code'] != 2000:
                # 接口发生错误
                self.set_inform_status(CrawlResultCall.INFORM_STATUS_2).set_inform_error(res['msg'])
            else:
                # 成功
                self.set_inform_status(CrawlResultCall.INFORM_STATUS_1)

        return self

    def inform(self):
        """
        通知
        :return:
        """
        # 需要更新的信息
        update_sql = {'inform_status': self.get_inform_status()}
        if self.get_inform_error():
            update_sql['inform_error'] = self.get_inform_error()
        # 保存数据
        return MongoDb.table('crontab_sub_task', 'task').update_one(
            {'_id': {'$eq': ObjectId(self.sub_task['_id'])}},
            {'$set': update_sql}
        )

    def set_inform_status(self, inform_status):
        """
        设置通知状态
        :param inform_status:
        :return:
        """
        self.inform_status = inform_status
        return self

    def set_inform_error(self, inform_error):
        """
        设置通知错误信息
        :param inform_error:
        :return:
        """
        self.inform_error = inform_error
        return self

    def get_inform_status(self):
        """
        获取通知状态
        :return:
        """
        return self.inform_status

    def get_inform_error(self):
        """
        获取通知错误信息
        :return:
        """
        return self.inform_error

    def _post(self):
        """
        post请求
        :return:
        """
        # 参数
        params = {
            'action': self.action,
            'sub_task_id': self.sub_task['_id'],
            'timestamp': time.time(),
            'custom': json.dumps(self.custom),
        }
        params['sign'] = self._create_sign(params)
        urllib3.disable_warnings()
        response = requests.post(
            self.get_conf_by_key('api'),
            params=params,
            headers={'Content-Type': 'application/json'},
            verify=False
        )
        return response

    @classmethod
    def _create_sign(cls, params):
        """
        生成签名
        :param params:
        :return:
        """
        return ApiSign.create_sign(params)

    def get_conf_by_key(self, key=None, default=None):
        """
        获取配置
        :param key:
        :param default:
        :return:
        """
        if 'source' in self.task:
            source = self.task['source']
        else:
            source = 1
        conf = CrawlResultCall.get_conf()
        return get_value(conf[str(source)], key, default)
