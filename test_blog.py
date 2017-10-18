import pytest
import mongomock
import motor
from main import build_app

# Tests are not currently working.


@pytest.yield_fixture
def app(monkeypatch):
    monkeypatch.setattr("motor.MotorClient.__delegate_class__",
                        mongomock.MongoClient)
    return build_app()


@pytest.fixture
def test_cli(loop, app, test_client):
    return loop.run_until_complete(test_client(app))


async def test_post_collition(test_cli):
    """If the name is already used, it must create a different post
    anyway without overwriting.

    """
    resp = await test_cli.get('/admin/post')

    assert resp.status == 200
