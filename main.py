import pymongo
import wtforms
from wtforms import validators, widgets
from sanic import Sanic, response
from sanic.views import HTTPMethodView
from sanic_jinja2 import SanicJinja2
from sanic_wtf import SanicForm
from motor import motor_asyncio
from slugify import slugify


app = Sanic(__name__)
jinja = SanicJinja2(app)
db = None

app.config['WTF_CSRF_SECRET_KEY'] = 'the super secret'

app.static('/static', './static')


class PostForm(SanicForm):
    title = wtforms.StringField('Título', validators=[
        validators.DataRequired()])
    subtitle = wtforms.StringField('Subtítulo')
    slug = wtforms.StringField('Cadena legible')
    publish_date = wtforms.DateTimeField('Fecha de publicación',
                                         format="%m/%d/%Y %H:%M %p")
    content = wtforms.StringField('Contenido', widget=widgets.TextArea())


session = {}


@app.middleware('request')
async def add_session(request):
    request['session'] = session


async def setup_db():
    """"""
    global db
    db = motor_asyncio.AsyncIOMotorClient('mongodb://127.0.0.1:27017')

app.add_task(setup_db())


@app.route("/")
async def index(request):
    posts = await db.blog_fisica.post.find(
        {'draft': False}).sort('publish_date', pymongo.DESCENDING).to_list(
            length=10)
    return jinja.render('index.html', request, posts=posts)


@app.route("/post")
async def posts(request):
    return jinja.render('post.html', request)


@app.route("/post/<slug>")
async def post(request, slug):
    post = await db.blog_fisica.post.find_one({'slug': slug})
    return jinja.render('post.html', request, post=post)

@app.route("/admin/posts/")
async def list_posts(request):
    """Show a table with all posts."""
    posts = await db.blog_fisica.post.find(
        {'draft': False}).sort('publish_date', pymongo.DESCENDING).to_list(
            length=10)
    return jinja.render('list_posts.html', request, posts=posts)


class Posts(HTTPMethodView):
    """A post in admin.

    It allows to create and store a post.

    """
    async def get(self, request):
        """Return the form."""
        form = PostForm(request)
        return jinja.render('add_post.html', request, form=form)

    async def post(self, request):
        """Save the post."""
        form = PostForm(request)

        if form.validate_on_submit():
            await db.blog_fisica.post.insert_one(dict(
                title=form.title.data,
                subtitle=form.subtitle.data,
                publish_date=form.publish_date.data,
                slug=slugify(form.title.data),
                draft=False,
                content=form.content.data,
            ))

            return response.redirect('/')

        return response.redirect('/404')


class Post(HTTPMethodView):
    async def get(self, request, slug):
        """Return the form with data."""
        post = await db.blog_fisica.post.find_one(dict(
            slug=slug
        ))
        form = PostForm(request, **post)
        return jinja.render('edit_post.html', request, form=form)

    async def post(self, request, slug):
        """Updates the post"""
        form = PostForm(request)

        if form.validate_on_submit():
            r = await db.blog_fisica.post.update_one(
                {'slug': slug},
                {'$set': dict(
                    title=form.title.data,
                    subtitle=form.subtitle.data,
                    publish_date=form.publish_date.data,
                    draft=False,
                    content=form.content.data,
                )
            })

            return response.redirect(app.url_for('post', slug=slug))

        return response.redirect('/404')


app.add_route(Posts.as_view(), '/admin/post')
app.add_route(Post.as_view(), '/admin/post/<slug>')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7000, debug=True)
