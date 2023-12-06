from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from models import Vote, Election, ElectionParticipant
from configuration import Configuration
import time
from redis import Redis
import json
import datetime

engine = create_engine(Configuration.SQLALCHEMY_DATABASE_URI, echo=False, future=True, pool_size=10, max_overflow=20)

Session = sessionmaker(bind=engine)
session = Session()


connected = False
while not connected:
    try:
        now = datetime.datetime.now()

        election = session.query(Election).filter(and_(Election.start <= now, Election.end > now)).first()
        with Redis(host=Configuration.REDIS_HOST) as redis:
            redis.ping()
        connected = True
    except Exception as e:
        print("Database or redis services not ready:")
        print(e)
        time.sleep(10)

while True:
    session = Session()
    now = datetime.datetime.now()

    election = session.query(Election).filter(and_(Election.start <= now, Election.end > now)).first()

    if not election:
        count = redis.llen(Configuration.REDIS_VOTE_LIST)
        print(f"{now}: There is no election going on currently.")
        if count:
            print(f"{now}: Removing {count} invalid votes from redis service.")
            redis.delete(Configuration.REDIS_VOTE_LIST)
        session.close()
        time.sleep(10)
        continue

    pollNumbersQuery = session.query(ElectionParticipant.pollNumber).distinct(ElectionParticipant.pollNumber).order_by(
        ElectionParticipant.pollNumber).filter(ElectionParticipant.electionId == election.id).all()
    pollNumbers = [dict(r)["pollNumber"] for r in pollNumbersQuery]

    votesQuery = session.query(
        Vote.electionOfficialJmbg,
        Vote.guid.label("ballotGuid"),
        Vote.pollNumber,
        Vote.status.label("reason"),
    ).filter(Vote.electionId == election.id, Vote.valid == False).all()
    votes = [dict(r) for r in votesQuery]

    with Redis(host=Configuration.REDIS_HOST) as redis:
        new_votes = redis.lrange(Configuration.REDIS_VOTE_LIST, 0, -1)

        if not new_votes:
            print(f"{now}: No new votes.")
            session.close()
            time.sleep(10)
            continue
        for voteString in new_votes:
            vote = json.loads(voteString.decode("utf-8"))
            exists = session.query(Vote).filter(Vote.guid == vote["GUID"]).first()

            if vote['pollNumber'] not in pollNumbers:
                newVote = Vote(
                    guid=vote['GUID'],
                    pollNumber=vote['pollNumber'],
                    electionOfficialJmbg=vote['electionOfficialJmbg'],
                    valid=False,
                    status="Invalid poll number.",
                    electionId=election.id,
                )
            elif exists:
                newVote = Vote(
                    guid=vote['GUID'],
                    pollNumber=vote['pollNumber'],
                    electionOfficialJmbg=vote['electionOfficialJmbg'],
                    valid=False,
                    status="Duplicate ballot.",
                    electionId=election.id,
                )
            else:
                newVote = Vote(
                    guid=vote['GUID'],
                    pollNumber=vote['pollNumber'],
                    electionOfficialJmbg=vote['electionOfficialJmbg'],
                    valid=True,
                    electionId=election.id,
                )

            session.add(newVote)
            session.commit()
            redis.lpop(Configuration.REDIS_VOTE_LIST)

    print(f"{now}: {len(new_votes)} new votes added from redis service.")
    session.close()
    time.sleep(10)
