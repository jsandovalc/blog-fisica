from sqlite3 import IntegrityError
from slugify import UniqueSlugify
import databases
import datetime as dt
from fastapi import FastAPI, Request, Form, status
from fastapi.templating import Jinja2Templates
import sqlalchemy as sa
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

DATABASE_URL = "sqlite:///./blog.db"

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
database = databases.Database(DATABASE_URL)
metadata = sa.MetaData()


posts = sa.Table(
    "posts",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("title", sa.String, nullable=False),
    sa.Column("subtitle", sa.String),
    sa.Column("slug", sa.String, nullable=False, unique=True),
    sa.Column("draft", sa.Boolean, nullable=False),
    sa.Column("content", sa.Text, nullable=False),
    sa.Column("publish_date", sa.DateTime, default=dt.datetime.utcnow),
)

engine = sa.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata.create_all(engine)


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin/post/")
def add_post_form(request: Request):
    return templates.TemplateResponse("add_post.html", {"request": request})


@app.post("/admin/post/")
async def add_post(
    request: Request,
    title: str = Form(...),
    subtitle: str = Form(...),
    draft: bool = Form(False),
    content: str = Form(...),
):
    slugify = UniqueSlugify()

    while True:
        query = posts.insert().values(
            title=title,
            subtitle=subtitle,
            draft=draft,
            content=content,
            slug=slugify(title, to_lower=True),
        )
        try:
            await database.execute(query)
        except IntegrityError:
            continue

        break

    # TODO: Maybe redirect to newly created post
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/about/")
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/contact/")
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})
