import sqlalchemy as sa
import aiohttp_jinja2
from sqlalchemy.dialects.postgresql import ARRAY
from .db import posts, tags, tags_posts


@aiohttp_jinja2.template('index.html')
async def index(request):
    async with request.app['db'].acquire() as conn:
        query = sa.select([posts, tags, tags_posts,
                           sa.func.array_agg(
                               tags.c.title,
                               type_=ARRAY(sa.String)).label('tags')],
                          use_labels=True).where(
            sa.and_(
                posts.c.id == tags_posts.c.post,
                tags_posts.c.tag == tags.c.id)).group_by(
                    posts.c.id, tags.c.id, tags_posts.c.tag, tags_posts.c.post)
        # .order_by(db.posts.c.publish_date.desc())
        print(query)
        ret = await conn.execute(query)
        db_posts = await ret.fetchall()
        # print(dir(posts[0]), 'llaves', posts[0].items())
        for item in db_posts[0].keys():
            print(item)
        # print(db_posts[0]['tags'], len(db_posts))
    return {'posts': db_posts}
