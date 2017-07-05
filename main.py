import json
import pymongo
import wtforms
from sanic import Sanic
from sanic_jinja2 import SanicJinja2
from sanic_wtf import SanicForm
from motor import motor_asyncio


app = Sanic(__name__)
jinja = SanicJinja2(app)
db = None

app.config['WTF_CSRF_SECRET_KEY'] = 'the super secret'

app.static('/static', './static')


class PostForm(SanicForm):
    title = wtforms.StringField('Título', validators=[DataRequired()])
    subtitle = wtforms.StringField('Subtítulo')


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
    post['content'] = json.loads(post['content'])
    return jinja.render('post.html', request, post=post)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7000, debug=True)
