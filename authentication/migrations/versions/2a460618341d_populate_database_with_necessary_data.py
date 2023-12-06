"""Populate sa with necessary data.

Revision ID: 2a460618341d
Revises: a2fff7262f81
Create Date: 2021-06-26 00:02:47.772791

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base



# revision identifiers, used by Alembic.
revision = '2a460618341d'
down_revision = 'a2fff7262f81'
branch_labels = None
depends_on = None

Base = declarative_base()

class UserRole(Base):
    __tablename__ = "userrole";

    id = sa.Column(sa.Integer, primary_key=True);
    userId = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False);
    roleId = sa.Column(sa.Integer, sa.ForeignKey("roles.id"), nullable=False);

class User(Base):
    __tablename__ = "users";

    id = sa.Column(sa.Integer, primary_key=True);
    email = sa.Column(sa.String(256), nullable=False, unique=True);
    password = sa.Column(sa.String(256), nullable=False);
    forename = sa.Column(sa.String(256), nullable=False);
    surname = sa.Column(sa.String(256), nullable=False);
    jmbg = sa.Column(sa.String(13), nullable=False, unique=True);

    roles = orm.relationship("Role", secondary=UserRole.__table__, back_populates="users");

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        import bcrypt
        self.password=bcrypt.hashpw(kwargs.get("password").encode('utf-8'), bcrypt.gensalt())

class Role(Base):
    __tablename__ = "roles";

    id = sa.Column(sa.Integer, primary_key=True);
    name = sa.Column(sa.String(256), nullable=False);

    users = orm.relationship("User", secondary=UserRole.__table__, back_populates="roles");

    def __repr__(self):
        return self.name;


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    admin = Role(name='administrator')
    zvanicnik = Role(name='zvanicnik')

    session.add(admin)
    session.add(zvanicnik)
    session.commit()

    account0_info = {
        "jmbg": "0000000000000",
        "forename": "admin",
        "surname": "admin",
        "email": "admin@admin.com",
        "password": "1"
    }
    account0 = User(**account0_info)
    session.add(account0)
    session.commit()
    userRole = UserRole(userId=account0.id, roleId=1)
    session.add(userRole)
    session.commit()

def downgrade():
    pass
