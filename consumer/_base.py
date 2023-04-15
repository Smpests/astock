class BaseConsumer(object):

    def consume(self, *args, **kwargs):
        raise NotImplementedError

    async def async_consume(self, *args, **kwargs):
        raise NotImplementedError
