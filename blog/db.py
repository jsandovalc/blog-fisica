import datetime as dt
import aiopg.sa
from sqlalchemy import Table, Column, Integer, String, MetaData, Boolean
from sqlalchemy import DateTime, Text, ForeignKey


metadata = MetaData()

tags = Table('tags', metadata,
             Column('id', Integer, primary_key=True),
             Column('title', Text, nullable=False, unique=True))

tags_posts = Table('tags_posts', metadata,
                   Column('tag', Integer, ForeignKey('tags.id')),
                   Column('post', Integer, ForeignKey('posts.id')))

posts = Table('posts', metadata,
              Column('id', Integer, primary_key=True),
              Column('title', String, nullable=False),
              Column('subtitle', String),
              Column('slug', String, nullable=False, unique=True),
              Column('draft', Boolean, nullable=False),
              Column('content', Text, nullable=False),
              Column('publish_date', DateTime, default=dt.datetime.utcnow))


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


async def close_pg(app):
    app['db'].close()
    await app['db'].wait_closed()
