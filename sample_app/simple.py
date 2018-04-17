from aiohttp import web


from aiohttp_aiopylimit.decorators import aiopylimit
from aiohttp_aiopylimit.limit import AIOHTTPAIOPyLimit

# Initialise the AIOHTTP app
app = web.Application()
routes = web.RouteTableDef()


# Add a view that will have the global limit applied
@routes.get("/")
async def test(request):
    return web.json_response({"test": True})


# Use this function to generate a custom limit key based on the request input
# This has to be synchronous
def custom_key(request) -> str:
    return "something"


# A custom view to return. This has to be asynchronous
async def custom_view(request):
    return web.json_response("bad", status=400)


# Sample simple view
@routes.get("/write")
@aiopylimit("write_api", (60, 1), key_func=custom_key,
            limit_reached_view=custom_view)  # 1 per 60 seconds
async def test(request):
    return web.json_response({"test": True})


# Sample simple view
@routes.get("/write2")
@aiopylimit("write_api2", (60, 1))  # 1 per 60 seconds
async def test(request):
    return web.json_response({"test": True})

# Local redis host
app['AIOHTTP_AIOPYRATELIMIT_REDIS_HOST'] = "localhost"

app.add_routes(routes)

# Initialise the app
AIOHTTPAIOPyLimit.init_app(app, global_limit=(10, 10))  # 10 per 10 seconds

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8001)
