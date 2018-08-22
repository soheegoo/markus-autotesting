import autotest_server

REDIS_PASSWORD = autotest_server.get_redis_password().get('password', '')
