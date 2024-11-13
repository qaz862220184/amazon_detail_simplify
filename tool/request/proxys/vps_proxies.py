# -*- coding: UTF-8 -*-
import requests
import random
from common.utils.cache import Chcaed
from common.utils.jhvps.vpn_proxy_api import LineProxy, logger
from common.utils.distribution_lock import RedisLock
from common.settings import CENTRES
from common.exceptions.exception import ProxyException


class VpsProxiesTool(object):
    lock_time = 30
    lock = RedisLock(
        lock_name='change_vpn',
        lock_timeout=lock_time
    )

    @classmethod
    def check_line(cls):
        """
        检查缓存中是否存在线路
        :return:
        """
        identifier = cls.lock.acquire_lock(
            acquire_timeout=cls.lock_time
        )
        try:
            if not LineProxy.get_v2ray_connect_url():
                LineProxy().change_vpn_line()
        except:
            raise ValueError("check the vpn line is error!")
        finally:
            cls.lock.release_lock(
                identifier=identifier
            )

    @classmethod
    def change_vpn_resource(cls, network_line_id, vpn=None, change_type=1):
        """
        切换线路代理
        :param network_line_id:
        :param vpn:
        :param change_type:
        :return:
        """
        lock = RedisLock(
            lock_name='change_vpn',
            lock_timeout=30,
            db='client'
        )
        identifier = lock.acquire_lock(
            acquire_timeout=cls.lock_time
        )
        try:
            # TODO 在这里添加一下时间的判断， 在redis中存储一个10分钟过期的key
            key_name = str(network_line_id) + '_used'
            change_tag = Chcaed.get(key_name, db='client')
            if change_tag:
                return 'default'
            Chcaed.put(key_name, True, 300, db='client')
            vpn_name = LineProxy().change_vpn_resource(LineProxy.get_network_line_id(), vpn, change_type)
            cls.set_vpn_stochastic_restrictions(network_line_id)
            return vpn_name
        except Exception as e:
            raise ProxyException("change vpn resource is error! error is {}".format(e), error_type='vps')
        finally:
            lock.release_lock(
                identifier=identifier
            )

    @classmethod
    def get_vpn_name(cls, network_line_id):
        """
        获取vpn_name
        :return:
        """
        redis_key = '{}_vps_vpn_name'.format(network_line_id)
        return Chcaed.get(redis_key, db='client')

    @classmethod
    def set_vpn_name(cls, network_line_id, vpn_name):
        """
        设置vpn_name
        :param vpn_name:
        :param network_line_id:
        :return:
        """
        redis_key = '{}_vps_vpn_name'.format(network_line_id)
        return Chcaed.put(redis_key, vpn_name, db='client')

    @classmethod
    def get_vpn_use_count(cls, network_line_id):
        """
        获取当前VPN的使用次数
        :return:
        """
        redis_key = '{}_vpn_use_count'.format(network_line_id)
        return Chcaed.get(redis_key, db='client')

    @classmethod
    def set_vpn_use_count(cls, use_count, network_line_id):
        """
        设置当前vpn的使用次数
        :return:
        """
        redis_key = '{}_vpn_use_count'.format(network_line_id)
        return Chcaed.put(redis_key, use_count, db='client')

    @classmethod
    def get_vpn_stochastic_restrictions(cls, network_line_id):
        """
        获取当前vpn的随机限制数量
        """
        redis_key = '{}_vpn_stochastic_restrictions'.format(network_line_id)
        return Chcaed.get(redis_key, db='client')

    @classmethod
    def set_vpn_stochastic_restrictions(cls, network_line_id):
        """
        获取当前vpn的随机限制数量
        """
        redis_key = '{}_vpn_stochastic_restrictions'.format(network_line_id)
        stochastic_restrictions = random.randint(100, 200)
        return Chcaed.put(redis_key, stochastic_restrictions, db='client')


class VpsProxiesTactic(VpsProxiesTool):

    @classmethod
    def change_vpn(cls, count, network_line_id, vpn=None, change_type=1):
        """
        切换代理
        :param count:
        :param network_line_id:
        :param vpn:
        :param change_type:
        :return:
        """
        # Step 1: 检查线路状态
        VpsProxiesTool.check_line()
        # Step 2： 检查错误状态和获取VPN状态
        error_status = Chcaed.get('{}_errors'.format(network_line_id))
        vpn_name = VpsProxiesTool.get_vpn_name(network_line_id)
        # Step 3：没有vpn名称（第一次运行）或者强制切换或者有错误状态，切换vpn
        if not vpn_name or 2 == change_type or error_status:
            Chcaed.get_driver().delete('errors')  # 删除错误状态
            vpn_name = VpsProxiesTool.change_vpn_resource(network_line_id, vpn, change_type)
            VpsProxiesTool.set_vpn_name(network_line_id, vpn_name)  # 更新vpn名称
            VpsProxiesTool.set_vpn_use_count(0, network_line_id)  # 更新vpn计数
            return True
        # Step 4： 获取vpn的使用次数
        use_count = VpsProxiesTool.get_vpn_use_count(network_line_id)
        if use_count is None:
            use_count = 0
        # Step 5： 获取随机的代理切换上限，不存在则设为200（第一次运行）
        count = VpsProxiesTool.get_vpn_stochastic_restrictions(network_line_id)
        if count is None:
            count = 200
        # Step 6： 判断是否达到切换次数
        if use_count >= count:
            VpsProxiesTool.set_vpn_use_count(0, network_line_id)  # 重置使用次数
            vpn_name = VpsProxiesTool.change_vpn_resource(network_line_id, vpn, change_type)
            VpsProxiesTool.set_vpn_name(network_line_id, vpn_name)
            return True
        # Step 7： 增加线路使用次数并更新
        use_count = use_count + 1
        VpsProxiesTool.set_vpn_use_count(use_count, network_line_id)
        return True

    @classmethod
    def lock_to_change_vpn(cls, network_line_id, vpn=None, change_type=1):
        """
        vpn异常--避免并发状态下出现重复切换操作
        :param vpn:
        :param network_line_id:
        :param change_type:
        :return:
        """
        lock_key = 'change_proxies_lock'
        lock_current = Chcaed.get(lock_key)
        if not lock_current:
            Chcaed.put(lock_key, 'change_proxies_lock', 30)
            cls.change_vpn(count=0, network_line_id=network_line_id, vpn=vpn, change_type=change_type)
        return True

    @classmethod
    def change_vpn_line(cls, business_id=None, country=None, area_type=None, frequency_time=10):
        data = LineProxy().change_vpn_line(business_id, country, area_type, frequency_time)
        return data

    @classmethod
    def get_line_proxies(cls, line_id):
        """
        获取线路对应的端口号
        :return:
        """
        url = CENTRES['api']
        params = {'network_line_id': line_id}
        response = requests.get(url, params=params)
        res = response.json()
        if 'code' in res and res['code'] == 200:
            port = res['data'].get('port')
            proxies = '{}:{}'.format(CENTRES['address'], port)
            logger.debug('get proxy is done!!! proxy is {}'.format(proxies))
            return proxies
        logger.debug('get proxy is done!!!')
        raise ValueError('the network_line_id not have corresponding port!!! network_line_id is {}'.format(line_id))

    @classmethod
    def close_line(cls, network_line_id, uuid):
        """
        接触端口占用
        :param network_line_id:
        :param uuid:
        :return:
        """
        LineProxy().close_vpn_line(network_line_id, uuid)
        return True
