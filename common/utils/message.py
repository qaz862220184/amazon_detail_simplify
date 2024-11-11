import requests
import json
from common.utils.encryption import Md5Encrytion
from common.settings import MESSAGE_CONF


class Client:
    """
    Rocket消息对接
    url:http://192.168.2.23:808/web/#/34?page_id=160
    """

    def __init__(self, url, apikey):
        """
        初始化
        :param url:
        :param apikey:
        """
        self.uri = url
        self.apikey = apikey

    def get_rocket_sender(self, source='1'):
        """
        获取发送者
        :param str source:
        :return:
        """
        params = {'source': source, 'algo': 'MD5'}
        return self.get('rocket/getRocketSender', params)

    def get_rocket_user_group(self, source='1', name=None):
        """
        获取用户分组
        :param str source:
        :param str name:
        :return:
        """
        params = {'source': source, 'algo': 'MD5'}
        if name is not None:
            params['name'] = name
        return self.get('rocket/getRocketUserGroup', params)

    def get_rocket_user_group_rule(self, rocket_user_group_id, source='1', pageNum='1', pageLimit='10'):
        """
        获取用户分组规则接口【分组用户】
        :param str rocket_user_group_id:
        :param str source:
        :param str pageNum:
        :param str pageLimit:
        :return:
        """
        params = {'rocket_user_group_id': rocket_user_group_id, 'source': source, 'algo': 'MD5', 'pageNum': pageNum,
                  'pageLimit': pageLimit}
        return self.get('rocket/getRocketUserGroupRule', params)

    def send_message_by_group_id(self, rocket_user_group_id, content, rocket_sender_id='0', source='1', remark=''):
        """
        使用分组发送消息
        :param rocket_user_group_id:
        :param content:
        :param rocket_sender_id:
        :param source:
        :param remark:
        :return:
        """
        params = {'rocket_user_group_id': rocket_user_group_id, 'content': content,
                  'rocket_sender_id': rocket_sender_id, 'source': source, 'algo': 'MD5'}
        if remark != '':
            params['remark'] = remark
        return self.post('rocket/sendMessageByGroupId', params)

    def send_message_by_uid(self, uids, content, rocket_sender_id='0', source='1', remark=''):
        """
        使用用户id发送消息
        :param uids:
        :param content:
        :param rocket_sender_id:
        :param source:
        :param remark:
        :return:
        """
        params = {'uids': uids, 'content': content, 'rocket_sender_id': rocket_sender_id, 'source': source,
                  'algo': 'MD5'}
        if remark != '':
            params['remark'] = remark
        return self.post('rocket/sendMessageByUid', params)

    def get(self, path, params):
        """
        get请求
        :param path:
        :param params:
        :return:
        """
        params['sign'] = self.__create_sign(params)
        response = requests.get(self.__get_api_url(path), params=params, headers={'content-type': 'application/json'})
        return self.__return_response(response)

    def post(self, path, params):
        """
        post请求
        :param path:
        :param params:
        :return:
        """
        params['sign'] = self.__create_sign(params)
        response = requests.post(self.__get_api_url(path), params=params, headers={'content-type': 'application/json'})
        return self.__return_response(response)

    @classmethod
    def __return_response(cls, response):
        """
        返回结果
        :param response:
        :return:
        """
        try:
            res = response.json()
        except Exception as e:
            res = response.text
        return res

    def __get_api_url(self, path):
        """
        返回请求路径
        :param path:
        :return:
        """
        if not path.startswith('/'):
            path = '/' + path
        return self.uri + path

    def __create_sign(self, params):
        """
        创建签名
        :param params:
        :return:
        """
        arr = sorted(params.items(), key=lambda params: params[0])
        dicts = {}
        for tup in arr:
            if tup[0] is 'content':
                continue
            else:
                val = tup[1]
            dicts[tup[0]] = val
        json_data = json.dumps(dicts, separators=(',', ':'), ensure_ascii=False)
        return Md5Encrytion.md5_lower32(json_data + self.apikey)


class RocketMessage:
    # uri = 'http://192.168.2.17:9501/api/v1'
    # apikey = 'hEI/qDhna7kL400WgZ91vDCPsbCPWCLLDwvxNrClmQg='

    client = Client(MESSAGE_CONF['api'], MESSAGE_CONF['apikey'])
    default_send_type = MESSAGE_CONF['default_send_type']
    default_group_id = MESSAGE_CONF['default_group_id']
    default_user_id = MESSAGE_CONF['default_user_id']
    default_source = MESSAGE_CONF['default_source']
    default_sender_id = MESSAGE_CONF['default_sender_id']

    @classmethod
    def send(cls, content, ids=None, rocket_sender_id=None, source=None, remark=''):
        """
        发送
        :param content:
        :param ids:
        :param rocket_sender_id:
        :param source:
        :param remark:
        :return:
        """
        if cls.default_send_type is 'user':
            return cls.send_by_user(content=content, uids=ids, rocket_sender_id=rocket_sender_id, source=source,
                                    remark=remark)
        else:
            return cls.send_by_group(content=content, gids=ids, rocket_sender_id=rocket_sender_id, source=source,
                                     remark=remark)

    @classmethod
    def send_by_user(cls, content, uids=None, rocket_sender_id=None, source=None, remark=''):
        """
        指定用户发送消息
        :param content:
        :param uids:
        :param rocket_sender_id:
        :param source:
        :param remark:
        :return:
        """
        if uids is None:
            uids = cls.default_user_id
        if rocket_sender_id is None:
            rocket_sender_id = cls.default_sender_id
        if source is None:
            source = cls.default_source
        return cls.client.send_message_by_uid(uids=uids, content=content, rocket_sender_id=rocket_sender_id,
                                              source=source,
                                              remark=remark)

    @classmethod
    def send_by_group(cls, content, gids=None, rocket_sender_id=None, source=None, remark=''):
        """
        指定分组发消息
        :param content:
        :param gids:
        :param rocket_sender_id:
        :param source:
        :param remark:
        :return:
        """
        if gids is None:
            gids = cls.default_group_id
        if rocket_sender_id is None:
            rocket_sender_id = cls.default_sender_id
        if source is None:
            source = cls.default_source
        return cls.client.send_message_by_group_id(rocket_user_group_id=gids, content=content,
                                                   rocket_sender_id=rocket_sender_id, source=source, remark=remark)
