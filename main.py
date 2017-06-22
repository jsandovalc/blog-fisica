from sanic import Sanic
from sanic_jinja2 import SanicJinja2

app = Sanic(__name__)
jinja = SanicJinja2(app)

app.static('/static', './static')

@app.route("/")
async def index(request):
    return jinja.render('index.html', request)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
