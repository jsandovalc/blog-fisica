import sys
import asyncio
import logging
import uvloop
import aiohttp_jinja2
import jinja2
from aiohttp import web
# from aioredis import create_pool
# from aiohttp_session import setup as setup_session
# from aiohttp_session.redis_storage import RedisStorage
from .routes import setup_routes
#from .processors import add_user_processor
# from .db import init_pg, close_pg


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


@web.middleware
async def handle_401(request, handler):
    """Send to login on Unathorized."""
    try:
        response = await handler(request)
    except web.HTTPUnauthorized:
        raise web.HTTPFound('/login')

    return response


async def init_app(argv=None, redis='redis', init_postgres=None,
                   close_postgres=None):
    app = web.Application(debug=True, middlewares=[handle_401])

    # redis_pool = await create_pool((redis, 6379))
    # setup_session(app, RedisStorage(redis_pool))

    # aiohttp_jinja2.setup(app,
    #                      context_processors=[add_user_processor,
    #                                          aiohttp_jinja2.request_processor],
    #                      loader=jinja2.PackageLoader('ads', 'templates'))

    aiohttp_jinja2.setup(app,
                         loader=jinja2.PackageLoader('blog', 'templates'))


    # app.on_startup.append(init_postgres or init_pg)
    # app.on_cleanup.append(close_postgres or close_pg)

    # app['config'] = config
    # app['api'] = api_app

    setup_routes(app)

    # app.add_subapp('/api/v1/', api_app)

    return app


def main(argv):
    logging.basicConfig(level=logging.DEBUG)

    app = init_app(argv)

    web.run_app(app,  host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main(sys.argv[1:])
