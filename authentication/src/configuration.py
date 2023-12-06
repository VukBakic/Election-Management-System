import os;
from datetime import timedelta;

databaseUrl = os.environ["DATABASE_URL"];

class Configuration ( ):
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseUrl}/authentication";
    SQLALCHEMY_TRACK_MODIFICATIONS = False;
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60);
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30);
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JSON_SORT_KEYS = False