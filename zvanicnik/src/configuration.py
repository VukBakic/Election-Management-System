import os;
from datetime import timedelta;

redisUrl = os.environ["REDIS_HOST"];

class Configuration ( ):
    REDIS_HOST = redisUrl
    REDIS_VOTE_LIST = "votes";
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JSON_SORT_KEYS = False

