import json
import requests
import math
from common.helpers import get_value
from urllib.parse import urlencode
from common.utils.cache import Chcaed
from common.utils.sundry_utils import File
from common.exceptions.exception import RequestException
from common.settings import REMOTE_FILE
from common.utils.encryption import Md5Encrytion
from requests_toolbelt.multipart.encoder import MultipartEncoder


class KodBoxBase:
    # https://blog.51cto.com/u_15057832/4400634
    # https://doc.kodcloud.com/v2/#/explorer/file?id=_15-%e6%96%87%e4%bb%b6%e4%b8%8a%e4%bc%a0
    @classmethod
    def http_get(cls, uri, headers=None, **params):
        """
        get请求
        :param headers:
        :param uri:
        :param params:
        :return:
        """
        request_url = cls.get_request_url(uri)
        # 参数
        if params:
            param = urlencode(params)
            request_url = request_url + '&' + param
        response = requests.get(
            url=request_url,
            headers=headers,
        )
        return cls.__return_response(response)

    @classmethod
    def http_post(
            cls,
            uri,
            headers=None,
            files=None,
            data=None,
            **payload
    ):
        """
        post请求
        :param data:
        :param uri:
        :param headers:
        :param files:
        :param payload:
        :return:
        """
        request_url = cls.get_request_url(uri)
        if not data:
            data = {}
        if payload:
            data = {**data, **payload}
        response = requests.post(
            url=request_url,
            headers=headers,
            files=files,
            data=data
        )
        return cls.__return_response(response)

    @classmethod
    def __return_response(cls, response):
        """
        返回响应信息
        :param response:
        :return:
        """
        if response.status_code != 200:
            raise RequestException(f'Server error {response.status_code}')
        return response.json()

    @classmethod
    def get_request_url(cls, uri):
        """
        获取请求url
        :param uri:
        :return:
        """
        api = cls.get_conf('api')
        if str(api).endswith('/') is False:
            api = api + '/'
        return api + '?' + uri

    @classmethod
    def get_conf(cls, name=None, default=None):
        config = REMOTE_FILE
        return get_value(
            result=config,
            name=name,
            default=default
        )


class KodBoxAuth(KodBoxBase):
    cache_pre = 'scrapy_kodbox_user_'
    cache_ttl = (3600 * 2)

    @classmethod
    def get_access_token(cls, username, password):
        if not username:
            username = cls.get_conf('username')
        if not password:
            password = cls.get_conf('password')
        cache_key = cls.__get_cache_key(
            key=username + password
        )
        res = Chcaed.get(cache_key)
        if not res:
            # 获取用户
            res = cls.auth(
                username=username,
                password=password
            )
            Chcaed.put(
                key=cache_key,
                value=res,
                ex=cls.cache_ttl
            )
        return res

    @classmethod
    def auth(cls, username, password):
        res = cls.http_get(
            uri='user/index/loginSubmit',
            name=username,
            password=password,
        )
        error = None
        if not res['code']:
            error = res['data']
        if error:
            raise RequestException(error)
        return res

    @classmethod
    def __get_cache_key(cls, key):
        return cls.cache_pre + key


class FileManage(KodBoxBase):

    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

    def create_share(
            self,
            source,
            password=None,
            title=None,
            time_to=0
    ):
        """
        创建分享
        :param time_to:
        :param source:
        :param password:
        :param title:
        :return:
        """
        res = self.user_share_get(source=source)
        data = res['data']
        if not data and not isinstance(data, dict):
            res2 = self.user_share_add(source=source)
            data2 = res2['data']
            # 请求编辑分享
            if not title:
                title = data2['title']
            res = self.user_share_edit(
                shareID=data2['shareID'],
                title=title,
                password=password,
                timeTo=time_to
            )
            data = res['data']
        if data:
            # 存在数据
            api = self.get_conf('api')
            return f"{api}/#s/{data['shareHash']}"
        else:
            # 分享失败
            return None

    def file_upload(self, source, filepath):
        """
        文件上传
        :param filepath:
        :param source:
        :return:
        """
        fileinfo = File(filepath)
        files = [fileinfo.create_upload_file()]
        path = self.__get_source(source)
        res = self.http_post(
            uri='explorer/upload/fileUpload',
            path=path,
            accessToken=self.__get_access_token(),
            files=files
        )
        return res

    def file_upload_by_chunk(self, source, filepath, chunk_size=5242880):
        """
        文件分片上传 -- 暂不支持断点重传
        :param chunk_size:
        :param filepath:
        :param source:
        :return:
        """
        file_obj = File(filepath)
        total_size = file_obj.get_size()
        total_chunk = math.ceil(total_size / chunk_size)
        # 上传的路径
        path = self.__get_source(source)
        access_token = self.__get_access_token()
        # 生成文件hash
        check_hash_simple = Md5Encrytion.md5_lower32(filepath)
        current_chunk = 0
        res = None
        while current_chunk < total_chunk:
            # 按分块读文件内容
            start = (current_chunk * chunk_size)
            end = min(total_size, start + chunk_size)
            with open(filepath, 'rb') as f:
                f.seek(start)
                file_chunk_data = f.read(end - start)
            # 生成二进制文件流
            data = MultipartEncoder(
                fields={
                    'name': file_obj.get_base_name(),
                    'size': str(total_size),
                    'chunkSize': str(chunk_size),
                    'chunk': str(current_chunk),
                    'chunks': str(total_chunk),
                    'path': path,
                    'checkHashSimple': check_hash_simple,
                    'accessToken': access_token,
                    'file': (file_obj.get_base_name(), file_chunk_data, file_obj.get_mime_types()),
                }
            )
            # 上传
            res = self.http_post(
                uri='explorer/upload/fileUpload',
                data=data,
                headers={'Content-Type': data.content_type}
            )
            # 块递增
            current_chunk = current_chunk + 1

        return res

    def user_share_edit(
            self,
            shareID,
            title,
            password=None,
            timeTo=0,
            isLink=1,
            options=None,
    ):
        """
        分享编辑
        :param shareID:
        :param title:
        :param password:
        :param timeTo:
        :param isLink:
        :param options:
        :return:
        """
        if options is None:
            options = self.__get_json({'onlyLogin': 0})
        res = self.http_post(
            uri='explorer/userShare/edit',
            shareID=shareID,
            isLink=isLink,
            title=title,
            password=password,
            options=options,
            timeTo=timeTo,
            accessToken=self.__get_access_token()
        )
        return res

    def user_share_add(self, source):
        """

        :param source:
        :return:
        """
        path = self.__get_source(source)
        res = self.http_post(
            uri='explorer/userShare/add',
            path=path,
            accessToken=self.__get_access_token()
        )
        return res

    def user_share_get(self, source):
        """

        :param source:
        :return:
        """
        path = self.__get_source(source)
        res = self.http_post(
            uri='explorer/userShare/get',
            path=path,
            accessToken=self.__get_access_token()
        )
        return res

    @classmethod
    def __get_source(cls, source):
        """
        获取路径
        :param source:
        :return:
        """
        return "{source:" + str(source) + "}"

    @classmethod
    def __get_json(cls, dicts):
        """
        获取路径
        :param dicts:
        :return:
        """
        return json.dumps(dicts)

    def __get_access_token(self):
        """
        获取token
        :return:
        """
        user = KodBoxAuth.get_access_token(
            username=self.username,
            password=self.password
        )
        return user['info']
