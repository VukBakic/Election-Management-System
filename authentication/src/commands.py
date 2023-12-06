
from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from .models import Role, User, UserRole


seedBlueprint = Blueprint('seed', __name__)
seedBlueprint.cli.short_help="Provides commands to populate database.";

@seedBlueprint.cli.command('generate')
def seed():
    """ Adds initial required data into database """
    database = SQLAlchemy()
    admin = Role(name='administrator')
    zvanicnik = Role(name='zvanicnik')
    database.session.add(admin)
    database.session.add(zvanicnik)
    database.session.commit()

    account0_info = {
        "jmbg": "000000000000",
        "forename": "admin",
        "surname": "admin",
        "email": "admin@admin.com",
        "password": "1"
    }
    account0= User(**account0_info)
    database.session.add(account0)
    database.session.commit()
    userRole = UserRole(userId=account0.id, roleId=1)
    database.session.add(userRole)
    database.session.commit()


    print("Seed successful. Database updated.")