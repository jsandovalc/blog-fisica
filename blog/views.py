import sqlalchemy as sa
import aiohttp_jinja2
from aiohttp import web
from . import db


@aiohttp_jinja2.template('index.html')
async def index(request):
    page = int(request.query.get('page', 1))
    offset = (page - 1) * 10

    async with request.app['db'].acquire() as conn:
        query = sa.text('''
        SELECT p.id, p.title, p.publish_date, p.slug, p.subtitle,
        (
        SELECT ARRAY(SELECT t.title
        FROM tags_posts pt
        JOIN tags t ON t.id=pt.tag
        WHERE pt.post = p.id)
        ) AS post_tags
        FROM posts p
        ORDER BY p.publish_date DESC
        LIMIT 10
        OFFSET :page ROWS;
        ''')

        ret = await conn.execute(query, page=offset)
        db_posts = await ret.fetchall()

    if not db_posts:
        raise web.HTTPNotFound

    return {'posts': db_posts, 'page': page}


@aiohttp_jinja2.template('post.html')
async def post(request):
    slug = request.match_info['slug']

    async with request.app['db'].acquire() as conn:
        query = sa.select([db.posts, db.tags_posts, db.tags],
                          use_labels=True).where(
            db.posts.c.slug == slug).where(
                db.posts.c.id == db.tags_posts.c.post).where(
                    db.tags_posts.c.tag == db.tags.c.id)
        posts = await conn.execute(query)
        posts = await posts.fetchall()
        for key in posts[0].keys():
            print(key)

    return {'post': posts[0], 'tags': [post['tags_title'] for post in posts]}
