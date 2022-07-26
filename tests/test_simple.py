from asyncio import sleep
import pytest

from sample_app.simple import app


@pytest.fixture
def cli(loop, aiohttp_client):
    return loop.run_until_complete(aiohttp_client(app))


@pytest.mark.asyncio
async def test_throttling_simple_app(cli):
    response = await cli.get('/write')
    assert response.status == 200
    response = await cli.get('/write')
    assert response.status == 400
    response = await cli.get('/write2')
    assert response.status == 200
    response = await cli.get('/write2')
    assert response.status == 429
    for x in range(0, 6):
        response = await cli.get('/')
        assert response.status == 200
    response = await cli.get('/')
    assert response.status == 429
    await sleep(10)
    response = await cli.get('/')
    assert response.status == 200


