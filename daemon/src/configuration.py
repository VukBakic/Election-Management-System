import os;

databaseUrl = os.environ["DATABASE_URL"];
redisUrl = os.environ["REDIS_HOST"];


class Configuration ( ):
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseUrl}/elections"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_HOST = redisUrl
    REDIS_VOTE_LIST = "votes"


