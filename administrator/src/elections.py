import functools
import sys
import datetime
from flask import Blueprint, request, Response, jsonify
from marshmallow import Schema, fields, ValidationError, INCLUDE
from functools import wraps
from .models import database, Participant, Election, ElectionParticipant, Vote
from flask.json import JSONEncoder
from sqlalchemy import or_, and_, func
from flask_jwt_extended import jwt_required, get_jwt
import re
from dateutil  import parser


match_iso8601 = re.compile(r'^(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d\.\d+)|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d)|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d)$').match


def validate_iso8601(str_val):
    try:
        if match_iso8601( str_val ) is not None:
            return True
    except:
        pass
    return False


electionsBlueprint = Blueprint("elections", __name__)


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


electionsBlueprint.json_encoder = CustomJSONEncoder


class ElectionSchema(Schema):
    class Meta:
        unknown = INCLUDE
        ordered = True

    start = fields.String(
        required=True,
        error_messages={"required": "Field start is missing."}
    )
    end = fields.String(
        required=True,
        error_messages={"required": "Field end is missing."}
    )
    individual = fields.Boolean(
        required=True,
        error_messages={"required": "Field individual is missing.", "invalid": "Invalid field individual."}
    )
    #participants = fields.List(
    #    cls_or_instance=fields.Integer(
    #        error_messages={"invalid": "Invalid field participants."}
    #    ),
    #    required=True,
    #    error_messages={"required": "Field participants is missing.", "invalid": "Invalid field participants."}
    #)

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
                if type(err.messages[next(iter(err.messages))]) == dict:
                    temp = err.messages[next(iter(err.messages))]

                    error = {
                        "message": temp[next(iter(temp))][0]
                    }
                else:
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
            return jsonify({"message": "Access denied"}), 403

        return wrapper

    return decorator





@electionsBlueprint.route("/getElections", methods=["GET"])
@required_role("administrator")
def getElections():
    elections = Election.query.all()
    return jsonify({"elections": elections}), 200


@electionsBlueprint.route("/createElection", methods=["POST"])
@required_role("administrator")
@required_params(ElectionSchema())
def createElection():
    participantsJson  = request.json.get("participants")
    if participantsJson is None:
        return jsonify({"message": "Field participants is missing."}), 400


    start = request.json.get("start")
    end = request.json.get("end")
    if not validate_iso8601(start) or not validate_iso8601(end):
        return jsonify({"message": "Invalid date and time."}), 400

    startBeforeEnd = start < end
    if not startBeforeEnd:
        return jsonify({"message": "Invalid date and time."}), 400


    dates = Election.query.filter(
        or_(
            Election.start.between(start, end),
            Election.end.between(start, end)
        )
    )


    if dates.scalar() is None:

        if len(participantsJson) < 2:
            return jsonify({"message": "Invalid participants."}), 400
        participantsSql = Participant.query.filter(Participant.id.in_(participantsJson)).all()
        if len(participantsJson) != len(participantsSql):
            return jsonify({"message": "Invalid participants."}), 400
        individual = request.json.get("individual")
        filtered = list(filter(lambda p: p.individual == individual, participantsSql))
        if len(filtered) != len(participantsSql):
            return jsonify({"message": "Invalid participants."}), 400

        election = Election(
            start=start,
            end=end,
            individual=individual

        )
        database.session.add(election)
        database.session.commit()
        sqlList = []
        counter = 1
        response = []
        for participant in filtered:
            sqlList.append(
                ElectionParticipant(participantId=participant.id, electionId=election.id, pollNumber=counter))
            response.append(counter)
            counter += 1
        database.session.bulk_save_objects(sqlList)
        database.session.commit()

        return jsonify({"pollNumbers": response}), 200
    else:
        return jsonify({"message": "Invalid date and time."}), 400


def dhont(nSeats, votes, census, verbose=False):

    total = sum(votes.values())
    keys_to_pop = []
    if total > 0:
        for key in votes:
            if (votes[key] / total) * 100 < census:
                keys_to_pop.append(key)
        for key in keys_to_pop:
            votes.pop(key)
    t_votes = votes.copy()
    seats = {}
    for key in votes: seats[key] = 0
    while sum(seats.values()) < nSeats:
        max_v = max(t_votes.values())
        next_seat = list(t_votes.keys())[list(t_votes.values()).index(max_v)]
        if next_seat in seats:
            seats[next_seat] += 1
        else:
            seats[next_seat] = 1

        if verbose:
            print("{} Result: {}".format(sum(seats.values()), next_seat))
            for key in t_votes:
                print("\t{} [{}]: {:.1f}".format(key, seats[key], t_votes[key]))
            print("\b")
        t_votes[next_seat] = votes[next_seat] / (seats[next_seat] + 1)
    return seats


def generateResults(election):
    individual = election.individual

    pollNumbersQuery = database.session.query(ElectionParticipant.pollNumber).order_by(
        ElectionParticipant.pollNumber).filter(ElectionParticipant.electionId == election.id).all()
    pollNumbers = [dict(r)["pollNumber"] for r in pollNumbersQuery]

    votesQuery = database.session.query(
        ElectionParticipant.pollNumber,
        func.count(Vote.id).label("count"),
    ).outerjoin(Vote, ElectionParticipant.pollNumber == Vote.pollNumber) \
        .group_by(ElectionParticipant.pollNumber) \
        .order_by(ElectionParticipant.pollNumber) \
        .filter(and_(ElectionParticipant.electionId == election.id,Vote.electionId == election.id ))

    votes = [dict(r) for r in votesQuery]

    total = sum(item['count'] for item in votes)

    if (individual):
        for index, number in enumerate(pollNumbers):
            forUpdate = ElectionParticipant.query.filter(and_(ElectionParticipant.pollNumber == pollNumbers[index],
                                                              ElectionParticipant.electionId == election.id)).first()
            forUpdate.result = round(votes[index]["count"] / (total if total != 0 else 1), 2)
            database.session.commit()
    else:
        votes_dict = {}


        for index, number in enumerate(pollNumbers):
            votes_dict[number] = votes[index]["count"]
        results = dhont(250, votes_dict, 5)
        for number in pollNumbers:
            forUpdate = ElectionParticipant.query.filter(
                and_(ElectionParticipant.pollNumber == number, ElectionParticipant.electionId == election.id)).first()
            if number in results:
                forUpdate.result = results[number]
            else:
                forUpdate.result = 0
            database.session.commit()


@electionsBlueprint.route("/getResults", methods=["GET"])
@required_role("administrator")
def getResults():

    id = request.args.get('id')
    if id is None:
        return jsonify({"message": "Field id is missing."}), 400

    election = Election.query.get(id)

    if election:
        if datetime.datetime.now() > election.end:
            participantsQuery = database.session.query(
                ElectionParticipant.pollNumber,
                Participant.name,
                ElectionParticipant.result,
            ).join(Participant, Participant.id == ElectionParticipant.participantId).filter(
                ElectionParticipant.electionId == id).order_by(ElectionParticipant.pollNumber)

            participants = [dict(r) for r in participantsQuery.all()]

            if any(p["result"] == None for p in participants):
                generateResults(election)
                participants = [dict(r) for r in participantsQuery.all()]

            if not election.individual:
                for participant in participants:
                    participant["result"] = int(participant["result"])

            votesQuery = database.session.query(
                Vote.electionOfficialJmbg,
                Vote.guid.label("ballotGuid"),
                Vote.pollNumber,
                Vote.status.label("reason"),
            ).filter(Vote.electionId == id, Vote.valid == False).all()
            votes = [dict(r) for r in votesQuery]

            return jsonify({
                "participants": participants,
                "invalidVotes": votes
            })

        else:
            return jsonify({"message": "Election is ongoing."}), 400

    return jsonify({"message": "Election does not exist."}), 400
