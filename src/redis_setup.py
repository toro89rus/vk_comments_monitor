import redis


r = redis.Redis(host="localhost", db=1, port=6379, decode_responses=True)
