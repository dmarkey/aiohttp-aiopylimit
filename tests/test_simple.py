from asyncio import sleep

from sample_app.simple import app


async def test_throttling_simple_app(test_client):
    client = await test_client(app)
    response = await client.get('/write')
    assert response.status == 200
    response = await client.get('/write')
    assert response.status == 400
    response = await client.get('/write2')
    assert response.status == 200
    response = await client.get('/write2')
    assert response.status == 429
    for x in range(0, 6):
        response = await client.get('/')
        assert response.status == 200
    response = await client.get('/')
    assert response.status == 429
    await sleep(10)
    response = await client.get('/')
    assert response.status == 200


