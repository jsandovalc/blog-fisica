import sqlalchemy as sa
import aiohttp_jinja2
from sqlalchemy.dialects.postgresql import ARRAY, array, array_agg
from .db import posts, tags, tags_posts


@aiohttp_jinja2.template('index.html')
async def index(request):
    offset = (int(request.query.get('page')) - 1) * 10
    async with request.app['db'].acquire() as conn:
        query = f'''
        SELECT p.id, p.title, p.publish_date, p.slug, p.subtitle,
        (
        SELECT ARRAY(SELECT t.title
        FROM tags_posts pt
        JOIN tags t ON t.id=pt.tag
        WHERE pt.post = p.id)
        ) AS post_tags
        FROM posts p
        OFFSET :page ROWS
        ORDER BY p.publish_date DESC LIMIT 10;
        '''
        ret = await conn.execute(query, page=offset)
        db_posts = await ret.fetchall()

    return {'posts': db_posts}


@aiohttp_jinja2.template('post.html')
async def post(request):
    return {}
