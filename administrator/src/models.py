from dataclasses import dataclass, field

import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import column_property
from typing import List

database = SQLAlchemy()



class Vote(database.Model):

    __tablename__ = "votes";

    id = database.Column(database.Integer, primary_key=True)
    guid = database.Column(database.String(36))
    pollNumber = database.Column(database.Integer)
    valid = database.Column(database.Boolean(), nullable=False)
    status = database.Column(database.String(24), nullable=True)
    electionId = database.Column(database.Integer, database.ForeignKey("election.id"), nullable=False);
    electionOfficialJmbg = database.Column(database.String(13), nullable=False);

@dataclass
class ParticipantBase(database.Model):
    id: int
    name: str

    __tablename__ = "participant";

    id = database.Column(database.Integer, primary_key=True);
    name = database.Column(database.String(256), nullable=False);
    individual = database.Column(database.Boolean(), nullable=False);

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

@dataclass
class Participant(ParticipantBase):
    individual: bool



@dataclass
class ElectionParticipant(database.Model):
    pollNumber: int
    result: float

    __tablename__ = "electionparticipant";


    id = database.Column(database.Integer, primary_key=True);
    participantId = database.Column(database.Integer, database.ForeignKey("participant.id"), nullable=False);
    electionId = database.Column(database.Integer, database.ForeignKey("election.id"), nullable=False);
    pollNumber = database.Column(database.Integer);
    result = database.Column(database.Float);



@dataclass
class Election(database.Model):
    id: int
    individual: bool
    start: datetime.datetime
    end: datetime.datetime
    participants: List[ParticipantBase]



    __tablename__ = "election";

    id = database.Column(database.Integer, primary_key=True)
    individual = database.Column(database.Boolean(), nullable=False)
    start = database.Column(database.DateTime(),nullable=False)
    end = database.Column(database.DateTime(),nullable=False)
    participants = database.relationship("ParticipantBase", secondary=ElectionParticipant.__table__);


    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

