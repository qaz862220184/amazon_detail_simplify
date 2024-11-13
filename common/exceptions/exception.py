

class JhBaseException(Exception):
    """
    异常父类
    """
    _type = 'scrapy-exception'

    def __init__(self, msg, **kwargs):
        self._msg = msg
        self._param = kwargs

    def __repr__(self):
        return self.to_string()

    def __str__(self):
        return self.to_string()

    def to_string(self):
        """
        转string
        :return:
        """
        return f'[{self._type}] Message: {self._msg}'

    def get_msg(self):
        """
        获取提示信息
        :return:
        """
        return self._msg

    def get_type(self):
        """
        获取类型
        :return:
        """
        return self._type

    def get_param(self):
        """
        获取参数
        :return:
        """
        return self._param


class SystemException(JhBaseException):
    _type = 'system-exception'


class XpathException(JhBaseException):
    _type = 'xpath-exception'


class RequestException(JhBaseException):
    _type = 'request-exception'


class TimeoutException(JhBaseException):
    _type = 'timeout-exception'


class ConfiguredException(JhBaseException):
    _type = 'configured-exception'


class PipelineException(JhBaseException):
    _type = 'pipeline-exception'


class CookieException(JhBaseException):
    _type = 'cookie-exception'


class ProxyException(JhBaseException):
    _type = 'proxy-exception'
