import sqlalchemy as sa
import aiohttp_jinja2
from email.mime.text import MIMEText
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


@aiohttp_jinja2.template('about.html')
async def about(request):
    return {}


@aiohttp_jinja2.template('contact.html')
async def contact(request):
    return {}

@aiohttp_jinja2.template('contact.html')
async def post_contact(request):
    host = config.mail_host
    port = config.mail_port
    user = config.mail_user
    password = config.mail_password

    loop = asyncio.get_event_loop()
    server = aiosmtplib.SMTP(host, port, loop=loop, use_tls=False)

    await server.connect()
    await server.starttls()
    await server.login(user, password)

    message = MIMEText(
        request.post().get('name') + '\n\n' +
        request.post().get('message') + '\n\n' +
        ','.join(request.post.get('email')))
    message['From'] = user
    message['To'] = user
    message['Subject'] = 'Mensaje recibido en el blog de Arquímedes'

    await server.send_message(message)

        # return response.json({'message': 'Mail sent'}, status=201)
    return {}
