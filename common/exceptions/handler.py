
class ExceptionHandler:

    @classmethod
    def get_last_exception_stack(cls, exception):
        """
        获取最后的堆栈跟踪
        :param exception:
        :return:
        """
        trace = cls.get_exception_stack(exception)
        if trace:
            return trace[len(trace) - 1]
        return None

    @classmethod
    def get_exception_stack(cls, exception):
        """
        获取异常捕获的堆栈
        :param exception:
        :return:
        """
        if isinstance(exception, BaseException):
            trace = []
            tb = exception.__traceback__
            while tb is not None:
                filename = tb.tb_frame.f_code.co_filename
                trace.append({
                    "filename": filename.replace('\\', '/'),
                    "name": tb.tb_frame.f_code.co_name,
                    "lineno": tb.tb_lineno
                })
                tb = tb.tb_next
            return trace
