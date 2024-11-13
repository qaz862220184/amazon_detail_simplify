
import requests
import time
import socket
import getpass
import json
from common.settings import VPN_LINE_PROXY
from common.utils.encryption import ApiSign
from common.utils.cache import Chcaed
from common.helpers import get_absolute_path
from common.exceptions.exception import ProxyException
from common.env import ENV
from common.core.redisdb.redis_pool import RedisClient
import logging
logger = logging.getLogger()


class LineProxy(object):

    token_key = 'line_token'

    def __init__(self):
        # 检查token是否存在
        if not Chcaed.get(self.token_key):
            self.get_auth_token()
        self.header = {
            'content-type': 'application/json',
            'token': self.get_token()
        }

    def get_all_line(self):
        """
        获取所有的线路
        :return:
        """
        response = requests.post(
            url=VPN_LINE_PROXY.get('get_all_line_api'),
            headers=self.header,
        )
        res = response.json()
        if 'code' in res and res['code'] == 200:
            return res['data']
        return []

    def change_vpn_line(self, business_id=None, country=None, area_type=None, frequency_time=10):
        """
        切换vpn线路
        :return:
        """
        params = {
            'network_business_id': business_id,
            'country': country,
            'area_type': area_type,
            'max_use_time': frequency_time
        }
        response = requests.post(
            url=VPN_LINE_PROXY.get('change_line_api'),
            headers=self.header,
            data=json.dumps(params)
        )
        try:
            res = response.json()
        except:
            raise ProxyException(
                'change vpn line is error!!! response info is {}. params is {}'.format(response.text, params))
        if 'code' in res and res['code'] == 200:
            data = res['data']
            Chcaed.put('network_line_use_id', data.get('uuid'))
            Chcaed.put('network_line_id', data.get('network_line_id'))
            Chcaed.put('v2ray_connect_url', data.get('v2ray_connect_url'))
            return data
        raise ProxyException('change vpn line is error!!! response info is {}'.format(res))

    def close_vpn_line(self, network_line_id, uuid):
        """
        关闭线路
        :param network_line_id:
        :param uuid:
        :return:
        """
        logger.debug('this is network_line_use_id on!!!!!')
        params = {'network_line_id': network_line_id, 'uuid': uuid}
        logger.debug(params)
        # 将任务发送到redis服务器上
        detail = {
            'type': 1,
            'url': VPN_LINE_PROXY.get('close_line_api'),
            'headers': self.header,
            'params': params
        }
        RedisClient.redis('client').lpush('adv_scrapy', json.dumps(detail))
        return True
        # response = requests.post(
        #     url=VPN_LINE_PROXY.get('close_line_api'),
        #     headers=self.header,
        #     data=json.dumps(params)
        # )
        # res = response.json()
        # if 'code' in res and res['code'] == 200:
        #     return True
        # return False

    def get_vpn_resource(self, network_line_id):
        """
        获取所有的vpn资源
        :param network_line_id:
        :return:
        """
        params = {'network_line_id': network_line_id}
        response = requests.post(
            url=VPN_LINE_PROXY.get('get_vpn_api'),
            headers=self.header,
            data=json.dumps(params)
        )
        res = response.json()
        if 'code' in res and res['code'] == 200:
            return res['data']
        return []

    def change_vpn_resource(self, network_line_id, vpn=None, change_type=1):
        """
        切换vpn资源
        :param network_line_id:
        :param vpn:
        :param change_type:
        :return:
        """
        params = {'network_line_id': network_line_id, "type": change_type}
        if vpn is not None:
            params['vpn'] = vpn
        # 将任务发送到redis服务器上
        detail = {
            'type': 4,
            'url': VPN_LINE_PROXY.get('change_vpn_api'),
            'headers': self.header,
            'params': params
        }
        RedisClient.redis('client').lpush('adv_scrapy', json.dumps(detail))
        return 'default'

    def start_up_cleaning(self, startup_time, max_release_time=1):
        """
        节点开机清理
        """
        params = {
            'node_id': ENV.find_env('NODE_ID'),
            'startup_time': startup_time,
            'max_release_time': max_release_time,
        }
        response = requests.post(
            url=VPN_LINE_PROXY.get('startup_cleaning_api'),
            headers=self.header,
            data=json.dumps(params)
        )
        return response

    @classmethod
    def get_auth_token(cls):
        # 获取当前系统主机名
        host_name = socket.gethostname()
        # 获取当前系统用户名
        user_name = getpass.getuser()
        params = {
            "computer_name": host_name,
            "timestamp": int(time.time()),
            "username": user_name
        }
        uuid = ENV.find_env('COMPUTER_UUID')
        if not uuid:
            raise ValueError('COMPUTER_UUID is not in settings file!!!!')
        pc_uuid = uuid
        ApiSign.set_api_key(pc_uuid)
        sign = ApiSign.create_sign(params)
        params['sign'] = sign
        # 请求授权
        headers = {'content-type': 'application/json'}
        response = requests.post(
            url=VPN_LINE_PROXY.get('program_authentication_api'),
            headers=headers,
            data=json.dumps(params),
        )
        res = response.json()
        if 'code' in res and res['code'] == 200:
            token = res['data'].get('token')
            expired = res['data'].get('expired')
            Chcaed.put(cls.token_key, token, expired)
            return True
        raise ValueError('get token by other auth is error! response is {}. params is {}'.format(res, params))

    @classmethod
    def get_token(cls):
        """
        获取token
        :return:
        """
        return Chcaed.get(cls.token_key)

    @classmethod
    def get_network_line_use_id(cls):
        return Chcaed.get('network_line_use_id')

    @classmethod
    def get_network_line_id(cls):
        return Chcaed.get('network_line_id')

    @classmethod
    def get_v2ray_connect_url(cls):
        return Chcaed.get('v2ray_connect_url')


class AuthAccount(object):

    def __init__(self):
        self.file_path = get_absolute_path('common/settings.py')
        self.headers = {'content-type': 'application/json'}

    def register_auth_account(self):
        """
        注册授权账户
        :return:
        """
        # 获取当前系统主机名
        host_name = socket.gethostname()
        # 获取当前系统用户名
        user_name = getpass.getuser()
        params = {
            "computer_name": host_name,
            "timestamp": int(time.time()),
            "username": user_name,
            "remark": "广告巡查节点",
        }
        sign = ApiSign.create_sign(params)
        params['sign'] = sign

        response = requests.post(
            url=VPN_LINE_PROXY.get('register_auth_api'),
            headers=self.headers,
            data=json.dumps(params)
        )
        res = response.json()
        if 'code' in res and res['code'] == 200:
            return res['data']
        raise ValueError('register auth response data is error!!!, response is {}'.format(res))

    def do_auth_account(self):
        """
        授权信息初始化
        :return:
        """
        if not ENV.find_env('COMPUTER_UUID'):
            account_info = self.register_auth_account()
            if not account_info:
                raise ValueError('register auth account is failed')
            ENV.update_env('COMPUTER_UUID', account_info['uuid'])
            return True
        return False


class VpsLineInit(object):
    """
    初始化配置代理信息
    """
    @classmethod
    def line_init(cls, business_id, country):
        """
        线路初始化
        :return:
        """
        if not LineProxy.get_v2ray_connect_url():
            LineProxy().change_vpn_line(business_id=business_id, country=country)


if __name__ == '__main__':
    # result = AuthAccount().do_auth_account()
    # print(result)

    # if not LineProxy.get_v2ray_connect_url():
    #     print('没有线路存在')
    #     LineProxy().change_vpn_line(1, 'FR')

    all_line = LineProxy().get_all_line()

    print(all_line)

    # VpsLineInit.line_init(
    #     business_id=1,
    #     country='US',
    #     base_path='',
    #     config_path='D:\\python_project\\advertising-rankings\\runtime\\v2ray\\config.json',
    #     v2ray_path='D:/v2rayN/wv2ray.exe',
    # )
