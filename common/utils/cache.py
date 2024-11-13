from common.settings import CACHE_CONF
from common.core.redisdb.redis_pool import RedisClient
from common.utils.encryption import Md5Encrytion
import json


class Chcaed:
    driver = CACHE_CONF['driver']
    prefix = CACHE_CONF['prefix']

    @classmethod
    def put(cls, key, value, ex=0, db='default'):
        """
        缓存写入
        :param key:
        :param value:
        :param ex:
        :param db:
        :return:
        """
        if ex > 0:
            return cls.get_driver(db).set(cls.get_cache_key(key), json.dumps(value), ex)
        else:
            return cls.get_driver(db).set(cls.get_cache_key(key), json.dumps(value))

    @classmethod
    def get(cls, key, db='default'):
        """
        获取缓存
        :param key:
        :param db:
        :return:
        """
        res = cls.get_driver(db).get(cls.get_cache_key(key))
        if res:
            return json.loads(res)
        return None

    @classmethod
    def delete(cls, key, db='default'):
        """
        删除
        :param key:
        :param db:
        :return:
        """
        return cls.get_driver(db).delete(cls.get_cache_key(key))

    @classmethod
    def clear(cls, db='default'):
        """
        清空所有缓存
        :return:
        """
        keys = cls.get_driver(db).keys(cls.prefix + '*')
        return cls.get_driver(db).delete(*keys)

    @classmethod
    def get_cache_key(cls, key):
        """
        获取缓存key
        :param key:
        :return:
        """
        if isinstance(key, str) is False and isinstance(key, bytes) is False:
            key = cls.create_key_by_params(key)
        return "_".join([cls.prefix, key])

    @classmethod
    def get_driver(cls, db='default'):
        """
        获取缓存扩展  ## 等效于table方法
        :return:
        """
        if cls.driver == 'redis':
            return RedisClient.redis(db)

    @classmethod
    def create_key_by_params(cls, params, pre=''):
        """
        根据参数生成一个缓存key
        :param pre:
        :param params:
        :return:
        """
        res = {}
        for key in params:
            if isinstance(params[key], str):
                res[key] = params[key]
        json_str = json.dumps(res)
        return pre + Md5Encrytion.md5_lower32(json_str)
