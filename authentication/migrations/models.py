from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class UserRole(database.Model):
    __tablename__ = "userrole";

    id = database.Column(database.Integer, primary_key=True);
    userId = database.Column(database.Integer, database.ForeignKey("users.id"), nullable=False);
    roleId = database.Column(database.Integer, database.ForeignKey("roles.id"), nullable=False);


class User(database.Model):
    __tablename__ = "users";

    id = database.Column(database.Integer, primary_key=True);
    email = database.Column(database.String(256), nullable=False, unique=True);
    password = database.Column(database.String(256), nullable=False);
    forename = database.Column(database.String(256), nullable=False);
    surname = database.Column(database.String(256), nullable=False);
    jmbg = database.Column(database.String(13), nullable=False, unique=True);

    roles = database.relationship("Role", secondary=UserRole.__table__, back_populates="users");

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        import bcrypt
        self.password=bcrypt.hashpw(kwargs.get("password").encode('utf-8'), bcrypt.gensalt())



class Role(database.Model):
    __tablename__ = "roles";

    id = database.Column(database.Integer, primary_key=True);
    name = database.Column(database.String(256), nullable=False);

    users = database.relationship("User", secondary=UserRole.__table__, back_populates="roles");

    def __repr__(self):
        return self.name;
