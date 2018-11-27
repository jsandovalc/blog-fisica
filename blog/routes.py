import pathlib
from . import views

PROJECT_ROOT = pathlib.Path(__file__).parent.parent


def setup_routes(app):
    app.router.add_get('/', views.index, name='index')
    # app.router.add_get('/login', views.login, name='login')
    # app.router.add_get('/logout', views.login, name='logout')
    # app.router.add_get('/post', views.login, name='posts')
    app.router.add_get('/post/{slug}', views.post, name='post')
    # app.router.add_get('/admin/post/{slug}', views.login, name='post')
    app.router.add_get('/about', views.about, name='about')
    app.router.add_get('/contact', views.contact, name='contact')
    app.router.add_post('/contact', views.post_contact, name='post-contact')

    setup_static_routes(app)


def setup_static_routes(app):
    """Main static files."""
    print('root', PROJECT_ROOT / 'static')
    print('static route', PROJECT_ROOT / 'static')
    app.router.add_static('/static/', path=PROJECT_ROOT / 'static',
                          name='static')
