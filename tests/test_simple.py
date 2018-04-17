from time import sleep

from sample_app.simple import app


def test_throttling_simple_app():
    request, response = app.test_client.get('/write')
    assert response.status == 200
    request, response = app.test_client.get('/write')
    assert response.status == 400
    request, response = app.test_client.get('/simpleview')
    assert response.status == 200
    request, response = app.test_client.get('/simpleview')
    assert response.status == 429
    request, response = app.test_client.get('/write2')
    assert response.status == 200
    request, response = app.test_client.get('/write2')
    assert response.status == 429
    for x in range(0, 4):
        request, response = app.test_client.get('/')
        assert response.status == 200
    request, response = app.test_client.get('/')
    assert response.status == 429
    sleep(10)
    request, response = app.test_client.get('/')
    assert response.status == 200


