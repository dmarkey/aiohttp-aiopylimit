import asynctest
import unittest
from aiohttp.web import Application, json_response, RouteTableDef
from aiopylimit import AIOPyRateLimit
from collections import UserDict

from aiohttp_aiopylimit.decorators import aiopylimit
from aiohttp_aiopylimit.limit import (AIOHTTPAIOPyLimit, REDIS_HOST_KEY,
                                      REDIS_PORT_KEY,
                                      REDIS_DB_KEY, REDIS_IS_SENTINAL_KEY,
                                      REDIS_PASSWORD_KEY)


class TestAIOHTTPAIOPyLimit(unittest.TestCase):

    def test_middleware_installed(self):
        app = Application()

        AIOHTTPAIOPyLimit.init_app(
            app, None, global_limit=(60, 60))

        self.assertEqual(app.middlewares[0].__name__,
                         'global_limit_middleware')


async def handler(request):
    return


class TestMiddleware(asynctest.TestCase):

    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=True)
    async def test_middleware_success(self, attempt, is_rate_limited):
        app = Application()
        app[REDIS_HOST_KEY] = 'remote-redis'

        AIOHTTPAIOPyLimit.init_app(
            app, None, global_limit=(60, 60))
        request = UserDict()
        request.remote = ''
        ret = await app.middlewares[0](request, handler)
        self.assertEqual(ret, None)
        attempt.assert_called_once_with(
            ('aiohttp-aiopylimit-pylimit_global-127.0.0.1'))
        is_rate_limited.assert_called_once_with(
            ('aiohttp-aiopylimit-pylimit_global-127.0.0.1'))

    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=True)
    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_middleware_limited(self, attempt, is_rate_limited):
        app = Application()

        AIOHTTPAIOPyLimit.init_app(
            app, None, global_limit=(60, 60))
        request = UserDict()
        request.remote = ''
        ret = await app.middlewares[0](request, handler)
        self.assertEqual(ret.status, 429)
        attempt.assert_not_called()
        is_rate_limited.assert_called_once_with(
            ('aiohttp-aiopylimit-pylimit_global-127.0.0.1'))

    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_middleware_just_over(self, attempt, is_rate_limited):
        app = Application()
        AIOHTTPAIOPyLimit.init_app(
            app, None, global_limit=(60, 60))
        request = UserDict()
        request.remote = ''
        ret = await app.middlewares[0](request, handler)
        self.assertEqual(ret.status, 429)
        is_rate_limited.assert_called_once_with(
            ('aiohttp-aiopylimit-pylimit_global-127.0.0.1'))
        attempt.assert_called_once_with(
            ('aiohttp-aiopylimit-pylimit_global-127.0.0.1'))

    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_middleware_success(self, attempt, is_rate_limited):
        app = Application()
        app[REDIS_HOST_KEY] = 'remote-redis'

        AIOHTTPAIOPyLimit.init_app(
            app, None, global_limit=(60, 60), key_func=lambda x: "temp")
        request = UserDict()
        request.remote = ''
        ret = await app.middlewares[0](request, handler)
        self.assertEqual(ret.status, 429)
        is_rate_limited.assert_called_once_with(
            ('aiohttp-aiopylimit-pylimit_global-temp'))
        attempt.assert_called_once_with(
            ('aiohttp-aiopylimit-pylimit_global-temp'))

    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_middleware_success(self, attempt, is_rate_limited):
        app = Application()

        AIOHTTPAIOPyLimit.init_app(
            app, None, global_limit=(60, 60), key_func=lambda x: "temp",
            global_namespace_prefix="testing")
        request = UserDict()
        request.remote = ''
        ret = await app.middlewares[0](request, handler)
        self.assertEqual(ret.status, 429)
        is_rate_limited.assert_called_once_with(
            'testing-pylimit_global-temp')
        attempt.assert_called_once_with('testing-pylimit_global-temp')


class TestDecorator(asynctest.TestCase):

    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=True)
    async def test_decorator_success(self, attempt, is_rate_limited):
        app = Application()

        routes = RouteTableDef()

        @routes.get("/")
        @aiopylimit("root_view", (60, 1))  # 1 per 60 seconds
        async def test(request):
            return json_response({"test": True})

        app.add_routes(routes)
        request = UserDict()
        request.app = UserDict()
        request.app['limit_global_namespace_prefix'] = "aiohttp"
        request.app['limit_key_func'] = lambda x: "key"
        request.app['limit_reached_view'] = None
        ret = await test(request)
        self.assertEqual(ret.status, 200)
        attempt.assert_called_once_with(
            'aiohttp-root_view-key')
        is_rate_limited.assert_called_once_with(
            'aiohttp-root_view-key')

    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=True)
    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=True)
    async def test_decorator_is_limited(self, attempt, is_rate_limited):
        app = Application()

        routes = RouteTableDef()

        @routes.get("/")
        @aiopylimit("root_view", (60, 1))  # 1 per 60 seconds
        async def test(request):
            return json_response({"test": True})

        async def test_view(request):
            return json_response("bad", status=429)

        app.add_routes(routes)
        request = UserDict()
        request.app = UserDict()
        request.app['limit_global_namespace_prefix'] = "aiohttp"
        request.app['limit_key_func'] = lambda x: "key"
        request.app['limit_reached_view'] = test_view
        ret = await test(request)
        self.assertEqual(ret.status, 429)
        attempt.assert_not_called()
        is_rate_limited.assert_called_once_with(
            'aiohttp-root_view-key')

    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_decorator_bad_attempt(self, attempt, is_rate_limited):
        app = Application()

        routes = RouteTableDef()

        @routes.get("/")
        @aiopylimit("root_view", (60, 1))  # 1 per 60 seconds
        async def test(request):
            return json_response({"test": True})

        app.add_routes(routes)

        async def test_view(request):
            return json_response("bad", status=429)

        request = UserDict()
        request.app = UserDict()
        request.app['limit_global_namespace_prefix'] = "aiohttp"
        request.app['limit_key_func'] = lambda x: "key"
        request.app['limit_reached_view'] = test_view
        ret = await test(request)
        self.assertEqual(ret.status, 429)
        attempt.assert_called_once_with(
            'aiohttp-root_view-key')
        is_rate_limited.assert_called_once_with(
            'aiohttp-root_view-key')

    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_decorator_custom_view(self, attempt, is_rate_limited):
        app = Application()
        routes = RouteTableDef()

        async def test_view(request):
            return json_response("bad", status=400)

        @routes.get("/")
        @aiopylimit("root_view", (60, 1),
                    limit_reached_view=test_view)
        async def test(request):
            return json_response({"test": True})

        app.add_routes(routes)

        async def test_view2(request):
            return json_response("bad", status=429)

        request = UserDict()
        request.app = UserDict()
        request.app['limit_global_namespace_prefix'] = "aiohttp"
        request.app['limit_key_func'] = lambda x: "key"
        request.app['limit_reached_view'] = test_view2
        ret = await test(request)
        self.assertEqual(ret.status, 400)
        attempt.assert_called_once_with(
            'aiohttp-root_view-key')
        is_rate_limited.assert_called_once_with(
            'aiohttp-root_view-key')

    @asynctest.patch("aiohttp_aiopylimit.decorators.AIOPyRateLimit",
                     return_value=asynctest.MagicMock(
                         is_rate_limited=asynctest.CoroutineMock(
                             return_value=True)))
    async def test_decorator_limiter_called_correctly(self, limit_class):
        app = Application()
        routes = RouteTableDef()

        async def test_view(request):
            return json_response("bad", status=400)

        async def test_view2(request):
            return json_response("bad", status=429)

        @routes.get("/")
        @aiopylimit("root_view", (60, 1),
                    limit_reached_view=test_view)
        async def test(request):
            return json_response({"test": True})

        app.add_routes(routes)

        request = UserDict()
        request.app = UserDict()
        request.app['limit_global_namespace_prefix'] = "aiohttp"
        request.app['limit_key_func'] = lambda x: "key"
        request.app['limit_reached_view'] = test_view2

        ret = await test(request)
        limit_class.assert_called_once_with(60, 1)
        self.assertEqual(ret.status, 400)

    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.is_rate_limited",
                     return_value=False)
    @asynctest.patch("aiohttp_aiopylimit.limit.AIOPyRateLimit.attempt",
                     return_value=False)
    async def test_decorator_class_based(self, attempt, is_rate_limited):
        async def test_view(request):
            return json_response("bad", status=400)

        class TestClass(object):
            @aiopylimit("root_view", (60, 1),
                        limit_reached_view=test_view)
            async def test(self, request):
                return json_response({"test": True})

        async def test_view2(request):
            return json_response("bad", status=429)

        request = UserDict()
        request.app = UserDict()
        request.app['limit_global_namespace_prefix'] = "aiohttp"
        request.app['limit_key_func'] = lambda x: "key"
        request.app['limit_reached_view'] = test_view2
        obj = TestClass()
        obj.request = request
        ret = await obj.test(request)
        self.assertEqual(ret.status, 400)
        attempt.assert_called_once_with(
            'aiohttp-root_view-key')
        is_rate_limited.assert_called_once_with(
            'aiohttp-root_view-key')
