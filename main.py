import asyncio
from sanic import Sanic
from sanic_jinja2 import SanicJinja2
from motor import motor_asyncio


app = Sanic(__name__)
jinja = SanicJinja2(app)



app.static('/static', './static')

@app.route("/")
async def index(request):
    return jinja.render('index.html', request)

@app.route("/post")
async def posts(request):
    return jinja.render('post.html', request)

@app.route("/post/<slug>")
async def post(request, slug):
    db = motor_asyncio.AsyncIOMotorClient('mongodb://127.0.0.1:27019')
    post = await db.blog_fisica.post.find_one({'slug': slug})
    return jinja.render('post.html', request, post=post)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
