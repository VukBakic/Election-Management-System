from flask import Flask, jsonify, request,  Response
from flask_jwt_extended import jwt_required, get_jwt
from functools import wraps
from .configuration import Configuration
from redis import Redis
from flask_jwt_extended import JWTManager
import io
import csv
import json
import time


def required_role(role):
    def decorator(fn):
        @jwt_required()
        @wraps(fn)
        def wrapper(*args, **kwargs):
            jwtData = get_jwt()
            roles = jwtData["roles"]
            if role in roles:
                return fn(*args, **kwargs)
            return jsonify({"message": "Access denied"}), 403

        return wrapper

    return decorator


def create_app():
    application = Flask(__name__)
    application.config.from_object(Configuration)

    connected=False
    while not connected:
        with Redis(host=Configuration.REDIS_HOST) as redis:
            try:
                redis.ping()
                connected = True
            except Exception as e:
                print(e)
                time.sleep(10)

    @application.route("/vote", methods=["POST"])
    @required_role("zvanicnik")
    def vote():
        if "file" not in request.files:
            return jsonify({"message": "Field file is missing."}), 400

        content = request.files["file"].stream.read().decode("utf-8");
        stream = io.StringIO(content);
        reader = csv.reader(stream);
        jwtData = get_jwt()

        votes = [];

        for index, row in enumerate(reader):
            try :
                if len(row) != 2:
                    return jsonify({"message": "Incorrect number of values on line {}.".format(index)}), 400
                if int(row[1]) <= 0:
                    return jsonify({"message": "Incorrect poll number on line {}.".format(index)}), 400
                vote = {
                    "GUID": row[0],
                    "pollNumber": int(row[1]),
                    "electionOfficialJmbg": jwtData["jmbg"]
                }
                votes.append(vote)
            except (IndexError, ValueError) as e:
                if(type(e)==ValueError):
                    return jsonify({"message": "Incorrect poll number on line {}.".format(index)}), 400
                return jsonify({"message": "Incorrect number of values on line {}.".format(index)}), 400

        for v in votes:
            with Redis(host=Configuration.REDIS_HOST) as redis:
                redis.rpush(Configuration.REDIS_VOTE_LIST, json.dumps(v));

        return Response(status=200)
    # end of routes

    jwt = JWTManager(application)
    return application
