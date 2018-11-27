"""This file is dangerous. It must not include real connection data in git."""
import json
import arrow
import psycopg2

posts = json.loads(open('/home/ark/posts.json').read())

conn = psycopg2.connect("dbname=blog_fisica host=127.0.0.1 user=arquimedes password=arquimedes123")

cur = conn.cursor()

cur.execute("DELETE FROM tags_posts")
cur.execute("DELETE FROM posts")
cur.execute("DELETE FROM tags")
conn.commit()

for post in posts:
    title = post['title']
    subtitle = post['subtitle']
    slug = post['slug']
    draft = post['draft']

    content = post['content']

    publish_date = arrow.get(post['publish_date']['$date']).datetime

    tags = post['tags']

    cur.execute("INSERT INTO posts (title, subtitle, slug, draft, content, publish_date) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id", (title, subtitle, slug, draft, content, publish_date))
    new_post = cur.fetchone()[0]
    conn.commit()
    for tag in tags:
        cur.execute("SELECT * FROM tags WHERE title=%s", (tag,))

        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO tags (title) VALUES (%s) RETURNING id", (tag,))
            new_tag = cur.fetchone()[0]

        cur.execute("INSERT INTO tags_posts (tag, post) VALUES (%s, %s)", (new_tag, new_post))
        conn.commit()
