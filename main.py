import pymongo
import wtforms
from wtforms import validators
from sanic import Sanic, response
from sanic.views import HTTPMethodView
from sanic_jinja2 import SanicJinja2
from sanic_wtf import SanicForm
from sanic_auth import Auth, User
from motor import motor_asyncio
from slugify import slugify
from delorean import Delorean


app = Sanic(__name__)
db = None


app.config.WTF_CSRF_SECRET_KEY = 'the super secret'
app.config.AUTH_LOGIN_ENDPOINT = 'login'

app.static('/static', './static')

auth = Auth(app)
jinja = SanicJinja2(app)


class PostForm(SanicForm):
    title = wtforms.StringField('Título', validators=[
        validators.DataRequired()])
    subtitle = wtforms.StringField('Subtítulo')
    slug = wtforms.StringField('Cadena legible')
    publish_date = wtforms.DateTimeField('Fecha de publicación',
                                         format="%m/%d/%Y %H:%M %p")
    content = wtforms.TextAreaField('Contenido')
    tags = wtforms.StringField('Etiquetas')


class QuestionForm(SanicForm):
    content = wtforms.TextAreaField('Pregunta')
    answers = wtforms.FieldList(wtforms.TextAreaField('Respuesta'),
                                min_entries=2)


class LoginForm(SanicForm):
    username = wtforms.StringField(
        'Usuario', validators=[validators.InputRequired()])
    password = wtforms.PasswordField(
        'Contraseña', validators=[validators.InputRequired()])
    submit = wtforms.SubmitField('Ingresar')


session = {}


@app.middleware('request')
async def add_session(request):
    request['session'] = session


@app.route('/login', methods=['GET', 'POST'])
async def login(request):
    message = ''
    form = LoginForm(request)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = form.password.data

        user = await db.blog_fisica.user.find_one(dict(username=username,
                                                       password=password))
        if user:
            user = User(id=1, name=username)
            auth.login_user(request, user)
            return response.redirect('/')
        message = 'invalid username or password'
    return jinja.render('login.html', request, message=message, form=form)


@app.route('/logout')
@auth.login_required
async def logout(request):
    auth.logout_user(request)
    return response.redirect('/login')


async def setup_db():
    global db
    db = motor_asyncio.AsyncIOMotorClient('mongodb://127.0.0.1:27017')

app.add_task(setup_db())


@app.route("/")
async def index(request):
    posts = await db.blog_fisica.post.find(
        dict(draft=False, publish_date={'$lte': Delorean().datetime})).sort(
            'publish_date', pymongo.DESCENDING).to_list(length=10)
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


@app.route("/about/")
async def about(request):
    """Show the about"""
    return jinja.render('about.html', request)


def get_tags_list(tag_string):
    return list(set(tag.strip().lower() for
                    tag in tag_string.split(',')))


class Posts(HTTPMethodView):
    """A post in admin.

    It allows to create and store a post.

    """
    decorators = [auth.login_required]

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
                publish_date=Delorean(form.publish_date.data, 'UTC').datetime,
                slug=slugify(form.title.data),
                draft=False,
                content=form.content.data,
                tags=get_tags_list(form.tags.data)
            ))

            return response.redirect('/')

        return response.redirect('/404')


class Questions(HTTPMethodView):
    """A question for posts."""
    decorators = [auth.login_required]

    async def get(self, request):
        """Return the form"""
        form = QuestionForm(request)
        return jinja.render('add_question.html', request, form=form)


class Post(HTTPMethodView):
    decorators = [auth.login_required]

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
            await db.blog_fisica.post.update_one(
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
app.add_route(Questions.as_view(), '/admin/question')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7000, debug=True)
