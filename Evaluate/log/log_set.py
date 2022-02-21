import os
import logging
import time
from logging import Handler, FileHandler, StreamHandler


class PathFileHandler(FileHandler):
    def __init__(self, path, filename, mode='a', encoding=None, delay=False):
        if not os.path.exists(path):
            os.mkdir(path)
        self.baseFilename = os.path.join(path, filename)
        self.mode = mode
        self.encoding = encoding
        self.delay = delay
        if delay:
            Handler.__init__(self)
            self.stream = None
        else:
            StreamHandler.__init__(self, self._open())


class Loggers(object):
    # 日志级别关系映射
    level_relations = {
        'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING,
        'error': logging.ERROR, 'critical': logging.CRITICAL
    }

    def __init__(self, level='info',
                 filename='{date}.log'.format(date=time.strftime("%Y-%m-%d_%H%M%S", time.localtime())),
                 log_dir='log_info', fmt='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        self.logger = logging.getLogger(filename)

        self.directory = os.path.join(os.getcwd(), log_dir)
        format_str = logging.Formatter(fmt)
        self.logger.setLevel(self.level_relations.get(level))
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(format_str)
        file_handler = PathFileHandler(path=self.directory, filename=filename, mode='a')
        file_handler.setFormatter(format_str)
        self.logger.addHandler(stream_handler)
        self.logger.addHandler(file_handler)


if __name__ == "__main__":
    """
    使用前只需要先调用Loggers类，然后在捕获错误的位置自定义信息，此模块会将错误日志报错在log_info中
    """
    txt = "错误信22222222222息"
    log = Loggers()
    log.logger.info(txt)
