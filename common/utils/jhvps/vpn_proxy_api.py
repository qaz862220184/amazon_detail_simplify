# -*- coding: UTF-8 -*-
import requests
import re
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
        """
        params = {
            'network_business_id': business_id,
            'country': country,
            'area_type': area_type,
            'max_use_time': frequency_time,
        }
        response = requests.post(
            url=VPN_LINE_PROXY.get('change_line_api'),
            headers=self.header,
            data=json.dumps(params)
        )
        try:
            res = response.json()
        except:
            raise ProxyException('change vpn line is error!!response info is {}. params is{}'.format(response.text,
                                                                                                     params))
        if 'code' in res and res['code'] == 200:
            data = res['data']
            Chcaed.put('network_line_use_id', data.get('network_line_use_id'))
            Chcaed.put('network_line_id', data.get('network_line_id'))
            Chcaed.put('v2ray_connect_url', data.get('v2ray_connect_url'))
            return data
        raise ProxyException('change vpn line is error!!! response info is {}'.format(res))

    def close_vpn_line(self, network_line_id, uuid):
        """
        关闭线路
        """
        logger.debug('this is network_line_use_id on!!!!!')
        params = {'network_line_id': network_line_id, 'uuid': uuid}
        logger.debug(params)
        response = requests.post(
            url=VPN_LINE_PROXY.get('close_line_api'),
            headers=self.header,
            data=json.dumps(params)
        )
        res = response.json()
        if 'code' in res and res['code'] == 200:
            return True
        return False

    def get_vpn_resource(self, network_line_id):
        """
        获取所有的vpn资源
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
        """
        params = {'network_line_id': network_line_id, 'type': change_type}
        if vpn is not None:
            params['vpn'] = vpn
        response = requests.post(
            url=VPN_LINE_PROXY.get('change_vpn_api'),
            headers=self.header,
            data=json.dumps(params),
        )
        res = response.json()
        if 'code' in res and res['code'] == 200:
            return res['data'].get('vpn') if res['data'] else 'local'
        elif 'code' in res and res['code'] == 602:
            return 'local'
        elif 'code' in res and res['code'] == 201:
            return 'reset'
        raise ValueError('change vpn resource is error!!! response info us {}. params is {}'.format(res, params))

    @classmethod
    def get_auth_token(cls):
        # 获取当前系统主机名
        host_name = socket.gethostname()
        # 获取当前系统用户名
        user_name = getpass.getuser()
        params = {
            'computer_name': host_name,
            'timestamp': int(time.time()),
            'username': user_name,
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
            data=json.dumps(params)
        )
        res = response.json()
        if 'code' in res and res['code'] == 200:
            token = res['data'].get('token')
            expired = res['data'].get('expired')
            Chcaed.put(cls.token_key, token, expired)
            return True
        raise ValueError('get token by other auth is error! response is {}, params is {}'.format(res, params))

    @classmethod
    def get_token(cls):
        """
        获取token
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
        注册授权账号
        """
        # 获取当前系统主机名
        host_name = socket.gethostname()
        # 获取当前系统用户名
        user_name = getpass.getuser()
        params = {
            'computer_name': host_name,
            'timestamp': int(time.time()),
            'username': user_name,
            'remark': '商品详情授权账号',
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
        raise ValueError('register auth response data is error!!! response is {}'.format(res))

    def do_auth_account(self):
        """
        授权信息初始化
        """
        # 判断配置文件里是否存在uuid
        if not ENV.find_env('COMPUTER_UUID'):
            account_info = self.register_auth_account()
            if not account_info:
                raise ValueError('register auth account is failed')
            ENV.update_env('COMPUTER_UUID', account_info['uuid'])
            return True
        return False


class VpsLineInit(object):
    """
    初始化配置信息
    """
    @classmethod
    def line_init(cls, business_id, country):
        """
        初始化线路
        """
        if not LineProxy.get_v2ray_connect_url():
            LineProxy().change_vpn_line(business_id=business_id, country=country)
