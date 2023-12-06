from flask import Flask
from flask_migrate import Migrate, upgrade
from .configuration import Configuration
from sqlalchemy_utils import database_exists, create_database
from .participants import participantsBlueprint
from .elections import electionsBlueprint
from flask_jwt_extended import JWTManager
import time

from .models import *


def create_app():
    application = Flask(__name__)
    application.config.from_object(Configuration)

    application.register_blueprint(participantsBlueprint)
    application.register_blueprint(electionsBlueprint)

    database.init_app(application)

    connected = False
    while not connected:
        try:
            if not database_exists(Configuration.SQLALCHEMY_DATABASE_URI):
                create_database(Configuration.SQLALCHEMY_DATABASE_URI)
            migrate = Migrate(application, database)
            with application.app_context():
                upgrade()
            connected = True
        except Exception as e:
            print(e)
            time.sleep(10)
            continue

    jwt = JWTManager(application)

    return application
