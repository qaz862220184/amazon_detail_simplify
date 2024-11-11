
from common.settings import DB_REDIS_CONF
import redis


class RedisDb:
    """
    redis连接池
    """
    def __init__(self):
        # redis连接池
        self.pool = redis.ConnectionPool(
            host=DB_REDIS_CONF['host'],
            port=DB_REDIS_CONF['port'],
            db=DB_REDIS_CONF['db'],
            max_connections=DB_REDIS_CONF['max_connections'],
            ** DB_REDIS_CONF['connection_kwargs'],
        )

    def get_redis(self):
        """
        获取redis客户端
        :return:
        """
        return redis.Redis(connection_pool=self.pool)


class RedisClient:
    """
    redis客户端
    """
    RedisPool = RedisDb()

    @classmethod
    def redis(cls):
        return cls.RedisPool.get_redis()

    def __call__(self, *args, **kwargs):
        """
        对象当方法用时触发
        :param args:
        :param kwargs:
        :return:
        """
        return RedisClient.redis()
