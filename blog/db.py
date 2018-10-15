import aiopg.sa


async def init_pg(app):
    conf = app['config']['postgres']
    engine = await aiopg.sa.create_engine(
        database=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
    )
    app['db'] = engine
    # app['api']['db'] = engine

    # from aiohttp_security import setup as setup_security
    # from aiohttp_security import SessionIdentityPolicy
    # from .auth import DBAuthorizationPolicy

    # auth_db = DBAuthorizationPolicy(engine)
    # session_policy = SessionIdentityPolicy()
    # setup_security(app, session_policy, auth_db)
    # setup_security(app['api'], session_policy, auth_db)


async def close_pg(app):
    app['db'].close()
    await app['db'].wait_closed()
