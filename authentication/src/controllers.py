import sys

from flask import Blueprint, request, Response, jsonify;
from marshmallow import Schema, fields, validates, ValidationError, validate, validates_schema, post_load
from functools import wraps
from .models import database, User, UserRole
from flask_jwt_extended import create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity;
from sqlalchemy import exc
from datetime import timedelta;


def non_empty(check: str):
    return len(check) != 0


def missing(field: str):
    return f"Field {field} is missing."


class UserSchema(Schema):
    class Meta:
        ordered = True

    jmbg = fields.String(
        validate=[non_empty],
        required=True,
        error_messages={"required": missing('jmbg'), "validator_failed": missing('jmbg')}
    )

    forename = fields.String(
        validate=[non_empty, validate.Length(max=256, error="Invalid forename.")],
        required=True,
        error_messages={"required": missing('forename'), "validator_failed": missing('forename')}
    )
    surname = fields.String(
        validate=[non_empty, validate.Length(max=256, error="Invalid surname.")],
        required=True,
        error_messages={"required": missing('surname'), "validator_failed": missing('surname')}
    )

    email = fields.Email(
        validate=[
            non_empty,
            validate.Length(max=256, error="Invalid email."),
            validate.Length(max=256, error="Invalid email.")
        ],
        required=True,
        error_messages={
            "required": missing('email'),
            "invalid": "Invalid email.",
            "validator_failed": missing('email')
        }
    )
    password = fields.String(

        validate=[
            non_empty,
            validate.Regexp(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$", error="Invalid password.")
        ],
        required=True,
        error_messages={"required": missing('password'), "validator_failed": missing('password')}
    )

    @validates('jmbg')
    def validate_jmbg(self, value):
        if len(value) == 0:
            raise ValidationError("Field jmbg is missing.")
        if len(value) != 13 or not value.isdigit():
            raise ValidationError("Invalid jmbg.")



        dd = value[0:2]
        mm = value[2:4]
        yyy = value[4:7]
        rr = value[7:9]
        bbb = value[9:12]
        k = value[12:13]


        if int(dd) not in range(1, 32):
            raise ValidationError("Invalid jmbg.")
        if int(mm) not in range(1, 13):
            raise ValidationError("Invalid jmbg.")
        if int(rr) not in range(70, 100):
            raise ValidationError("Invalid jmbg.")

        l = 11 - ((7 * (int(value[0]) + int(value[6])) + 6 * (int(value[1]) + int(value[7])) + 5 * (
                int(value[2]) + int(value[8])) + 4 * (int(value[3]) + int(value[9])) + 3 * (
                           int(value[4]) + int(value[10])) + 2 * (int(value[5]) + int(value[11]))) % 11)

        if int(l) not in range(1, 10):
            l = 0
        if int(k) != l:
            raise ValidationError("Invalid jmbg.")


class LoginSchema(Schema):
    class Meta:
        ordered = True

    email = fields.Email(
        validate=[
            non_empty,
            validate.Length(max=256, error="Invalid email."),
            validate.Length(max=256, error="Invalid email.")
        ],
        required=True,
        error_messages={
            "required": missing('email'),
            "validator_failed": missing('email'),
            "invalid": "Invalid email."
        }
    )
    password = fields.String(
        validate=non_empty,
        required=True,
        error_messages={"required": missing('password'), "validator_failed": missing('password')}
    )

    @post_load
    def check_empty(self, item, many, **kwargs):
        if not non_empty(item["email"]):
            raise ValidationError(missing('email'))
        if not non_empty(item["password"]):
            raise ValidationError(missing('password'))


class DeleteSchema(Schema):
    email = fields.Email(
        validate=[
            non_empty,
            validate.Length(max=256, error="Invalid email."),
            validate.Length(max=256, error="Invalid email.")],
        required=True,
        error_messages={
            "required": missing('email'),
            "invalid": "Invalid email.",
            "validator_failed": missing('email')
        }
    )


def required_params(schema):
    def decorator(fn):

        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json() or {}
                for field in schema.fields:
                    if field in data:
                        if not data[field] or len(data[field]) == 0:
                            return jsonify({"message": missing(field)}), 400
                    else:
                        return jsonify({"message": missing(field)}), 400
                schema.load(data)
            except ValidationError as err:

                error = {
                    "message": err.messages["jmbg"][0] if 'jmbg' in err.messages else
                    err.messages[next(iter(err.messages))][0]
                }
                return jsonify(error), 400
            return fn(*args, **kwargs)

        return wrapper

    return decorator


controllersBlueprint = Blueprint("controllers", __name__)


@controllersBlueprint.route("/register", methods=["POST"])
@required_params(UserSchema())
def register():
    jsonObject = request.get_json()
    user = User(**request.get_json())
    try:
        database.session.add(user)
        database.session.commit()
        userRole = UserRole(userId=user.id, roleId=2)
        database.session.add(userRole)
        database.session.commit()
    except exc.IntegrityError as e:
        print(e)
        return jsonify({"message": "Email already exists."}), 400
    return Response(status=200)


@controllersBlueprint.route("/login", methods=["POST"])
@required_params(LoginSchema())
def login():
    user = User.query.filter(User.email == request.json.get("email")).first()
    if user:
        import bcrypt
        if bcrypt.checkpw(request.get_json().get("password").encode('utf-8'), user.password.encode('utf-8')):
            jwtData = {
                "forename": user.forename,
                "surname": user.surname,
                "jmbg": user.jmbg,
                "roles": [str(role) for role in user.roles]
            }
            accessToken = create_access_token(
                identity=user.email,
                additional_claims=jwtData
            )
            refreshToken = create_refresh_token(
                identity=user.email,
                additional_claims=jwtData
            )
            return jsonify(accessToken=accessToken, refreshToken=refreshToken), 200
    return jsonify({"message": "Invalid credentials."}), 400


@controllersBlueprint.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    jwtData = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"],
        "jmbg": refreshClaims["jmbg"]
    }

    return jsonify(accessToken=create_access_token(
        identity=identity,
        additional_claims=jwtData,
        expires_delta=timedelta(minutes=60)
    )), 200


@controllersBlueprint.route("/delete", methods=["POST"])
@jwt_required()
@required_params(DeleteSchema())
def delete():
    jwtData = get_jwt()
    roles = jwtData["roles"]
    if "administrator" in roles:
        user = User.query.filter(User.email == request.json.get("email")).first()

        if user:
            if "administrator" not in user.roles:
                database.session.delete(user)
                database.session.commit()
                return Response(status=200)
    return jsonify({"message": "Unknown user."}), 400
