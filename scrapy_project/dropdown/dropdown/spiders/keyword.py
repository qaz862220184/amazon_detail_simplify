# -*- coding: utf-8 -*-
import sys
sys.path.append("..")
sys.path.append("../..")
from ..items import DropdownItem
from common.base.scrapy_base import DropdownSpiderBase
from tool.config import Config
from common.helpers import get_value
import json


class KeywordSpider(DropdownSpiderBase):
    name = 'keyword'

    def __init__(self, params=None, *args, **kwargs):
        # 调用父类
        # params = 'eyJzdWJfdGFza19pZCI6ICI2NGEzN2E2NTg3NTMwYjBiOTFjMWQzNmMiLCAidGFza19pZCI6ICI2NGEzN2E2NTg3NTMwYjBiOTFjMWQzNmIiLCAidGltZSI6IDE2ODg0MzUzMDEsICJzaWduIjogImJhYzgwOTJmOWYwMWE0MDg3ZWJmMWUxYzI0OGYxZGI5In0='
        # 没有数据的
        # params = 'eyJzdWJfdGFza19pZCI6ICI2NGEzOGE5MTgwNWQ4NjViMDY1NGI3YmUiLCAidGFza19pZCI6ICI2NGEzOGE5MTgwNWQ4NjViMDY1NGI3YmQiLCAidGltZSI6IDE2ODg0MzUzMDEsICJzaWduIjogIjc1M2VkZThlZjA0ZjE1NmQzODAxMjM5MmE4MjNiN2Q2In0='
        super(KeywordSpider, self).__init__(params, *args, **kwargs)

        handle_data = self.subtask_handle_data
        # 国家参数初始化
        country_code = handle_data.get('country_code')
        country = Config.get_country(country_code)
        if not country:
            raise ValueError('The Country code does not exist')
        self.country = country
        # 请求参数
        self.page = 11
        self.prefix = handle_data.get('keyword')
        if not self.prefix:
            raise ValueError('The Prefix does not exist')

    def start_requests(self):
        """
        请求参数设置
        :return:
        """
        yield self.form_request(
            url=self.get_request_url(),
            params={
                'limit': self.page,
                'prefix': self.prefix,
                'suggestion-type': 'WIDGET',
                'page-type': 'Gateway',
                'alias': 'aps',
                'site-variant': 'desktop',
                'version': '3',
                'event': 'onKeyPress',
                # US:1、JP:6、CA:7、FR:5、DE:4、GB:3
                'plain-mid': self.country['plain_mid'],
                'client-info': 'amazon-search-ui',
            },
            headers={'Content-Type': 'application/json'},
        )

    def parse(self, response, **kwargs):
        """
        参数解析
        :param response:
        :return:
        """
        res = json.loads(response.text)
        sort = 0
        result = []
        exists = []
        for val in res['suggestions']:
            if val['value'] in exists:
                # 去重
                continue
            sort += 1
            item = {}
            item['sort'] = sort
            item['suggType'] = val['suggType']
            item['type'] = val['type']
            item['value'] = val['value']
            item['refTag'] = get_value(val, 'refTag')
            item['candidateSources'] = get_value(val, 'candidateSources')
            item['strategyId'] = get_value(val, 'strategyId')
            item['prior'] = get_value(val, 'prior')
            item['ghost'] = get_value(val, 'ghost')
            item['help'] = get_value(val, 'help')
            item['spellCorrected'] = get_value(val, 'spellCorrected')
            item['fallback'] = get_value(val, 'fallback')
            item['blackListed'] = get_value(val, 'blackListed')
            item['xcatOnly'] = get_value(val, 'xcatOnly')
            result.append(item)
            exists.append(val['value'])
        # 赋值
        keyword_item = DropdownItem()
        keyword_item['result'] = result
        yield keyword_item

    def get_request_url(self):
        """
        获取请求url
        :return:
        """
        if 'associated_domain' not in self.country:
            raise ValueError('The Associated domain does not exist')
        return f"https://{self.country['associated_domain']}/api/2017/suggestions"

    def get_country_site(self):
        """
        获取主域名
        :return:
        """
        if 'domain' in self.country:
            return self.country['domain']
        else:
            return 'www.amazon.com'

    # def execute_success_call(self):
    #     pass
    #
    # def execute_error_call(self, exception):
    #     pass
