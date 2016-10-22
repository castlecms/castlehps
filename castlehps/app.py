from aiohttp import web


class CastleHPSApplication(web.Application):
    def __init__(self, settings):
        self.settings = settings
        super(CastleHPSApplication, self).__init__()
