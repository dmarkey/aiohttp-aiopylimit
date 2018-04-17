from aiohttp.web import json_response, middleware
from aiopylimit.aiopyratelimit import AIOPyRateLimit

REDIS_HOST_KEY = "AIOHTTP_AIOPYRATELIMIT_REDIS_HOST"
REDIS_PORT_KEY = "AIOHTTP_AIOPYRATELIMIT_REDIS_PORT"
REDIS_DB_KEY = "AIOHTTP_AIOPYRATELIMIT_REDIS_DB"
REDIS_PASSWORD_KEY = "AIOHTTP_AIOPYRATELIMIT_PASSWORD_DB"
REDIS_IS_SENTINAL_KEY = "AIOHTTP_AIOPYRATELIMIT_IS_SENTINAL"


def default_key_func(request):
    if request.remote:
        return request.remote
    return "127.0.0.1"


def create_default_view(status_code=429):
    async def view(request):
        return json_response("Limit reached, try again later.",
                             status=status_code)
    return view


class AIOHTTPAIOPyLimit(object):
    @classmethod
    def init_app(cls, app, limit_reached_view=None,
                 limit_reached_http_code=429, global_limit=None,
                 global_limit_namespace="pylimit_global",
                 global_namespace_prefix="aiohttp-aiopylimit",
                 key_func=default_key_func):
        if REDIS_HOST_KEY not in app:
            raise ValueError("Need a redis server host defined")

        if limit_reached_http_code != 429 and limit_reached_view is not None:
            raise ValueError("Please implement the "
                             "limit_reached_http_code in your custom view.")

        if limit_reached_view is None:
            limit_reached_view = create_default_view(limit_reached_http_code)

        redis_host = app[REDIS_HOST_KEY]
        redis_port = int(app.get(REDIS_PORT_KEY, 6379))
        redis_db = int(app.get(REDIS_DB_KEY, 1))
        is_sentinal_redis = bool(app.get(REDIS_IS_SENTINAL_KEY, 0))
        redis_password = app.get(REDIS_PASSWORD_KEY, None)

        app['limit_key_func'] = key_func
        app['limit_reached_view'] = limit_reached_view
        app['limit_global_namespace_prefix'] = global_namespace_prefix

        AIOPyRateLimit.init(
            redis_host=redis_host,
            redis_port=redis_port,
            db=redis_db,
            is_sentinel_redis=is_sentinal_redis,
            redis_password=redis_password,
            force_new_connection=True)

        if global_limit is not None:
            global_limiter = AIOPyRateLimit(*global_limit)

            @middleware
            async def global_limit_middleware(request, handler):
                key = key_func(request)
                full_key = f'{global_namespace_prefix}-' \
                           f'{global_limit_namespace}-{key}'
                if await global_limiter.is_rate_limited(full_key) \
                        or not await global_limiter.attempt(full_key):
                    return await limit_reached_view(request)
                return await handler(request)

            app.middlewares.append(global_limit_middleware)
