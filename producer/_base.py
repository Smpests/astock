class BaseProducer(object):

    def produce(self, *args, **kwargs):
        raise NotImplementedError

    async def async_produce(self, *args, **kwargs):
        raise NotImplementedError
