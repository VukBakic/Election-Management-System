import os;
from datetime import timedelta;

databaseUrl = os.environ["DATABASE_URL"];

class Configuration ( ):
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseUrl}/elections";
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = 18000
    JSON_SORT_KEYS = False