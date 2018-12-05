import sys
import pathlib
import asyncio
import logging
import uvloop
import aiohttp_jinja2
import jinja2
import aiohttp_security
import aiohttp_admin
from aiohttp import web
# from aiohttp_admin.backends.sa import PGResource
from aiohttp_admin.security import DummyAuthPolicy, DummyTokenIdentityPolicy
from .routes import setup_routes
from .settings import config
# from aioredis import create_pool
# from aiohttp_session import setup as setup_session
# from aiohttp_session.redis_storage import RedisStorage
# from .processors import add_user_processor
from .db import init_pg, close_pg


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

PROJ_ROOT = pathlib.Path(__file__).parent.parent


@web.middleware
async def handle_401(request, handler):
    """Send to login on Unathorized."""
    try:
        response = await handler(request)
    except web.HTTPUnauthorized:
        raise web.HTTPFound('/login')

    return response


def setup_admin(app, pg):
    admin_config_path = str(PROJ_ROOT / 'static' / 'js')
    # resources = (PGResource(pg, db.post, url='posts'),
    #              PGResource(pg, db.tag, url='tags'),
    #              PGResource(pg, db.comment, url='comments'))
    admin = aiohttp_admin.setup(app, admin_config_path, resources=tuple())

    # setup dummy auth and identity
    ident_policy = DummyTokenIdentityPolicy()
    auth_policy = DummyAuthPolicy(username="admin", password="admin")
    aiohttp_security.setup(admin, ident_policy, auth_policy)

    return admin


async def init_app(argv=None, redis='redis', init_postgres=None,
                   close_postgres=None):

    app = web.Application(debug=True, middlewares=[handle_401])

    aiohttp_jinja2.setup(app,
                         loader=jinja2.PackageLoader('blog', 'templates'))

    app['config'] = config

    pg = await init_pg(app)
    app.on_cleanup.append(close_postgres or close_pg)

    setup_routes(app)

    admin = setup_admin(app, pg)
    app.add_subapp('/admin/', admin)

    return app


def main(argv):
    logging.basicConfig(level=logging.DEBUG)
    app = init_app(argv)
    web.run_app(app,  host='0.0.0.0', port=config['blog'].get('port', 7000))


if __name__ == '__main__':
    main(sys.argv[1:])
