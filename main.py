import locale
from pathlib import Path
import asyncio
import asyncio_redis
import pymongo
import shortuuid
import wtforms
import aiosmtplib
import config
from email.mime.text import MIMEText
from wtforms import validators
from sanic import Sanic, response
from sanic.views import HTTPMethodView
from sanic_jinja2 import SanicJinja2
from sanic_wtf import SanicForm, FileAllowed
from sanic_auth import Auth, User
from sanic_session import RedisSessionInterface
from motor import motor_asyncio
from slugify import slugify
from delorean import Delorean



class Redis:
    """A simple wrapper class that allows you to share a connection pool
    across your application.

    Taken from: https://pythonhosted.org/sanic_session/using_the_interfaces.html

    """
    _pool = None

    async def get_redis_pool(self):
        if not self._pool:
            self._pool = await asyncio_redis.Pool.create(
                host='localhost', port=6379, poolsize=10
            )

        return self._pool

def build_app():
    locale.setlocale(locale.LC_TIME, 'es_CO.utf8')
    app = Sanic(__name__)
    db = None

    app.config.WTF_CSRF_SECRET_KEY = 'the super secret'
    app.config.AUTH_LOGIN_ENDPOINT = 'login'

    app.static('/static', './static')

    auth = Auth(app)
    jinja = SanicJinja2(app)

    redis = Redis()
    # pass the getter method for the connection pool into the session
    session_interface = RedisSessionInterface(redis.get_redis_pool)

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

    @app.middleware('request')
    async def add_session_to_request(request):
        # before each request initialize a session
        # using the client's request
        await session_interface.open(request)


    @app.middleware('response')
    async def save_session(request, response):
        # after each request save the session,
        # pass the response to set client cookies
        await session_interface.save(request, response)
        session = {}

    # @app.middleware('request')
    # async def add_session(request):
    #     request['session'] = session

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
        nonlocal db
        db = motor_asyncio.AsyncIOMotorClient('mongodb://127.0.0.1:27017')

    app.add_task(setup_db())

    @app.route("/")
    async def index(request):
        posts = await db.blog_fisica.post.find(
            dict(draft=False, publish_date={
                '$lte': Delorean().datetime})).sort(
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
    @auth.login_required
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

    @app.get("/contact/")
    async def contact(request):
        """Return the contact form."""
        return jinja.render("contact.html", request)

    @app.post("/contact/")
    async def post_contact(request):
        print('posting', request.form)
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
            request.form.get('name') + '\n\n' +
            request.form.get('message') + '\n\n' +
            ','.join(request.form['email']))
        message['From'] = user
        message['To'] = user
        message['Subject'] = 'Mensaje recibido en el blog de Arquímedes'

        await server.send_message(message)

        return response.json({'message': 'Mail sent'}, status=201)

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
            return jinja.render('add_post.html', request, form=form,
                                action='Crear')

        async def post(self, request):
            """Save the post."""
            form = PostForm(request)

            if form.validate_on_submit():
                slug = slugify(form.title.data)

                post = await db.blog_fisica.post.find_one(dict(slug=slug))

                suffix = 0
                while post:
                    slug = slugify(f'{form.title.data}-{suffix}')
                    post = await db.blog_fisica.post.find_one(dict(slug=slug))
                    suffix += 1

                await db.blog_fisica.post.insert_one(dict(
                    title=form.title.data,
                    subtitle=form.subtitle.data,
                    publish_date=Delorean(
                        form.publish_date.data, 'UTC').datetime,
                    slug=slug,
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
            post['tags'] = ', '.join(post['tags'])
            form = PostForm(request, **post)
            return jinja.render('edit_post.html', request, form=form,
                                action="Actualizar", post=post)

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
                        tags=get_tags_list(form.tags.data)
                    )
                    })

                return response.redirect(app.url_for('post', slug=slug))

            return response.redirect('/404')

    class ImageForm(SanicForm):
        image = wtforms.fields.FileField('Imagen', validators=[
            FileAllowed('jpg bpm png jpeg jpg gif'.split())])
        submit = wtforms.SubmitField('Subir')

    class Image(HTTPMethodView):
        """Allow image uploading."""
        decorators = [auth.login_required]

        async def get(self, request):
            """Return the upload image form."""
            return jinja.render('upload_image.html', request,
                                form=ImageForm(request))

        async def post(self, request):
            """Store the image in img uploads directory."""
            form = ImageForm(request)

            if form.validate_on_submit():
                image = form.image.data

                # MUST NOT trust path.
                uploaded_file = (Path('./static/uploads/img') /
                                 f'{shortuuid.uuid()}-{image.name}')
                uploaded_file.write_bytes(image.body)

                return response.redirect('/admin')

            return response.redirect('/admin/image')

    app.add_route(Posts.as_view(), '/admin/post')
    app.add_route(Post.as_view(), '/admin/post/<slug>')
    app.add_route(Questions.as_view(), '/admin/question')
    app.add_route(Image.as_view(), '/admin/image')

    return app


if __name__ == '__main__':
    build_app().run(host="0.0.0.0", port=7000, debug=True)
