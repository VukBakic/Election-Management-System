from dataclasses import dataclass
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, declarative_base

import datetime


Base = declarative_base()


class Vote(Base):

    __tablename__ = "votes";

    id = Column(Integer, primary_key=True)
    guid = Column(String(36))
    pollNumber = Column(Integer)
    valid = Column(Boolean(), nullable=False)
    status = Column(String(24), nullable=True)
    electionId = Column(Integer, ForeignKey("election.id"), nullable=False);
    electionOfficialJmbg = Column(String(13), nullable=False);

@dataclass
class Participant(Base):
    id: int
    name: str
    individual: bool

    __tablename__ = "participant";

    id = Column(Integer, primary_key=True);
    name = Column(String(256), nullable=False);
    individual = Column(Boolean(), nullable=False);

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

@dataclass
class ElectionParticipant(Base):
    pollNumber: int
    result: float

    __tablename__ = "electionparticipant";


    id = Column(Integer, primary_key=True);
    participantId = Column(Integer, ForeignKey("participant.id"), nullable=False);
    electionId = Column(Integer, ForeignKey("election.id"), nullable=False);
    pollNumber = Column(Integer);
    result = Column(Float);


@dataclass
class Election(Base):
    id: int
    individual: bool
    start: datetime.datetime
    end: datetime.datetime
    participants: Participant

    __tablename__ = "election";

    id = Column(Integer, primary_key=True)
    individual = Column(Boolean(), nullable=False)
    start = Column(DateTime(),nullable=False)
    end = Column(DateTime(),nullable=False)
    participants = relationship("Participant", secondary=ElectionParticipant.__table__);

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}