import uuid
import math
import time
from common.core.redisdb.redis_pool import RedisClient


class RedisLock:

    def __init__(self, lock_name, conn=None, lock_timeout=60, db='default'):
        self.lock_name = lock_name
        self.lock_timeout = lock_timeout
        if not conn:
            conn = RedisClient.redis(db)
        self.conn = conn

    def acquire_lock(self, acquire_timeout=5, lock_timeout=None):
        """
        基于 Redis 实现的分布式锁
        :param acquire_timeout: 获取锁的超时时间，默认 5 秒
        :param lock_timeout: 锁的超时时间，默认 60 秒
        :return:
        """
        if not lock_timeout:
            lock_timeout = self.get_lock_timeout()
        identifier = str(uuid.uuid4())
        lock_name = self.__get_lock_names()
        lock_timeout = int(math.ceil(lock_timeout))

        end = time.time() + acquire_timeout

        while time.time() < end:
            # 如果不存在这个锁则加锁并设置过期时间，避免死锁
            if self.get_conn().set(lock_name, identifier, ex=lock_timeout, nx=True):
                return identifier

            time.sleep(0.001)

        return False

    def release_lock(self, identifier):
        """
        释放锁
        :param identifier: 锁的标识
        :return:
        """
        unlock_script = """
        if redis.call("get",KEYS[1]) == ARGV[1] then
            return redis.call("del",KEYS[1])
        else
            return 0
        end
        """
        lock_name = self.__get_lock_names()
        unlock = self.get_conn().register_script(unlock_script)
        result = unlock(keys=[lock_name], args=[identifier])
        if result:
            return True
        else:
            return False

    def __get_lock_names(self):
        """
        获取完整锁名称
        :return:
        """
        return f'lock:{self.get_lock_name()}'

    def get_lock_name(self):
        return self.lock_name

    def get_lock_timeout(self):
        return self.lock_timeout

    def get_conn(self):
        return self.conn
