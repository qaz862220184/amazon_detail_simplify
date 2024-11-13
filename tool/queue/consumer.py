import sys
sys.path.append('..')
sys.path.append('../..')
sys.path.append('../../..')
import json
import traceback
from bson.objectid import ObjectId
from common.core.mongodb.mongo import MongoDb
from common.core.query.sub_meter import SubMeterQuery
from common.core.redisdb.redis_pool import RedisClient
from common.utils.cache import Chcaed
from common.utils.message import RocketMessage
import functools
import redis
import asyncio
import aiohttp
from loguru import logger
from filelock import FileLock


# 重试装饰器
def retry(retries=3, delay_time=5):
    func_name_map = {
        1: 'close line',
        2: 'retry task',
        3: 'crawl result call',
        4: 'change vpn',
    }

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            attempts = 0
            while attempts < retries:
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    func_type = args[0]['type']
                    func_name = func_name_map.get(func_type)
                    self.logger.debug(f'{func_name} error, message is: {str(e)}')
                    attempts += 1
                    if attempts == retries:
                        self.logger.error(f"Function {func_name} failed after {retries} retries")
                        raise
                    else:
                        self.logger.warning(f"Retrying {func_name} in {delay_time} seconds ({attempts}/{retries})")
                        await asyncio.sleep(delay_time)
        return wrapper
    return decorator


class AsyncTask(object):

    def __init__(self):
        log_file = f'adv_spider_task.log'
        self.logger = self.setup_logger_async(log_file)
        self.redis_client = RedisClient.redis('client')

    @classmethod
    def setup_logger_async(cls, log_file):
        lock = FileLock(log_file + ".lock")
        with lock:
            logger.remove()
            logger.add(log_file, rotation='00:00', retention='7 days', encoding='utf-8', enqueue=True, backtrace=True, diagnose=True)
            return logger

    @classmethod
    def get_redis_client(cls):
        # redis池
        connect = redis.ConnectionPool(
            host="127.0.0.1",
            port=6379,
            db=0,
            max_connections=10,
            decode_responses=True,
        )
        return redis.Redis(connection_pool=connect)

    @retry(retries=3, delay_time=5)
    async def callback_task(self, data, semaphore):
        async with semaphore:
            self.logger.debug(data)
            verify = data.get('verify', False)
            conn = aiohttp.TCPConnector(ssl=verify)
            task_type = data['type']
            params = data['params']
            # TODO 根据这个类型
            if int(task_type) == 4:
                network_line_id = params.get('network_line_id')
                key_name = str(network_line_id) + '_used'
                change_tag = Chcaed.get(key_name, db='client')
                if change_tag:
                    self.logger.debug('change time not out!!!')
                    return
            async with aiohttp.ClientSession(connector=conn) as session:
                url = data['url']
                headers = data['headers']
                async with session.post(url=url, json=params, headers=headers) as response:
                    res = await response.json()
                    if 'code' in res and res['code'] == 200:
                        return True
                    self.logger.debug(f'the request type is {task_type}, response is {res}')
                    # 补充一些切换操作的返回操作
                    if int(task_type) == 4:
                        network_line_id = params.get('network_line_id')
                        self._do_change_after(res, network_line_id)
                    # 有一些接口的正确返回code是2000
                    if 'code' in res and res['code'] == 2000:
                        inform_status = 1
                    else:
                        inform_status = 2
                    inform_error = res.get('msg', '')
                    # 这些是任务回调需要用到的数据
                    if task_type == 3:
                        update_sql = {'inform_status': inform_status}
                        if inform_error:
                            update_sql['inform_error'] = inform_error
                        # 保存数据
                        return MongoDb.sub_table('scrapy_sub_task', SubMeterQuery.CYCLE_YEARLY).update_one(
                            {'_id': {'$eq': ObjectId(data['sub_task_id'])}, "platform": data['platform']},
                            {'$set': update_sql}
                        )

    async def process_queue(self):
        semaphore = asyncio.Semaphore(50)
        while True:
            # 使用 blpop 阻塞等待队列数据，超时时间设置为 0 表示一直阻塞直到有数据
            queue_name, data = self.redis_client.blpop('adv_scrapy', timeout=0)
            # 根据已有数据请求接口
            try:
                if data is not None:
                    result = json.loads(data)
                    await self.callback_task(result, semaphore)
            except:
                traceback.format_exc()

    def main(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.process_queue())

    @classmethod
    def _do_change_after(cls, response, network_line_id):
        """
        根据切换接口返回的数据执行操作
        605：vps状态不正确，请切换线路
        403：vpn服务商不存在（严重错误，需要提醒）
        201：当前已存在占用锁，等待解锁切换vpn（需要更换线路）
        602：不可切换vpn，请继续使用 （继续使用vpn）
        200：vpn切换成功（需要更换线路）
        """
        if 'code' in response and response['code'] == 200:
            return True
        if 'code' in response and response['code'] == 201:
            return True
        if 'code' in response and response['code'] == 605:
            return True
        if 'code' in response and response['code'] == 602:
            # 减少计数
            redis_key = '{}_vpn_use_count'.format(network_line_id)
            use_count = Chcaed.get(redis_key, db='client')
            Chcaed.put(redis_key, use_count - 20, db='client')
            return True
        if 'code' in response and response['code'] == 403:
            RocketMessage.send_by_user('vpn服务商不存在,请检查线路数据')
            return True
        return True


if __name__ == '__main__':
    AsyncTask().main()
