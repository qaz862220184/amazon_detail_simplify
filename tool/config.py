from scrapy.utils.project import get_project_settings
from common.core.mongodb.mongo import MongoDb
from common.helpers import get_value
from common.utils.cache import Chcaed
from bson.objectid import ObjectId
from datetime import datetime


class ScrapyConfig:
    """
    只可在scrapy运行时使用，否则无法获取到值
    """
    settings = get_project_settings()

    @classmethod
    def get_settings_value(cls, name, default=None):
        """
        获取配置值
        :param name:
        :param default:
        :return:
        """
        return get_value(result=cls.settings, name=name, default=default)


class Config:

    @classmethod
    def get_country(cls, key=None):
        """
        获取国家数据
        :param key:
        :return:
        """
        data_key = 'country_data_key'
        country = Chcaed.get(data_key)
        if country is None:
            country = {}
            result = MongoDb.table('scrapy_country').find({'status': {'$eq': 1}})
            if result:
                for item in result:
                    for filed in item:
                        if isinstance(item[filed], datetime) or isinstance(item[filed], ObjectId):
                            item[filed] = str(item[filed])
                    country[item['code']] = item
            if country:
                Chcaed.put(data_key, country, 3600)
        if key is not None and country:
            return country[key]
        return country
