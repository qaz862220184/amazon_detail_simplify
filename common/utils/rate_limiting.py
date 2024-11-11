from common.core.redisdb.redis_pool import RedisClient
from common.utils.encryption import Md5Encrytion
import time
import random


class RequestLimiting:
    # 限定时间【在限定的时间范围内达到下面条件就会封禁，如果时间过期将会开始新一轮的累计】
    limited_timestamp = (3600 * 3)
    max_total_count = 2000
    max_error_count = 8
    # 封禁时间
    forbid_timestamp = (3600 * 1)

    def __init__(
            self,
            key,
            limited_timestamp=limited_timestamp,
            max_total_count=max_total_count,
            max_error_count=max_error_count,
            forbid_timestamp=forbid_timestamp,
    ):
        self.key = key
        self.limited_timestamp = limited_timestamp
        self.max_total_count = max_total_count
        self.max_error_count = max_error_count
        self.forbid_timestamp = forbid_timestamp
        # redis对象
        self.redis = RedisClient.redis()
        # 初始化哈希
        rule_key = self.get_cache_key()
        if not self.redis.hgetall(name=rule_key):
            self.__init_data()

    def is_survive(self):
        """
        是否存活【可用】
        :return:
        """
        lock_key = self.get_cache_key(type=1)
        if self.redis.get(lock_key):
            return False
        else:
            timestamp = int(time.time())
            name_key = self.get_cache_key()
            key = 'expires_timestamp'
            expires_timestamp = int(
                self.redis.hget(name=name_key, key=key)
            )
            if 0 < expires_timestamp < timestamp:
                # 当前数据已过期，需要重新生成计数
                self.__init_data()
            return True

    def error_count_increment(self):
        """
        错误次数加1
        :return:
        """
        if self.is_survive() is False:
            return None
        name_key = self.get_cache_key()
        key = 'error_count'
        # 递增
        self.redis.hincrby(name=name_key, key=key)
        error_count = int(self.redis.hget(name=name_key, key=key))
        if error_count >= self.max_error_count:
            # 重置数据 并且 加锁
            self.__set_lock()
        return error_count

    def total_count_increment(self):
        """
        总次数加1
        :return:
        """
        if self.is_survive() is False:
            return None
        name_key = self.get_cache_key()
        key = 'total_count'
        # 递增
        self.redis.hincrby(name=name_key, key=key)
        total_count = int(self.redis.hget(name=name_key, key=key))
        if total_count >= self.max_total_count:
            # 重置数据 并且 加锁
            self.__set_lock()
        return total_count

    def get_cache_key(self, type=0):
        """
        获取缓存key
        :param type:
        :return:
        """
        if type == 0:
            type = 'rule'
        elif type == 1:
            type = 'lock'
        key = Md5Encrytion.md5_lower32(self.key)
        return f'amazon_scrapy_request_validate_{type}_{key}'

    def __set_lock(self):
        # 加锁
        lock_key = self.get_cache_key(1)
        self.redis.set(
            name=lock_key,
            value=1,
            ex=self.forbid_timestamp
        )
        # 重置数据
        self.__init_data(initial_timestamp=self.forbid_timestamp)
        return True

    def __init_data(self, initial_timestamp=0):
        """
        初始化数据
        :param initial_timestamp:
        :return:
        """
        expires_timestamp = 0
        if self.limited_timestamp >= 0:
            # 说明限定时间
            timestamp = int(time.time())
            expires_timestamp = (timestamp
                                 + self.limited_timestamp
                                 + initial_timestamp)
        default = {
            'total_count': 0,
            'error_count': 0,
            'expires_timestamp': expires_timestamp,
            'origin_key': self.key
        }
        # 初始化哈希
        rule_key = self.get_cache_key()
        return self.redis.hset(name=rule_key, mapping=default)



class RequestRatioLimiting:

    def __init__(self, exec_ratio, non_exec_ratio):
        """
        初始化
        :param exec_ratio:
        :param non_exec_ratio:
        """
        self.exec_ratio = self.__get_ratio(exec_ratio)
        self.non_exec_ratio = self.__get_ratio(non_exec_ratio)

    def is_exec(self):
        """
        是否执行
        :return:
        """
        some_list = [False, True]
        probabilities = [self.non_exec_ratio, self.exec_ratio]
        return self.random_pick(
            some_list=some_list,
            probabilities=probabilities
        )

    @classmethod
    def random_pick(cls, some_list, probabilities):
        """
        随机选择
        :param some_list:
        :param probabilities:
        :return:
        """
        x = random.uniform(0, 1)
        cumulative_probability = 0.0
        item = None
        for item, item_probability in zip(some_list, probabilities):
            cumulative_probability += item_probability
            if x < cumulative_probability:
                break
        return item

    @classmethod
    def __get_ratio(cls, value):
        """
        获取比例
        :param value:
        :return:
        """
        if value >= 1:
            value = round(value / 100, 2)
        if value > 1:
            raise ValueError('The value of the ratio cannot be greater than 1')
        return value




if __name__ == '__main__':
    rules = {
        # 限定时间范围，填0时则为无时间限制
        'limited_timestamp': (3600 * 3),
        # 在限定的时间范围内最大的请求次数
        'max_total_count': 6000,
        # 在限定的时间范围内最大的错误请求次数
        'max_error_count': 20,
        # 禁止时间
        'forbid_timestamp': (3600 * 1)
    }
    request = RequestLimiting(key='www', ** rules)
    request.error_count_increment()
    request.total_count_increment()


    # rules = {
    #     # 执行主动模式比例
    #     'exec_ratio': 30,
    #     # 不执行主动模式比例
    #     'non_exec_ratio': 70,
    # }
    # request = RequestRatioLimiting(** rules)
    # res1 = []
    # res2 = []
    # for i in range(1, 101):
    #     res = request.is_exec()
    #     if res:
    #         res1.append(res)
    #     else:
    #         res2.append(res)
    # print(len(res1))
    # print(len(res2))
