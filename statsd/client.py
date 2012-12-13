import logging
import random
import socket
import time


logger = logging.getLogger('statd')


class Statsd(object):

    def __init__(self, bucket_prefix='', host='127.0.0.1', port=8125,
                 buffer_size=0):
        self.bucket_prefix = bucket_prefix
        self.address = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.buffer_size = buffer_size
        self.buffer = ''

    def __del__(self):
        self.flush()

    def __setitem__(self, bucket, value):
        self.gauge(bucket, value)

    def flush(self):
        if self.buffer:
            logger.debug('sendto %r', self.buffer)
            self.socket.sendto(self.buffer, self.address)
            self.buffer = ''

    def send(self, command):
        logger.info('send %r', command)
        if self.buffer_size:
            if self.buffer:
                if len(self.buffer) + 1 + len(command) <= self.buffer_size:
                    self.buffer += '\n'
                    self.buffer += command
                    if len(self.buffer) == self.buffer_size:
                        self.flush()
                    return
                self.flush()
            if len(command) < self.buffer_size:
                self.buffer = command
                return
        logger.debug('sendto %r', command)
        self.socket.sendto(command, self.address)

    def child(self, name):
        return StatsdChild(self, name)

    def count(self, bucket, value=1, sampling=None):
        if sampling is None:
            self.send('%s%s:%d|c' % (self.bucket_prefix, bucket, value))
        else:
            if random.random() < sampling:
                self.send('%s%s:%d|c|@%f' % (self.bucket_prefix, bucket,
                                             value, sampling))

    def counter(self, bucket, sampling=None):
        return StatsdCounter(self, bucket, sampling=sampling)

    def gauge(self, bucket, value):
        self.send('%s%s:%r|g' % (self.bucket_prefix, bucket, value))

    def time(self, bucket, seconds):
        self.send('%s%s:%d|ms' % (self.bucket_prefix, bucket, 1000 * seconds))

    def timer(self, bucket):
        return StatsdTimer(self, bucket)


class StatsdChild(Statsd):

    def __init__(self, parent, name):
        if parent.bucket_prefix:
            bucket_prefix = parent.bucket_prefix + '.' + name + '.'
        else:
            bucket_prefix = name + '.'
        Statsd.__init__(self, bucket_prefix)
        self.parent = parent

    def flush(self):
        self.parent.flush()

    def send(self, command):
        self.parent.send(command)


class StatsdCounter(object):

    def __init__(self, statsd, bucket, sampling=None):
        self.statsd = statsd
        self.bucket = bucket
        self.sampling = sampling

    def __enter__(self):
        self.statsd.count(self.bucket, 1)
        return self

    def __exit__(self):
        self.statsd.count(self.bucket, -1)

    def __iadd__(self, value):
        self.statsd.count(self.bucket, value, self.sampling)


class StatsdTimer(object):

    def __init__(self, statsd, bucket):
        self.statsd = statsd
        self.bucket = bucket
        self._start = None
        self._split = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def start(self):
        self._start = time.time()
        self._split = None

    def stop(self):
        self.statsd.time(self.bucket, time.time() - self._start)
        self._start = None
        self._split = None

    def split(self, sub_bucket):
        now = time.time()
        seconds = now - (self._split or self._start)
        self.statsd.time(self.bucket + '.' + sub_bucket, seconds)
        self._split = now
