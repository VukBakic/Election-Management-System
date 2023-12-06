import sys

from flask import Blueprint, request, Response, jsonify;
from marshmallow import Schema, fields, ValidationError, validate
from functools import wraps
from .models import database, Participant;


from flask_jwt_extended import jwt_required, get_jwt;


participantsBlueprint = Blueprint("participants", __name__)


class CreateSchema(Schema):
   class Meta:
      ordered = True
   name = fields.String(
      validate=validate.Length(max=256, error="Invalid name."),
      required=True,
      error_messages={"required": "Field name is missing."}
   )
   individual=fields.Boolean(
      required=True,
      error_messages={"required": "Field individual is missing.", "invalid":"Invalid field individual."}
   )


def missing(field: str):
    return f"Field {field} is missing."

def required_params(schema):
   def decorator(fn):

      @wraps(fn)
      def wrapper(*args, **kwargs):
         try:
            data = request.get_json() or {}
            for field in schema.fields:
               if field in data:
                  if type(data[field]) is str:
                     if not data[field] or len(data[field]) == 0:
                        return jsonify({"message": missing(field)}), 400
               else:
                  return jsonify({"message": missing(field)}), 400
            schema.load(request.get_json() or {})
         except ValidationError as err:

            error = {
               "message": err.messages[next(iter(err.messages))][0]
            }
            return jsonify(error), 400
         return fn(*args, **kwargs)

      return wrapper

   return decorator

def required_role(role):
   def decorator(fn):

      @jwt_required()
      @wraps(fn)
      def wrapper(*args, **kwargs):
         jwtData = get_jwt()
         roles = jwtData["roles"]
         if role in roles:
            return fn(*args, **kwargs)
         return  jsonify({"message":"Access denied"}), 403

      return wrapper

   return decorator

@participantsBlueprint.route("/createParticipant", methods=["POST"])
@required_role("administrator")
@required_params(CreateSchema())
def createParticipant():
   jsonObject = request.get_json()
   user = Participant(**request.get_json())
   database.session.add(user)
   database.session.commit();
   if user.id :
      return jsonify({"id": user.id}), 200
   return jsonify({"message": "Error occurred"}), 400

@participantsBlueprint.route("/getParticipants", methods=["GET"])
@required_role("administrator")
def getParticipants():
   users = Participant.query.all()
   return jsonify({"participants": list(map(lambda a: a.as_dict(), users))}), 200


