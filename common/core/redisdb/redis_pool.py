
from common.settings import DB_REDIS_CONF
import redis


class RedisDb:
    """
    redis连接池
    """
    db = 'default'

    @classmethod
    def set_db(cls, db):
        if db:
            cls.db = db
        else:
            cls.db = 'default'

    @classmethod
    def get_redis_pool(cls):
        # redis连接池
        redis_conf = DB_REDIS_CONF[cls.db]
        if not redis_conf:
            raise ValueError('redis config is not exist!')
        pool = redis.ConnectionPool(
            host=redis_conf['host'],
            port=redis_conf['port'],
            db=redis_conf['db'],
            password=redis_conf['password'],
            max_connections=redis_conf['max_connections'],
            ** redis_conf['connection_kwargs'],
        )
        return pool

    def get_redis(self, db):
        """
        获取redis客户端
        :return:
        """
        self.set_db(db)
        return redis.Redis(connection_pool=self.get_redis_pool())


class RedisClient:
    """
    redis客户端
    """
    RedisPool = RedisDb()

    @classmethod
    def redis(cls, db=None):
        return cls.RedisPool.get_redis(db)

    def __call__(self, *args, **kwargs):
        """
        对象当方法用时触发
        :param args:
        :param kwargs:
        :return:
        """
        return RedisClient.redis()
